#!/usr/bin/env python3
import random
import subprocess
import zipfile
import os
import shutil
import sys
import platform
import wave
import struct
import tempfile
from datetime import datetime
from pathlib import Path
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Label, Static
from textual.binding import Binding
from textual.worker import Worker, WorkerState
# Optional audio synthesis dependencies
try:
    import numpy as np
    import tinysoundfont
    from static_ffmpeg import run
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    np = None
    tinysoundfont = None
    run = None

from .soundfont_manager import SoundfontManager

# Default output directory - try Desktop, fallback to home
def get_default_output_dir():
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return desktop
    # Fallback to home directory if Desktop doesn't exist
    return Path.home()

DEFAULT_OUTPUT_DIR = get_default_output_dir()

# Note: Soundfont paths are now managed by SoundfontManager
# The old SOUNDFONT_PATH global variable has been removed in favor of dynamic selection


# Japanese-inspired scale intervals
SCALE_MAP = {
    "Hirajoshi": [0, 2, 3, 7, 8],
    "In Sen": [0, 1, 5, 7, 10],
    "Kumoi": [0, 2, 3, 7, 9],
    "Yo": [0, 2, 5, 7, 9]
}

ROOT_OPTIONS = list(range(45, 57))  # A2 to A#3

# Soundfont-specific instrument and mix profiles
SOUNDFONT_PROFILES = {
    'GeneralUser GS': {
        'instruments': {
            'pad': 89,          # Warm Pad
            'flute': 76,        # Pan Flute
            'vibraphone': 11,   # Vibraphone
            'strings': 48,      # String Ensemble 1
            'music_box': 10     # Music Box
        },
        'volumes_with_effects': {
            'pad': 5.5,         # Dominant foundation
            'flute': 14.6,      # Counter melody, blended with pads
            'vibraphone': 2.91, # Counter melody, matches music box
            'strings': 0.10,    # Subtle background drone
            'music_box': 0.25   # Twinkly background sparkle
        },
        'volumes_no_effects': {
            'pad': 3.5,
            'flute': 3.5,
            'vibraphone': 1.1,
            'strings': 0.25,
            'music_box': 0.4
        }
    },
    'SGM V2.01': {
        'instruments': {
            'pad': 91,          # Space Voice (more ambient than Warm Pad)
            'flute': 75,        # Pan Flute (was 76 Bottle Blow - incorrect)
            'vibraphone': 11,   # Vibraphone
            'strings': 49,      # Slow Strings (more ambient than regular Strings)
            'music_box': 10     # Music Box
        },
        'volumes_with_effects': {
            'pad': 1.67,
            'flute': 0.53,
            'vibraphone': 3.51,
            'strings': 0.10,
            'music_box': 20.0
        },
        'volumes_no_effects': {
            'pad': 4.15,
            'flute': 1.04,
            'vibraphone': 47.68,
            'strings': 0.16,
            'music_box': 47.59
        }
    },
    'FluidR3 GM': {
        'instruments': {
            'pad': 89,          # Warm Pad (standard GM)
            'flute': 76,        # Pan Flute
            'vibraphone': 11,   # Vibraphone
            'strings': 48,      # String Ensemble 1
            'music_box': 10     # Music Box
        },
        'volumes_with_effects': {
            'pad': 0.48,
            'flute': 1.20,
            'vibraphone': 1.52,
            'strings': 0.02,
            'music_box': 0.19
        },
        'volumes_no_effects': {
            'pad': 6.84,
            'flute': 0.06,
            'vibraphone': 0.84,
            'strings': 0.01,
            'music_box': 0.44
        }
    }
}


def build_scale(root, scale_name):
    intervals = SCALE_MAP.get(scale_name, SCALE_MAP["Hirajoshi"])
    return [root + i for i in intervals]


def pick_notes(scale, count, shifts):
    return [random.choice(scale) + random.choice(shifts) for _ in range(count)]


def apply_reverb(audio, sample_rate, room_size=0.5, damping=0.5, wet=0.3):
    """Apply massive ambient reverb - evolving wash that breathes."""
    # Dense delay network - multiple delay lines for rich reverb
    delay_times = [int(sample_rate * t) for t in [
        0.0297, 0.0371, 0.0411, 0.0437, 0.0527, 0.0631, 0.0719, 0.0823,
        0.0941, 0.1049, 0.1181, 0.1289
    ]]

    output = np.zeros_like(audio)

    # Build reverb with controlled feedback for evolution
    for delay_samples in delay_times:
        delayed = np.zeros_like(audio)
        delayed[delay_samples:] = audio[:-delay_samples]

        # Reduced feedback iterations - faster decay allows chord changes to be heard
        for iteration in range(4):
            feedback = np.zeros_like(delayed)
            decay = room_size * damping * (0.78 ** iteration)  # Faster progressive decay
            feedback[delay_samples:] = delayed[:-delay_samples] * decay
            delayed = delayed + feedback

        output += delayed

    # Moderate diffusion - 8 passes for smooth but evolving wash
    for pass_num in range(8):
        diffused = np.zeros_like(output)
        # Varying diffusion delays for smooth wash
        diffuse_delay = int(sample_rate * (0.015 + pass_num * 0.004))
        if diffuse_delay < len(output):
            diffused[diffuse_delay:] = output[:-diffuse_delay] * 0.7
            output = output * 0.55 + diffused * 0.45

    # Mix with very little dry signal
    output = output * wet * 0.45
    output = audio * (1.0 - wet) * 0.2 + output

    return output


def apply_delay(audio, sample_rate, delay_time_sec, feedback=0.4, wet=0.3):
    """Apply tempo-synced delay effect."""
    delay_samples = int(sample_rate * delay_time_sec)

    output = audio.copy()
    delayed = np.zeros_like(audio)

    # Create delayed signal with feedback
    for i in range(len(audio)):
        if i >= delay_samples:
            delayed[i] = audio[i - delay_samples] + delayed[i - delay_samples] * feedback
        output[i] = audio[i] + delayed[i] * wet

    return output


def apply_warm_overdrive(audio, drive=2.0, mix=0.5):
    """Apply warm tube-style overdrive for musical harmonic saturation."""
    # Asymmetric soft clipping (like tube amps) - more musical
    driven = audio * drive

    # Soft clipping with cubic waveshaping for smooth harmonics
    def soft_clip(x):
        # Smooth saturation curve
        return np.where(np.abs(x) < 1.0,
                       x - (x**3) / 3,
                       np.sign(x) * (2/3))

    saturated = soft_clip(driven)

    # Add subtle even harmonics (warm character)
    harmonics = soft_clip(driven * 1.5) * 0.2
    saturated = saturated + harmonics

    # Very gentle high-frequency rolloff for warmth
    # Simple one-pole lowpass approximation
    filtered = saturated.copy()
    alpha = 0.92  # Gentle rolloff
    for i in range(1, len(filtered)):
        filtered[i] = alpha * filtered[i] + (1 - alpha) * filtered[i-1]

    # Mix with dry signal
    output = audio * (1.0 - mix) + filtered * mix

    return output


def apply_chorus(audio, sample_rate, rate=0.5, depth=0.003, mix=0.3):
    """Apply chorus/flanger effect for movement and dimension."""
    output = audio.copy()

    # LFO (Low Frequency Oscillator) for modulation
    lfo_samples = np.arange(len(audio))
    lfo = np.sin(2 * np.pi * rate * lfo_samples / sample_rate)

    # Modulated delay time (in samples)
    max_delay = int(depth * sample_rate)
    delay_samples = (lfo * max_delay).astype(int) + max_delay

    # Apply modulated delay
    chorus_signal = np.zeros_like(audio)
    for i in range(len(audio)):
        delay = delay_samples[i]
        if i >= delay:
            chorus_signal[i] = audio[i - delay]

    # Mix with dry signal
    output = audio * (1.0 - mix) + chorus_signal * mix

    return output


def apply_stereo_widening(mono_audio, width=0.7):
    """Convert mono to stereo with width control."""
    # Create stereo by adding phase-shifted versions
    left = mono_audio.copy()

    # Simple all-pass filter for phase shift (approximation)
    right = mono_audio.copy()
    for i in range(1, len(right)):
        right[i] = 0.7 * right[i] + 0.3 * right[i-1]

    # Apply width
    mid = (left + right) / 2
    side = (left - right) / 2

    left = mid + side * width
    right = mid - side * width

    # Interleave for stereo
    stereo = np.zeros(len(mono_audio) * 2, dtype=np.float32)
    stereo[0::2] = left
    stereo[1::2] = right

    return stereo


def apply_compressor(audio, threshold=0.5, ratio=3.0, attack_samples=220, release_samples=4400):
    """Apply simple RMS compressor for glue and dynamics control."""
    output = audio.copy()
    envelope = 0.0

    for i in range(len(audio)):
        # RMS detection
        input_level = abs(audio[i])

        # Envelope follower
        if input_level > envelope:
            envelope += (input_level - envelope) / attack_samples
        else:
            envelope += (input_level - envelope) / release_samples

        # Compute gain reduction
        if envelope > threshold:
            # Calculate how much over threshold
            over = envelope - threshold
            # Apply ratio
            gain_reduction = 1.0 - (over * (1.0 - 1.0/ratio))
            output[i] = audio[i] * gain_reduction

    # Makeup gain
    output = output * 1.5

    return output


def apply_limiter(audio, threshold=0.95, release_samples=2200):
    """Apply brick-wall limiter to prevent clipping."""
    output = audio.copy()
    envelope = 0.0

    for i in range(len(audio)):
        input_level = abs(audio[i])

        # Fast attack, slower release
        if input_level > envelope:
            envelope = input_level  # Instant attack
        else:
            envelope += (input_level - envelope) / release_samples

        # Hard limiting
        if envelope > threshold:
            gain = threshold / envelope
            output[i] = audio[i] * gain

    return output


def apply_paulstretch(samplerate, smp, stretch=8.0, windowsize_seconds=0.25):
    """
    Apply Paul Stretch algorithm - extreme time stretching for ambient textures.

    Based on the public domain implementation by Paul Nasca (Nasca Octavian Paul).
    Uses FFT with phase randomization to create ethereal stretched audio.

    Args:
        samplerate: Sample rate in Hz (e.g., 44100)
        smp: Audio samples as numpy array
        stretch: Stretch factor (e.g., 8.0 means 8x longer)
        windowsize_seconds: Window size in seconds (e.g., 0.25)

    Returns:
        Stretched audio as numpy array
    """
    # Calculate window size in samples (must be even, >= 16)
    windowsize = int(windowsize_seconds * samplerate)
    windowsize = max(16, windowsize)
    windowsize = int(windowsize / 2) * 2  # Make even
    half_windowsize = windowsize // 2

    # Create window function (raised cosine with power modification)
    window = 0.5 - np.cos(np.arange(windowsize, dtype='float') * 2.0 * np.pi / (windowsize - 1)) * 0.5

    # Calculate displacement (how far to advance in input per iteration)
    displace_pos = (windowsize * 0.5) / stretch

    # Initialize buffers
    old_windowed_buf = np.zeros(windowsize)

    # Amplitude correction for overlap-add
    hinv_sqrt2 = (1 + np.sqrt(0.5)) * 0.5
    hinv_buf = hinv_sqrt2 - (1.0 - hinv_sqrt2) * np.cos(np.arange(half_windowsize, dtype='float') * 2.0 * np.pi / half_windowsize)

    start_pos = 0.0
    output_chunks = []

    while start_pos < len(smp):
        # Extract windowed buffer from input
        istart_pos = int(np.floor(start_pos))
        buf = smp[istart_pos:istart_pos + windowsize].copy()

        # Zero-pad if at end of file
        if len(buf) < windowsize:
            buf = np.append(buf, np.zeros(windowsize - len(buf)))

        # Apply window
        buf = buf * window

        # FFT -> get magnitude spectrum
        freqs_mag = np.abs(np.fft.rfft(buf))

        # Randomize phase (key step!)
        ph = np.random.uniform(0, 2 * np.pi, len(freqs_mag)) * 1j
        freqs = freqs_mag * np.exp(ph)

        # Inverse FFT
        buf = np.fft.irfft(freqs)

        # Apply window again
        buf = buf * window

        # Overlap-add: combine first half of current with second half of previous
        output = buf[0:half_windowsize] + old_windowed_buf[half_windowsize:windowsize]
        old_windowed_buf = buf

        # Apply amplitude correction
        output = output * hinv_buf

        # Clamp to [-1, 1]
        output = np.clip(output, -1.0, 1.0)

        output_chunks.append(output)

        # Advance position
        start_pos += displace_pos

    return np.concatenate(output_chunks)


def render_channel_to_audio(midi_path, soundfont_path, channel, total_samples, sample_rate=44100):
    """Render a single MIDI channel to audio array."""
    synth = tinysoundfont.Synth()
    sfid = synth.sfload(soundfont_path)

    # Parse MIDI file
    mid = MidiFile(midi_path)

    # Get tempo
    tempo = 500000  # Default
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break

    ticks_per_beat = mid.ticks_per_beat
    tempo_sec = tempo / 1000000.0
    tempo_seconds_per_tick = tempo_sec / ticks_per_beat

    # Collect events for this channel only
    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if hasattr(msg, 'channel') and msg.channel == channel:
                if msg.type in ['note_on', 'note_off', 'program_change']:
                    events.append((abs_time, msg))

    # Sort events by time
    events.sort(key=lambda x: x[0])

    # Render audio
    output_chunks = []
    event_idx = 0
    samples_generated = 0

    while samples_generated < total_samples:
        next_chunk_samples = min(4096, total_samples - samples_generated)
        current_time_ticks = (samples_generated / sample_rate) / tempo_seconds_per_tick
        next_time_ticks = ((samples_generated + next_chunk_samples) / sample_rate) / tempo_seconds_per_tick

        # Process events in this time range
        while event_idx < len(events) and events[event_idx][0] < next_time_ticks:
            _, msg = events[event_idx]
            if msg.type == 'program_change':
                synth.program_change(msg.channel, msg.program)
            elif msg.type == 'note_on' and msg.velocity > 0:
                synth.noteon(msg.channel, msg.note, msg.velocity)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                synth.noteoff(msg.channel, msg.note)
            event_idx += 1

        # Generate audio chunk
        chunk = synth.generate(next_chunk_samples)
        chunk_array = np.frombuffer(chunk, dtype=np.float32)
        output_chunks.append(chunk_array)
        samples_generated += next_chunk_samples

    # Concatenate and convert stereo to mono
    output_stereo = np.concatenate(output_chunks)
    output_mono = output_stereo.reshape(-1, 2).mean(axis=1)

    return output_mono


def render_midi_to_wav(midi_path, wav_path, soundfont_path, tempo_bpm=120, enable_effects=True, profile=None):
    """Render MIDI file to WAV with optional per-track effects.

    Master chain (compression, limiting, stereo widening) always applied.
    """
    # Use GeneralUser profile as default if not provided
    if profile is None:
        profile = SOUNDFONT_PROFILES['GeneralUser GS']

    # Select volume set based on effects
    volumes = profile['volumes_with_effects'] if enable_effects else profile['volumes_no_effects']
    # Parse MIDI to get total length
    mid = MidiFile(midi_path)

    total_ticks = 0
    tempo = 500000
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
        track_ticks = sum(m.time for m in track if hasattr(m, 'time'))
        total_ticks = max(total_ticks, track_ticks)

    ticks_per_beat = mid.ticks_per_beat
    tempo_sec = tempo / 1000000.0
    total_seconds = (total_ticks / ticks_per_beat) * tempo_sec

    sample_rate = 44100
    total_samples = int(total_seconds * sample_rate) + sample_rate

    # Calculate delay times based on tempo
    beat_duration = 60.0 / tempo_bpm
    eighth_note_delay = beat_duration / 2  # Eighth note for bells
    half_note_delay = beat_duration * 2    # Half note for music box

    # Render each channel separately
    # Channel 0: Pad (massive reverb)
    # Channel 1: Flute (massive reverb)
    # Channel 2: Vibraphone (half-note delay)
    # Channel 3: Strings/Drone (saturation)
    # Channel 4: Music Box (eighth-note delay)

    channel_audio = {}
    for ch in range(5):
        audio = render_channel_to_audio(midi_path, soundfont_path, ch, total_samples, sample_rate)

        # Apply effects and volume based on enable_effects flag
        if enable_effects:
            # WITH EFFECTS - apply effects then profile volume
            if ch == 0:  # Pad - Massive evolving reverb wash
                audio = apply_reverb(audio, sample_rate, room_size=0.85, damping=0.78, wet=0.92)
                audio = audio * volumes['pad']
            elif ch == 1:  # Flute - same massive reverb as pad
                audio = apply_reverb(audio, sample_rate, room_size=0.85, damping=0.78, wet=0.92)
                audio = audio * volumes['flute']
            elif ch == 2:  # Vibraphone - reverb then half-note delay
                audio = apply_reverb(audio, sample_rate, room_size=0.65, damping=0.6, wet=0.65)
                audio = apply_delay(audio, sample_rate, half_note_delay, feedback=0.65, wet=0.5)
                audio = audio * volumes['vibraphone']
            elif ch == 3:  # Drone - tape saturation with subtle chorus
                audio = apply_warm_overdrive(audio, drive=9.0, mix=0.95)  # Extreme tape saturation
                audio = apply_chorus(audio, sample_rate, rate=0.5, depth=0.002, mix=0.25)  # Subtle movement
                audio = audio * volumes['strings']
            elif ch == 4:  # Music Box - delay then slow flanger
                audio = apply_delay(audio, sample_rate, eighth_note_delay, feedback=0.75, wet=0.6)
                audio = apply_chorus(audio, sample_rate, rate=0.3, depth=0.004, mix=0.3)  # Slow flanger
                audio = audio * volumes['music_box']
        else:
            # NO EFFECTS - profile volumes adjusted for no effects
            if ch == 0:  # Pad
                audio = audio * volumes['pad']
            elif ch == 1:  # Flute
                audio = audio * volumes['flute']
            elif ch == 2:  # Vibraphone
                audio = audio * volumes['vibraphone']
            elif ch == 3:  # Drone
                audio = audio * volumes['strings']
            elif ch == 4:  # Music Box
                audio = audio * volumes['music_box']

        channel_audio[ch] = audio

    # Mix all channels
    output_mono = np.zeros(total_samples, dtype=np.float32)
    for audio in channel_audio.values():
        output_mono += audio

    # Mastering chain
    # 1. Gentle compression for glue
    output_mono = apply_compressor(output_mono, threshold=0.4, ratio=2.5)

    # 2. Brick-wall limiter to prevent clipping and add loudness
    output_mono = apply_limiter(output_mono, threshold=0.95)

    # 3. Final normalization
    max_val = np.max(np.abs(output_mono))
    if max_val > 0:
        output_mono = output_mono / max_val * 0.95

    # 4. Stereo widening for immersive soundstage
    output_stereo = apply_stereo_widening(output_mono, width=0.7)

    # Write stereo WAV file
    with wave.open(str(wav_path), 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Convert float32 stereo to int16
        audio_int16 = (output_stereo * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())


def convert_wav_to_mp3(wav_path, mp3_path):
    """Convert WAV to MP3 using static-ffmpeg."""
    # Ensure ffmpeg is available
    ffmpeg_path, _ = run.get_or_fetch_platform_executables_else_raise()

    # Run ffmpeg conversion
    subprocess.run([
        ffmpeg_path,
        '-y',  # Overwrite output file
        '-i', str(wav_path),
        '-codec:a', 'libmp3lame',
        '-qscale:a', '2',  # High quality
        str(mp3_path)
    ], check=True, capture_output=True)


class SoundfontSelector(Static):
    def __init__(self, soundfont_manager, **kwargs):
        super().__init__(**kwargs)
        self.sf_manager = soundfont_manager
        self._is_disabled = False

    def render(self) -> str:
        if self.sf_manager.count() <= 1:
            # Only one soundfont, show name without cycling UI
            text = f"🎹 {self.sf_manager.get_current_name()}"
        else:
            # Multiple soundfonts, show current with indicator
            text = f"🎹 [bold cyan]{self.sf_manager.get_current_name()}[/] ({self.sf_manager.current_index + 1}/{self.sf_manager.count()})"

        # Dim if disabled
        if self._is_disabled:
            return f"[dim]{text}[/dim]"
        return text

    def next_soundfont(self):
        if not self._is_disabled:
            self.sf_manager.next_soundfont()
            self.refresh()

    def prev_soundfont(self):
        if not self._is_disabled:
            self.sf_manager.previous_soundfont()
            self.refresh()

    def set_disabled(self, disabled: bool):
        self._is_disabled = disabled
        self.refresh()


class ScaleSelector(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scales = list(SCALE_MAP.keys())
        self.current_index = 0

    def render(self) -> str:
        options = []
        for i, scale in enumerate(self.scales):
            if i == self.current_index:
                options.append(f"[bold cyan]▶ {scale}[/]")
            else:
                options.append(f"  {scale}")
        return "\n".join(options)

    def next_scale(self):
        self.current_index = (self.current_index + 1) % len(self.scales)
        self.refresh()

    def prev_scale(self):
        self.current_index = (self.current_index - 1) % len(self.scales)
        self.refresh()

    def get_scale(self):
        return self.scales[self.current_index]


class TempoControl(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 48
        self.min_val = 30
        self.max_val = 60

    def render(self) -> str:
        bar_width = 30
        filled = int((self.value - self.min_val) / (self.max_val - self.min_val) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"Tempo (BPM): [bold]{self.value:3d}[/] [{bar}]"

    def increase(self):
        if self.value < self.max_val:
            self.value += 1
            self.refresh()

    def decrease(self):
        if self.value > self.min_val:
            self.value -= 1
            self.refresh()


class BarsControl(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 12
        self.min_val = 4
        self.max_val = 16

    def render(self) -> str:
        bar_width = 30
        filled = int((self.value - self.min_val) / (self.max_val - self.min_val) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"Length (bars): [bold]{self.value:3d}[/] [{bar}]"

    def increase(self):
        if self.value < self.max_val:
            self.value += 1
            self.refresh()

    def decrease(self):
        if self.value > self.min_val:
            self.value -= 1
            self.refresh()


class LayerCheckbox(Static):
    def __init__(self, label: str, checked: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.checked = checked
        self._is_disabled = False

    def render(self) -> str:
        checkbox = "\\[X]" if self.checked else "\\[ ]"
        if self._is_disabled:
            return f"[dim]{checkbox} {self.label}[/dim]"
        return f"{checkbox} {self.label}"

    def toggle(self):
        if not self._is_disabled:
            self.checked = not self.checked
            self.refresh()

    def set_disabled(self, disabled: bool):
        self._is_disabled = disabled
        self.refresh()


class AmbientGeneratorApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        width: 100%;
        text-align: center;
        background: $primary;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }

    .section {
        border: solid $primary;
        margin: 0 2;
        padding: 0 1;
        height: auto;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        padding: 0;
    }

    ScaleSelector {
        height: 4;
        padding: 0 1;
    }

    TempoControl, BarsControl {
        padding: 0;
        height: 1;
    }

    LayerCheckbox {
        height: 1;
        padding: 0 1;
    }

    SoundfontSelector {
        height: 1;
        padding: 0 1;
    }

    #generate-button {
        width: 100%;
        margin: 0 2;
    }

    #status {
        width: 100%;
        text-align: center;
        padding: 0;
        color: $success;
        height: 1;
    }

    #output-dir {
        width: 100%;
        text-align: center;
        padding: 0;
        color: $text-muted;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("g", "generate", "Generate", priority=True),
        Binding("o", "open_output", "Open Output", show=False),
        Binding("up,k", "tempo_up", "Tempo +", show=False),
        Binding("down,j", "tempo_down", "Tempo -", show=False),
        Binding("left,h", "bars_down", "Bars -", show=False),
        Binding("right,l", "bars_up", "Bars +", show=False),
        Binding("s", "next_scale", "Next Scale", show=False),
        Binding("S", "prev_scale", "Prev Scale", show=False),
        Binding("1", "toggle_pad", "Toggle Pad", show=False),
        Binding("2", "toggle_melody", "Toggle Flute", show=False),
        Binding("3", "toggle_counter", "Toggle Vibraphone", show=False),
        Binding("4", "toggle_drone", "Toggle Strings", show=False),
        Binding("5", "toggle_bells", "Toggle Music Box", show=False),
        Binding("a", "toggle_audio", "Toggle Audio", show=False),
        Binding("e", "toggle_effects", "Toggle Effects", show=False),
        Binding("p", "toggle_paulstretch", "Toggle Paul Stretch", show=False),
        Binding("f", "next_soundfont", "Next Soundfont", show=False),
        Binding("F", "prev_soundfont", "Prev Soundfont", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_dir = DEFAULT_OUTPUT_DIR
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Initialize soundfont manager
        self.soundfont_manager = SoundfontManager()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("🎼 Ambient Hirajoshi Generator", id="title")

        with Container(classes="section"):
            yield Label("Scale (s):", classes="section-title")
            yield ScaleSelector(id="scale-select")

        with Container(classes="section"):
            yield Label("Parameters (↑↓←→):", classes="section-title")
            yield TempoControl(id="tempo-control")
            yield BarsControl(id="bars-control")

        with Container(classes="section"):
            yield Label("Instruments (1-5):", classes="section-title")
            yield LayerCheckbox("1. Pad", True, id="check-pad")
            yield LayerCheckbox("2. Flute", True, id="check-melody")
            yield LayerCheckbox("3. Vibraphone", True, id="check-counter")
            yield LayerCheckbox("4. Strings", True, id="check-drone")
            yield LayerCheckbox("5. Music Box", True, id="check-bells")

        with Container(classes="section"):
            yield Label("Audio Options (a/e/p/f):", classes="section-title")
            yield LayerCheckbox("Render Audio", True, id="check-audio")
            yield LayerCheckbox("Enable Effects", True, id="check-effects")
            yield LayerCheckbox("Paul Stretch (8x)", False, id="check-paulstretch")
            yield SoundfontSelector(self.soundfont_manager, id="soundfont-selector")

        yield Button("🎶 Generate (g)", variant="success", id="generate-button")
        yield Static("Ready", id="status")
        yield Static(f"📁 Output: {self.output_dir}", id="output-dir")

        yield Footer()

    def action_next_scale(self) -> None:
        selector = self.query_one("#scale-select", ScaleSelector)
        selector.next_scale()
        self.query_one("#status", Static).update(f"Selected scale: {selector.get_scale()}")

    def action_prev_scale(self) -> None:
        selector = self.query_one("#scale-select", ScaleSelector)
        selector.prev_scale()
        self.query_one("#status", Static).update(f"Selected scale: {selector.get_scale()}")

    def action_tempo_up(self) -> None:
        self.query_one("#tempo-control", TempoControl).increase()

    def on_mount(self) -> None:
        """Called when app is mounted - set initial checkbox states"""
        self._update_audio_dependent_checkboxes()

    def action_tempo_down(self) -> None:
        self.query_one("#tempo-control", TempoControl).decrease()

    def action_bars_up(self) -> None:
        self.query_one("#bars-control", BarsControl).increase()

    def action_bars_down(self) -> None:
        self.query_one("#bars-control", BarsControl).decrease()

    def action_toggle_drone(self) -> None:
        self.query_one("#check-drone", LayerCheckbox).toggle()

    def action_toggle_pad(self) -> None:
        self.query_one("#check-pad", LayerCheckbox).toggle()

    def action_toggle_melody(self) -> None:
        self.query_one("#check-melody", LayerCheckbox).toggle()

    def action_toggle_counter(self) -> None:
        self.query_one("#check-counter", LayerCheckbox).toggle()

    def action_toggle_bells(self) -> None:
        self.query_one("#check-bells", LayerCheckbox).toggle()

    def action_toggle_audio(self) -> None:
        audio_checkbox = self.query_one("#check-audio", LayerCheckbox)
        audio_checkbox.toggle()

        # Update dependent checkboxes
        self._update_audio_dependent_checkboxes()

    def action_toggle_effects(self) -> None:
        self.query_one("#check-effects", LayerCheckbox).toggle()

    def _update_audio_dependent_checkboxes(self) -> None:
        """Enable/disable effects, paul stretch, and soundfont selector based on audio rendering state"""
        audio_enabled = self.query_one("#check-audio", LayerCheckbox).checked
        effects_checkbox = self.query_one("#check-effects", LayerCheckbox)
        paulstretch_checkbox = self.query_one("#check-paulstretch", LayerCheckbox)
        soundfont_selector = self.query_one("#soundfont-selector", SoundfontSelector)

        # Disable effects, paul stretch, and soundfont selector if audio is disabled
        effects_checkbox.set_disabled(not audio_enabled)
        paulstretch_checkbox.set_disabled(not audio_enabled)
        soundfont_selector.set_disabled(not audio_enabled)

    def action_toggle_paulstretch(self) -> None:
        self.query_one("#check-paulstretch", LayerCheckbox).toggle()

    def action_next_soundfont(self) -> None:
        selector = self.query_one("#soundfont-selector", SoundfontSelector)
        selector.next_soundfont()

    def action_prev_soundfont(self) -> None:
        selector = self.query_one("#soundfont-selector", SoundfontSelector)
        selector.prev_soundfont()

    def action_open_output(self) -> None:
        """Open output directory in file manager"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_dir)])
            elif system == "Windows":
                os.startfile(str(self.output_dir))
            elif system == "Linux":
                subprocess.run(["xdg-open", str(self.output_dir)])
            else:
                self.notify(f"⚠️ Cannot open folder on {system}")
                return
            self.notify(f"📂 Opened {self.output_dir}")
        except Exception as e:
            self.notify(f"⚠️ Could not open folder: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "generate-button":
            self.action_generate()

    def _update_status(self, message: str) -> None:
        """Helper to update status widget"""
        status = self.query_one("#status", Static)
        status.update(message)

    def action_generate(self) -> None:
        """Start generation in a background worker for responsive UI"""
        status = self.query_one("#status", Static)
        status.update("🎵 Generating...")

        tempo = self.query_one("#tempo-control", TempoControl).value
        bars = self.query_one("#bars-control", BarsControl).value
        scale_choice = self.query_one("#scale-select", ScaleSelector).get_scale()
        include_drone = self.query_one("#check-drone", LayerCheckbox).checked
        include_pad = self.query_one("#check-pad", LayerCheckbox).checked
        include_melody = self.query_one("#check-melody", LayerCheckbox).checked
        include_counter = self.query_one("#check-counter", LayerCheckbox).checked
        include_bells = self.query_one("#check-bells", LayerCheckbox).checked
        render_audio = self.query_one("#check-audio", LayerCheckbox).checked
        enable_effects = self.query_one("#check-effects", LayerCheckbox).checked
        enable_paulstretch = self.query_one("#check-paulstretch", LayerCheckbox).checked

        # Run generation in background worker so UI stays responsive
        # Use lambda to defer execution until worker thread starts
        self.run_worker(
            lambda: self.generate_track(tempo, bars, scale_choice, include_drone, include_pad,
                              include_melody, include_counter, include_bells,
                              render_audio, enable_effects, enable_paulstretch),
            thread=True,
            exclusive=True,
            exit_on_error=False
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion"""
        status = self.query_one("#status", Static)

        if event.state == WorkerState.SUCCESS:
            files = event.worker.result
            if files:
                base_name = Path(files['midi']).stem
                if 'mp3' in files:
                    if 'mp3_stretched' in files:
                        status.update(f"✅ {base_name} + stretched")
                        self.notify(f"✅ Generated normal + Paul Stretched (8x) versions! Press 'o' to open folder")
                    else:
                        status.update(f"✅ {base_name}")
                        self.notify(f"✅ Generated MIDI and MP3! Press 'o' to open folder")
                else:
                    status.update(f"✅ {base_name}.mid")
                    self.notify(f"✅ Generated MIDI only! Press 'o' to open folder")

        elif event.state == WorkerState.ERROR:
            error = str(event.worker.error)
            status.update(f"❌ Error: {error}")
            self.notify(f"Error: {error}")

    def generate_track(self, tempo, bars, scale_choice, include_drone, include_pad,
                      include_melody, include_counter, include_bells, render_audio=True,
                      enable_effects=True, enable_paulstretch=False):
        # Check if audio dependencies are available
        if render_audio and not AUDIO_AVAILABLE:
            raise ImportError(
                "Audio synthesis dependencies not installed. "
                "Install with: pip install ambient-gen[audio]\n\n"
                "Or install PortAudio first:\n"
                "  macOS: brew install portaudio\n"
                "  Linux: sudo apt-get install portaudio19-dev\n"
                "Then: pip install ambient-gen[audio]"
            )

        # Update status from worker thread
        self.call_from_thread(self._update_status, "🎵 Creating MIDI...")

        # Get soundfont profile for instrument mapping
        profile_name = self.soundfont_manager.get_profile_name()
        profile = SOUNDFONT_PROFILES.get(profile_name, SOUNDFONT_PROFILES['GeneralUser GS'])

        root = random.choice(ROOT_OPTIONS)
        scale = build_scale(root, scale_choice)
        chords = [sorted(random.sample(scale, 3)) for _ in range(bars)]
        melody_notes = pick_notes(scale, 16, [12, 24])  # Lowered by one octave
        counter_notes = pick_notes(scale, 12, [12, 24])
        fx_notes = pick_notes(scale, 60, [36, 48, 60])
        drone_note = root  # Move up an octave (was root - 12)
        bar_ticks = 1920  # 4 beats * 480 ticks per beat
        full_ticks = bar_ticks * bars  # Exactly the number of bars requested

        mid = MidiFile(ticks_per_beat=480)
        tempo_track = MidiTrack()
        tempo_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo)))
        tempo_track.append(MetaMessage('time_signature', numerator=4, denominator=4))
        mid.tracks.append(tempo_track)

        def make_track(channel, program, pan, reverb, chorus, name):
            t = MidiTrack()
            t.append(MetaMessage('track_name', name=name, time=0))
            t.append(Message('program_change', program=program, channel=channel, time=0))
            t.append(Message('control_change', control=91, value=reverb, channel=channel, time=0))
            t.append(Message('control_change', control=93, value=chorus, channel=channel, time=0))
            t.append(Message('control_change', control=10, value=pan, channel=channel, time=0))
            return t

        # Only create tracks that are enabled
        tracks_to_pad = []

        if include_pad:
            pad = make_track(0, profile['instruments']['pad'], 64, 127, 0, "Pad")
            mid.tracks.append(pad)

        if include_melody:
            melody = make_track(1, profile['instruments']['flute'], 32, 80, 90, "Flute")
            mid.tracks.append(melody)

        if include_counter:
            counter = make_track(2, profile['instruments']['vibraphone'], 96, 70, 100, "Vibraphone")
            mid.tracks.append(counter)

        if include_drone:
            drone = make_track(3, profile['instruments']['strings'], 64, 127, 0, "Strings")
            mid.tracks.append(drone)

        if include_bells:
            fx = make_track(4, profile['instruments']['music_box'], 64, 100, 60, "Music Box")
            mid.tracks.append(fx)

        # Add notes to enabled tracks
        if include_pad:
            for i in range(bars):
                chord = chords[i]

                # First chord starts immediately, subsequent chords have no additional delay
                delay = 0

                # Play original octave (louder)
                for note in chord:
                    pad.append(Message('note_on', note=note, velocity=60, time=delay, channel=0))
                    delay = 0

                # Play lower octave (quieter for subtle thickness)
                for note in chord:
                    pad.append(Message('note_on', note=note - 12, velocity=35, time=0, channel=0))

                # note_offs: first one at bar_ticks, rest at 0
                all_notes = chord + [note - 12 for note in chord]
                for idx, note in enumerate(all_notes):
                    pad.append(Message('note_off', note=note, velocity=60, time=bar_ticks if idx == 0 else 0, channel=0))
            tracks_to_pad.append((pad, 0))

        if include_drone:
            drone.append(Message('note_on', note=drone_note, velocity=35, time=0, channel=3))
            drone.append(Message('note_off', note=drone_note, velocity=35, time=full_ticks, channel=3))

        if include_melody:
            absolute_time = 0
            time_acc = 0
            for note in melody_notes:
                # Check if this note would exceed the length
                if absolute_time + time_acc + 480 > full_ticks:
                    break

                vel = random.randint(45, 70)
                melody.append(Message('note_on', note=note, velocity=vel, time=time_acc, channel=1))
                melody.append(Message('note_off', note=note, velocity=vel, time=480, channel=1))
                absolute_time += time_acc + 480
                time_acc = random.choice([960, 1440, 1920, 2400])
            tracks_to_pad.append((melody, 1))

        if include_counter:
            absolute_time = 0
            time_acc = 0
            for note in counter_notes:
                # Check if this note would exceed the length
                if absolute_time + time_acc + 600 > full_ticks:
                    break

                vel = random.randint(40, 60)
                counter.append(Message('note_on', note=note, velocity=vel, time=time_acc, channel=2))
                counter.append(Message('note_off', note=note, velocity=vel, time=600, channel=2))
                absolute_time += time_acc + 600
                time_acc = random.choice([1920, 2880, 3840])
            tracks_to_pad.append((counter, 2))

        if include_bells:
            absolute_time = 0
            fx_time = 0
            for note in fx_notes:
                # Check if this note would exceed the length
                if absolute_time + fx_time + 240 > full_ticks:
                    break

                vel = random.randint(35, 65)
                pan = random.randint(0, 127)
                fx.append(Message('control_change', control=10, value=pan, channel=4, time=0))
                fx.append(Message('note_on', note=note, velocity=vel, time=fx_time, channel=4))
                fx.append(Message('note_off', note=note, velocity=vel, time=240, channel=4))
                absolute_time += fx_time + 240
                fx_time = random.choice([240, 480, 720, 960])
            tracks_to_pad.append((fx, 4))

        # Pad all tracks to exactly full_ticks length
        for track, channel in tracks_to_pad:
            # Sum up all delta times to get the current length
            track_time = sum(msg.time for msg in track if hasattr(msg, 'time'))
            if track_time < full_ticks:
                # Pad with silence to reach full_ticks
                remaining = full_ticks - track_time
                track.append(Message('note_off', note=0, velocity=0, time=remaining, channel=channel))
            track.append(MetaMessage('end_of_track', time=0))

        # Add end_of_track to drone separately (it's already the right length)
        if include_drone:
            drone.append(MetaMessage('end_of_track', time=0))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"ambient_{timestamp}"
        full_midi = self.output_dir / f"{base}.mid"
        full_mp3 = self.output_dir / f"{base}.mp3"

        # Save MIDI
        mid.save(str(full_midi))

        # Conditionally render audio
        if render_audio:
            effects_label = "with effects" if enable_effects else "no effects"
            self.call_from_thread(self._update_status, f"🎵 Rendering audio ({effects_label})...")

            # Create temporary WAV file
            temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav', prefix='ambient_')
            os.close(temp_wav_fd)  # Close file descriptor, we'll use the path

            # Get selected soundfont path
            soundfont_path = str(self.soundfont_manager.get_current_path())

            render_midi_to_wav(str(full_midi), temp_wav_path, soundfont_path,
                             tempo_bpm=tempo, enable_effects=enable_effects, profile=profile)

            self.call_from_thread(self._update_status, "🎵 Converting to MP3...")

            convert_wav_to_mp3(temp_wav_path, str(full_mp3))

            # Apply Paul Stretch if enabled
            if enable_paulstretch:
                self.call_from_thread(self._update_status, "🎵 Applying Paul Stretch (8x)...")

                # Load the rendered WAV file
                import wave
                with wave.open(temp_wav_path, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    n_channels = wav_file.getnchannels()
                    audio_data = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)

                # Convert int16 to float32
                audio_float = audio_data.astype(np.float32) / 32767.0

                # Handle stereo - convert to mono for Paul Stretch, then back to stereo
                if n_channels == 2:
                    audio_float = audio_float.reshape(-1, 2).mean(axis=1)

                # Apply Paul Stretch
                stretched = apply_paulstretch(sample_rate, audio_float, stretch=8.0, windowsize_seconds=0.25)

                # Convert back to stereo if original was stereo
                if n_channels == 2:
                    stretched_stereo = apply_stereo_widening(stretched, width=0.7)
                    # Convert back to int16
                    stretched_int16 = (stretched_stereo * 32767).astype(np.int16)
                else:
                    stretched_int16 = (stretched * 32767).astype(np.int16)

                # Create temporary stretched WAV file
                temp_stretched_fd, temp_stretched_path = tempfile.mkstemp(suffix='_stretched.wav', prefix='ambient_')
                os.close(temp_stretched_fd)

                # Save stretched WAV to temp file
                with wave.open(temp_stretched_path, 'w') as wav_file:
                    wav_file.setnchannels(n_channels)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(stretched_int16.tobytes())

                # Add status update before MP3 conversion
                self.call_from_thread(self._update_status, "🎵 Converting stretched audio to MP3...")

                # Convert stretched WAV to MP3
                stretched_mp3 = self.output_dir / f"{base}_stretched.mp3"
                convert_wav_to_mp3(temp_stretched_path, str(stretched_mp3))

                # Clean up temporary WAV files
                try:
                    os.unlink(temp_wav_path)
                    os.unlink(temp_stretched_path)
                except Exception:
                    pass  # Ignore cleanup errors

                return {
                    'midi': str(full_midi),
                    'mp3': str(full_mp3),
                    'mp3_stretched': str(stretched_mp3)
                }
            else:
                # Clean up temporary WAV file
                try:
                    os.unlink(temp_wav_path)
                except Exception:
                    pass  # Ignore cleanup errors

                return {
                    'midi': str(full_midi),
                    'mp3': str(full_mp3)
                }
        else:
            # MIDI only
            return {
                'midi': str(full_midi)
            }


def main():
    app = AmbientGeneratorApp()
    app.run()
    return 0


if __name__ == "__main__":
    exit(main())

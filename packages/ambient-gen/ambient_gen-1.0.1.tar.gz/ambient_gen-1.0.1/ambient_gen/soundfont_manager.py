"""Soundfont manager for the ambient generator."""

from pathlib import Path
from typing import List, Dict


class SoundfontManager:
    """Manages available soundfonts and selection."""

    def __init__(self):
        self.package_dir = Path(__file__).parent
        self.soundfonts_dir = self.package_dir / "soundfonts"
        self.fallback_sf2 = self.package_dir / "GeneralUser.sf2"

        self.available_fonts = self._discover_soundfonts()
        self.current_index = 0

        # If no soundfonts found in soundfonts/, use fallback
        if not self.available_fonts and self.fallback_sf2.exists():
            self.available_fonts = [{
                'name': 'GeneralUser GS',
                'path': self.fallback_sf2,
                'description': 'High-quality General MIDI soundfont'
            }]

    def _discover_soundfonts(self) -> List[Dict]:
        """Discover all available soundfont files."""
        fonts = []

        if not self.soundfonts_dir.exists():
            return fonts

        # Look for both SF2 and SF3 files
        for pattern in ['*.sf2', '*.sf3', '*.SF2', '*.SF3']:
            for sf_path in self.soundfonts_dir.glob(pattern):
                fonts.append(self._create_font_entry(sf_path))

        # Sort by name
        fonts.sort(key=lambda x: x['name'])
        return fonts

    def _create_font_entry(self, path: Path) -> Dict:
        """Create a soundfont entry dictionary."""
        # Extract name from filename
        name = path.stem

        # Pretty names for known soundfonts
        name_mapping = {
            'GeneralUser': 'GeneralUser GS',
            'GeneralUser_GS': 'GeneralUser GS',
            'SGM_V2': 'SGM V2.01',
            'SGM-V2.01': 'SGM V2.01',
            'TimGM6mb': 'TimGM6mb',
            'FluidR3_GM': 'FluidR3 GM',
        }

        display_name = name_mapping.get(name, name)

        # Descriptions for known fonts
        descriptions = {
            'GeneralUser GS': 'Excellent pads and flutes',
            'SGM V2.01': 'Rich, warm ambient tones',
            'TimGM6mb': 'Compact General MIDI',
            'FluidR3 GM': 'FluidSynth GM soundfont',
        }

        return {
            'name': display_name,
            'path': path,
            'description': descriptions.get(display_name, 'General MIDI soundfont')
        }

    def get_current(self) -> Dict:
        """Get the currently selected soundfont."""
        if not self.available_fonts:
            raise RuntimeError("No soundfonts available")
        return self.available_fonts[self.current_index]

    def get_current_path(self) -> Path:
        """Get the path to the currently selected soundfont."""
        return self.get_current()['path']

    def get_current_name(self) -> str:
        """Get the name of the currently selected soundfont."""
        return self.get_current()['name']

    def next_soundfont(self):
        """Cycle to the next soundfont."""
        if len(self.available_fonts) > 1:
            self.current_index = (self.current_index + 1) % len(self.available_fonts)

    def previous_soundfont(self):
        """Cycle to the previous soundfont."""
        if len(self.available_fonts) > 1:
            self.current_index = (self.current_index - 1) % len(self.available_fonts)

    def get_all_names(self) -> List[str]:
        """Get a list of all soundfont names."""
        return [font['name'] for font in self.available_fonts]

    def count(self) -> int:
        """Get the number of available soundfonts."""
        return len(self.available_fonts)

    def get_profile_name(self) -> str:
        """Get the profile name for the current soundfont (for looking up in SOUNDFONT_PROFILES)."""
        return self.get_current_name()

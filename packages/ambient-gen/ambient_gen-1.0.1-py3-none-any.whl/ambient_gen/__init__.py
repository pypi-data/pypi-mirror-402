"""Ambient Generator - Create generative ambient music."""

__version__ = "1.0.0"
__author__ = "Beowulf Audio"
__description__ = "Create lush, generative ambient music with spacey textures"

# Extract soundfonts on first import
import tarfile
from pathlib import Path

_package_dir = Path(__file__).parent
_soundfonts_dir = _package_dir / "soundfonts"
_soundfonts_archive = _package_dir / "soundfonts.tar.xz"

def _extract_soundfonts():
    """Extract soundfonts from archive if not already extracted."""
    if not _soundfonts_dir.exists() and _soundfonts_archive.exists():
        _soundfonts_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(_soundfonts_archive, 'r:xz') as tar:
                tar.extractall(_soundfonts_dir)
        except Exception as e:
            # If extraction fails, clean up and raise
            if _soundfonts_dir.exists():
                import shutil
                shutil.rmtree(_soundfonts_dir)
            raise RuntimeError(f"Failed to extract soundfonts: {e}")

# Extract soundfonts on module import
_extract_soundfonts()

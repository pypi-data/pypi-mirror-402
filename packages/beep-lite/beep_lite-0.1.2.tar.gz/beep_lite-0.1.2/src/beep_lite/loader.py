"""WAV file loader using importlib.resources."""

import logging
from functools import lru_cache
from importlib import resources

from .types import Sound

logger = logging.getLogger(__name__)


class SoundNotFoundError(Exception):
    """Raised when a sound file cannot be found."""

    pass


@lru_cache(maxsize=16)
def load_wav(sound: Sound) -> bytes:
    """Load a WAV file from the assets directory.

    Uses importlib.resources for reliable resource loading,
    compatible with PyInstaller and other packaging tools.

    Args:
        sound: The sound to load.

    Returns:
        The WAV file data as bytes.

    Raises:
        SoundNotFoundError: If the WAV file cannot be found.
    """
    filename = f"{sound.value}.wav"

    try:
        # Python 3.9+ style using files()
        assets = resources.files("beep_lite") / "assets"
        wav_file = assets / filename

        return wav_file.read_bytes()
    except FileNotFoundError as e:
        raise SoundNotFoundError(f"WAV file not found: {filename}") from e
    except Exception as e:
        raise SoundNotFoundError(f"Failed to load WAV file {filename}: {e}") from e


def preload_all() -> None:
    """Preload all sound files into cache.

    Call this at application startup to avoid latency on first play.
    Errors are logged but not raised.
    """
    for sound in Sound:
        try:
            load_wav(sound)
            logger.debug(f"Preloaded sound: {sound.value}")
        except SoundNotFoundError as e:
            logger.warning(f"Failed to preload {sound.value}: {e}")


def clear_cache() -> None:
    """Clear the sound cache.

    Useful for testing or when sound files have been updated.
    """
    load_wav.cache_clear()

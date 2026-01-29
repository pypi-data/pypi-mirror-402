"""Core playback logic and backend selection."""

from __future__ import annotations

import logging
import sys

from .backends import Backend
from .loader import load_wav
from .types import Sound

logger = logging.getLogger(__name__)

# Module-level backend instance (lazy initialization)
_backend: Backend | None = None


def _select_backend() -> Backend:
    """Select the best available backend for the current platform.

    Priority:
    1. Windows: winsound (zero dependencies)
    2. All platforms: simpleaudio (if installed)
    3. Fallback: terminal bell

    Returns:
        An instance of the selected backend.
    """
    # Windows: prefer winsound
    if sys.platform == "win32":
        try:
            from .backends.winsound_backend import WinsoundBackend

            backend = WinsoundBackend()
            logger.debug("Selected winsound backend")
            return backend
        except ImportError:
            logger.debug("winsound not available")

    # Try simpleaudio (cross-platform)
    try:
        from .backends.simpleaudio_backend import SimpleaudioBackend

        backend = SimpleaudioBackend()
        logger.debug("Selected simpleaudio backend")
        return backend
    except ImportError:
        logger.debug("simpleaudio not available")

    # Fallback to terminal bell
    from .backends.fallback_backend import FallbackBackend

    logger.debug("Selected fallback backend (terminal bell)")
    return FallbackBackend()


def _get_backend() -> Backend:
    """Get the backend instance, initializing if necessary.

    Returns:
        The backend instance.
    """
    global _backend
    if _backend is None:
        _backend = _select_backend()
    return _backend


def _reset_backend() -> None:
    """Reset the backend instance.

    Useful for testing or when changing backends at runtime.
    """
    global _backend
    _backend = None


def play_sound(sound: Sound) -> None:
    """Play a sound using the selected backend.

    This is the core playback function. It loads the WAV data
    and delegates to the appropriate backend.

    Args:
        sound: The sound to play.

    Raises:
        SoundNotFoundError: If the WAV file cannot be found.
        Exception: If playback fails (backend-specific).
    """
    data = load_wav(sound)
    backend = _get_backend()
    backend.play(sound, data)
    logger.debug(f"Playing sound: {sound.value}")

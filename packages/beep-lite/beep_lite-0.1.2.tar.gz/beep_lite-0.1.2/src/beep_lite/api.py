"""Public API for beep-lite.

This module provides the main user-facing functions for playing notification sounds.
All functions are designed to be safe - they will never raise exceptions that could
crash the application.

Example:
    >>> import beep_lite as beep
    >>> beep.ok()      # Play success sound
    >>> beep.ng()      # Play error sound
    >>> beep.play(Sound.SCAN_OK)  # Play using enum
"""

import logging

from .core import play_sound
from .types import Sound

logger = logging.getLogger(__name__)


def ok() -> None:
    """Play the OK/success notification sound.

    Use this for normal completion of operations.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.OK)
    except Exception as e:
        logger.warning(f"Failed to play OK sound: {e}")


def ng() -> None:
    """Play the NG/error notification sound.

    Use this for errors or failures.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.NG)
    except Exception as e:
        logger.warning(f"Failed to play NG sound: {e}")


def warn() -> None:
    """Play the warning notification sound.

    Use this for warnings that need attention.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.WARN)
    except Exception as e:
        logger.warning(f"Failed to play WARN sound: {e}")


def crit() -> None:
    """Play the critical/urgent notification sound.

    Use this for critical situations requiring immediate attention.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.CRIT)
    except Exception as e:
        logger.warning(f"Failed to play CRIT sound: {e}")


def moo() -> None:
    """Play the 'moo' notification sound.

    A playful low-frequency notification sound.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.MOO)
    except Exception as e:
        logger.warning(f"Failed to play MOO sound: {e}")


def mew() -> None:
    """Play the 'mew' notification sound.

    A light high-frequency notification sound.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.MEW)
    except Exception as e:
        logger.warning(f"Failed to play MEW sound: {e}")


def scan_ok() -> None:
    """Play the scan success notification sound.

    Use this for successful barcode/QR scans.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.SCAN_OK)
    except Exception as e:
        logger.warning(f"Failed to play SCAN_OK sound: {e}")


def scan_ng() -> None:
    """Play the scan failure notification sound.

    Use this for failed barcode/QR scans.
    Never raises exceptions - errors are logged as warnings.
    """
    try:
        play_sound(Sound.SCAN_NG)
    except Exception as e:
        logger.warning(f"Failed to play SCAN_NG sound: {e}")


def play(sound: Sound) -> None:
    """Play a notification sound by Sound enum.

    This is the generic play function that accepts any Sound enum value.
    Never raises exceptions - errors are logged as warnings.

    Args:
        sound: The Sound enum value to play.

    Example:
        >>> from beep_lite import play, Sound
        >>> play(Sound.OK)
        >>> play(Sound.SCAN_NG)
    """
    try:
        play_sound(sound)
    except Exception as e:
        logger.warning(f"Failed to play {sound.value} sound: {e}")

"""beep-lite: Cross-platform notification sound library.

A lightweight library for playing notification sounds in industrial
and business applications. Works on Windows, macOS, and Linux.

Basic usage:
    >>> import beep_lite as beep
    >>> beep.ok()       # Success sound
    >>> beep.ng()       # Error sound
    >>> beep.warn()     # Warning sound
    >>> beep.crit()     # Critical sound

Using Sound enum:
    >>> from beep_lite import play, Sound
    >>> play(Sound.SCAN_OK)
    >>> play(Sound.SCAN_NG)

All functions are exception-safe - they will never crash your application.
Errors are logged as warnings.
"""

from .api import crit, mew, moo, ng, ok, play, scan_ng, scan_ok, warn
from .loader import clear_cache, preload_all
from .types import Sound

__version__ = "0.1.0"
__all__ = [
    # Main API functions
    "ok",
    "ng",
    "warn",
    "crit",
    "moo",
    "mew",
    "scan_ok",
    "scan_ng",
    "play",
    # Types
    "Sound",
    # Utilities
    "preload_all",
    "clear_cache",
    # Metadata
    "__version__",
]

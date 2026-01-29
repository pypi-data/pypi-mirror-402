"""Sound type definitions for beep-lite."""

from enum import Enum


class Sound(Enum):
    """Enumeration of available notification sounds.

    Each value corresponds to a WAV file in the assets directory.

    Attributes:
        OK: Normal completion sound (bright, ascending)
        NG: Error/failure sound (descending, slightly longer)
        WARN: Warning sound (two-tone alert)
        CRIT: Critical/urgent sound (three low tones)
        MOO: Playful notification (low frequency sweep)
        MEW: Light notification (high frequency sweep)
        SCAN_OK: Scan success (very short, sharp)
        SCAN_NG: Scan failure (low, short)
    """

    OK = "ok"
    NG = "ng"
    WARN = "warn"
    CRIT = "crit"
    MOO = "moo"
    MEW = "mew"
    SCAN_OK = "scan_ok"
    SCAN_NG = "scan_ng"

"""Fallback backend using terminal bell."""

import logging
import sys

from ..types import Sound

logger = logging.getLogger(__name__)


class FallbackBackend:
    """Fallback backend using terminal bell.

    This backend works on any platform but only produces a simple beep.
    It ignores the actual sound type and just outputs the bell character.
    """

    def play(self, sound: Sound, data: bytes) -> None:
        """Play a terminal bell sound.

        Args:
            sound: The sound type (ignored, only bell is played).
            data: The WAV file data (ignored).
        """
        try:
            # Output bell character to stderr to avoid interfering with stdout
            sys.stderr.write("\a")
            sys.stderr.flush()
        except Exception as e:
            logger.warning(f"Fallback bell failed: {e}")

    def is_available(self) -> bool:
        """Check if fallback is available.

        Returns:
            Always True, as terminal bell should work anywhere.
        """
        return True

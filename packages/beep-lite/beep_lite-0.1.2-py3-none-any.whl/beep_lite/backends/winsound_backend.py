"""Windows winsound backend implementation."""

import logging
import sys
import tempfile
import threading
from pathlib import Path

from ..types import Sound

logger = logging.getLogger(__name__)


class WinsoundBackend:
    """Backend using Windows winsound module.

    This backend is only available on Windows and has zero external dependencies.
    Uses SND_ASYNC for non-blocking playback.
    """

    def __init__(self) -> None:
        """Initialize the winsound backend."""
        if sys.platform != "win32":
            raise ImportError("winsound is only available on Windows")

        # Import here to avoid errors on non-Windows platforms
        import winsound

        self._winsound = winsound
        self._temp_dir = Path(tempfile.gettempdir()) / "beep_lite"
        self._temp_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def play(self, sound: Sound, data: bytes) -> None:
        """Play a sound asynchronously using winsound.

        Args:
            sound: The sound type to play.
            data: The WAV file data as bytes.
        """
        try:
            # winsound.PlaySound with SND_MEMORY doesn't work well with SND_ASYNC
            # So we write to a temp file and play from there
            temp_file = self._temp_dir / f"{sound.value}.wav"

            with self._lock:
                temp_file.write_bytes(data)

            self._winsound.PlaySound(
                str(temp_file),
                self._winsound.SND_FILENAME | self._winsound.SND_ASYNC,
            )
        except Exception as e:
            logger.warning(f"winsound playback failed for {sound.value}: {e}")

    def is_available(self) -> bool:
        """Check if winsound is available.

        Returns:
            True on Windows, False otherwise.
        """
        return sys.platform == "win32"

"""Backend implementations for sound playback."""

from typing import Protocol

from ..types import Sound


class Backend(Protocol):
    """Protocol for sound playback backends.

    All backend implementations must conform to this interface.
    """

    def play(self, sound: Sound, data: bytes) -> None:
        """Play a sound asynchronously.

        Args:
            sound: The sound type to play.
            data: The WAV file data as bytes.

        Note:
            This method should not block the calling thread.
            Implementations should handle errors gracefully without raising.
        """
        ...

    def is_available(self) -> bool:
        """Check if this backend is available on the current system.

        Returns:
            True if the backend can be used, False otherwise.
        """
        ...

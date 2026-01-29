"""Base TTS backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


class TTSBackend(ABC):
    """Abstract base class for TTS backends."""

    name: str = "base"
    sample_rate: int = 22050

    def __init__(
        self,
        voice: str,
        models_dir: Path | None = None,
        console: Console | None = None,
    ):
        """
        Initialize the TTS backend.

        Args:
            voice: Voice model/name to use
            models_dir: Directory for storing models
            console: Rich console for output
        """
        self.voice = voice
        self.models_dir = models_dir or Path.cwd() / "models"
        self.console = console
        self.models_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def setup(self) -> None:
        """Download/prepare the model. Called once before generating."""
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        output_path: Path,
        **kwargs,
    ) -> bool:
        """
        Generate audio for a single text segment.

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            **kwargs: Backend-specific parameters

        Returns:
            True if successful, False otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def list_voices(cls) -> dict[str, tuple[str, str]]:
        """
        List available voices for this backend.

        Returns:
            Dict mapping voice ID to (display_name, description)
        """
        pass

    @classmethod
    @abstractmethod
    def default_voice(cls) -> str:
        """Return the default voice for this backend."""
        pass

    def log(self, message: str, style: str = "") -> None:
        """Log a message to console or stdout."""
        if self.console:
            if style:
                self.console.print(f"[{style}]{message}[/{style}]")
            else:
                self.console.print(message)
        else:
            print(message)

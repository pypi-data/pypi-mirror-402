"""Piper TTS backend."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from quickcall_voiceover.backends.base import TTSBackend

if TYPE_CHECKING:
    from rich.console import Console


class PiperBackend(TTSBackend):
    """Piper TTS backend implementation."""

    name = "piper"
    sample_rate = 22050

    # Popular Piper voices
    VOICES = {
        "en_US-hfc_male-medium": ("Male (US)", "Clear male voice, medium quality"),
        "en_US-hfc_female-medium": ("Female (US)", "Clear female voice, medium quality"),
        "en_US-amy-medium": ("Amy (US)", "Natural female voice"),
        "en_US-joe-medium": ("Joe (US)", "Natural male voice"),
        "en_US-ryan-high": ("Ryan (US)", "High quality male voice"),
        "en_US-lessac-high": ("Lessac (US)", "High quality female voice"),
        "en_GB-alan-medium": ("Alan (UK)", "British male voice"),
        "en_GB-alba-medium": ("Alba (UK)", "British female voice"),
        "en_GB-cori-high": ("Cori (UK)", "High quality British female"),
    }

    DEFAULT_VOICE = "en_US-hfc_male-medium"

    def __init__(
        self,
        voice: str,
        models_dir: Path | None = None,
        console: Console | None = None,
        length_scale: float = 1.0,
        noise_scale: float = 0.667,
        noise_w: float = 0.8,
        sentence_silence: float = 0.5,
    ):
        super().__init__(voice, models_dir, console)
        self.length_scale = length_scale
        self.noise_scale = noise_scale
        self.noise_w = noise_w
        self.sentence_silence = sentence_silence
        self.model_path: Path | None = None

    def setup(self) -> None:
        """Download voice model if not present."""
        from piper.download_voices import download_voice

        model_file = self.models_dir / f"{self.voice}.onnx"
        if model_file.exists():
            self.log(f"✓ Voice model cached: {self.voice}", "green")
            self.model_path = model_file
            return

        self.log(f"↓ Downloading voice model: {self.voice}...", "yellow")
        download_voice(self.voice, self.models_dir)
        self.log(f"✓ Downloaded to: {self.models_dir}", "green")
        self.model_path = model_file

    def generate(
        self,
        text: str,
        output_path: Path,
        **kwargs,
    ) -> bool:
        """Generate audio using Piper CLI."""
        if not self.model_path:
            self.setup()

        length_scale = kwargs.get("length_scale", self.length_scale)
        noise_scale = kwargs.get("noise_scale", self.noise_scale)
        noise_w = kwargs.get("noise_w", self.noise_w)
        sentence_silence = kwargs.get("sentence_silence", self.sentence_silence)

        cmd = [
            sys.executable,
            "-m",
            "piper",
            "--model",
            str(self.model_path),
            "--output_file",
            str(output_path),
            "--length_scale",
            str(length_scale),
            "--noise_scale",
            str(noise_scale),
            "--noise_w",
            str(noise_w),
            "--sentence_silence",
            str(sentence_silence),
        ]

        try:
            subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Error generating audio: {e.stderr}", "red")
            return False

    @classmethod
    def list_voices(cls) -> dict[str, tuple[str, str]]:
        """List available Piper voices."""
        return cls.VOICES

    @classmethod
    def default_voice(cls) -> str:
        """Return the default Piper voice."""
        return cls.DEFAULT_VOICE

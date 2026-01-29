"""Kokoro TTS backend."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from quickcall_voiceover.backends.base import TTSBackend

if TYPE_CHECKING:
    from rich.console import Console


class KokoroBackend(TTSBackend):
    """Kokoro-82M TTS backend implementation."""

    name = "kokoro"
    sample_rate = 24000

    # Kokoro voices - format: voice_id -> (display_name, description)
    # Voice naming: first letter = language, second letter = gender (f=female, m=male)
    VOICES = {
        # American English
        "af_heart": ("Heart (US Female)", "Warm, expressive American female"),
        "af_bella": ("Bella (US Female)", "Clear American female"),
        "af_nicole": ("Nicole (US Female)", "Professional American female"),
        "af_sarah": ("Sarah (US Female)", "Friendly American female"),
        "af_sky": ("Sky (US Female)", "Bright American female"),
        "am_adam": ("Adam (US Male)", "Clear American male"),
        "am_michael": ("Michael (US Male)", "Professional American male"),
        # British English
        "bf_emma": ("Emma (UK Female)", "British female"),
        "bf_isabella": ("Isabella (UK Female)", "Elegant British female"),
        "bm_george": ("George (UK Male)", "British male"),
        "bm_lewis": ("Lewis (UK Male)", "Clear British male"),
    }

    # Language code mapping
    LANG_CODES = {
        "a": "American English",
        "b": "British English",
        "e": "Spanish",
        "f": "French",
        "h": "Hindi",
        "i": "Italian",
        "j": "Japanese",
        "p": "Brazilian Portuguese",
        "z": "Mandarin Chinese",
    }

    DEFAULT_VOICE = "af_heart"

    def __init__(
        self,
        voice: str,
        models_dir: Path | None = None,
        console: Console | None = None,
        speed: float = 1.0,
        lang_code: str | None = None,
    ):
        super().__init__(voice, models_dir, console)
        self.speed = speed
        # Auto-detect language from voice name (first letter)
        self.lang_code = lang_code or voice[0] if voice else "a"
        self.pipeline = None

    def setup(self) -> None:
        """Initialize the Kokoro pipeline."""
        try:
            from kokoro import KPipeline

            self.log(f"Initializing Kokoro ({self.LANG_CODES.get(self.lang_code, 'Unknown')})...")
            self.pipeline = KPipeline(lang_code=self.lang_code)
            self.log(f"✓ Kokoro ready with voice: {self.voice}", "green")
        except ImportError:
            self.log("Error: kokoro not installed. Run: uv add kokoro soundfile", "red")
            raise
        except Exception as e:
            self.log(f"Error initializing Kokoro: {e}", "red")
            raise

    def generate(
        self,
        text: str,
        output_path: Path,
        **kwargs,
    ) -> bool:
        """Generate audio using Kokoro."""
        import soundfile as sf

        if not self.pipeline:
            self.setup()

        speed = kwargs.get("speed", self.speed)
        voice = kwargs.get("voice", self.voice)

        try:
            # Kokoro returns a generator of (graphemes, phonemes, audio)
            generator = self.pipeline(text, voice=voice, speed=speed)

            # Collect all audio chunks
            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio)

            if not audio_chunks:
                self.log("No audio generated", "red")
                return False

            # Concatenate and save
            import numpy as np

            full_audio = np.concatenate(audio_chunks)
            sf.write(str(output_path), full_audio, self.sample_rate)
            return True

        except Exception as e:
            self.log(f"Error generating audio: {e}", "red")
            return False

    @classmethod
    def list_voices(cls) -> dict[str, tuple[str, str]]:
        """List available Kokoro voices."""
        return cls.VOICES

    @classmethod
    def default_voice(cls) -> str:
        """Return the default Kokoro voice."""
        return cls.DEFAULT_VOICE

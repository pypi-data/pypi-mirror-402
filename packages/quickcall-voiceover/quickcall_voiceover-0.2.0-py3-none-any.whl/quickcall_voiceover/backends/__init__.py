"""TTS backend implementations."""

from quickcall_voiceover.backends.base import TTSBackend
from quickcall_voiceover.backends.kokoro import KokoroBackend
from quickcall_voiceover.backends.piper import PiperBackend

__all__ = ["TTSBackend", "PiperBackend", "KokoroBackend", "get_backend"]

BACKENDS = {
    "piper": PiperBackend,
    "kokoro": KokoroBackend,
}


def get_backend(name: str) -> type[TTSBackend]:
    """Get a TTS backend by name."""
    if name not in BACKENDS:
        available = ", ".join(BACKENDS.keys())
        raise ValueError(f"Unknown backend '{name}'. Available: {available}")
    return BACKENDS[name]

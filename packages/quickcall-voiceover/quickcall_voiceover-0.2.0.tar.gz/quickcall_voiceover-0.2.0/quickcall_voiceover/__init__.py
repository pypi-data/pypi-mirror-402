"""QuickCall VoiceOver - Multi-backend TTS for creating voice-over audio assets."""

__version__ = "0.2.0"

from quickcall_voiceover.backends import BACKENDS, TTSBackend, get_backend
from quickcall_voiceover.generator import generate_from_text, generate_voiceover

__all__ = [
    "generate_voiceover",
    "generate_from_text",
    "get_backend",
    "BACKENDS",
    "TTSBackend",
    "__version__",
]

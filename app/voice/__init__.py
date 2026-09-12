"""Voice processing package using Google Gemini Multimodal Audio ASR and Google Text-to-Speech."""
from .voice_service import transcribe_audio, synthesize_speech, get_language_code

__all__ = [
    "transcribe_audio",
    "synthesize_speech",
    "get_language_code",
]

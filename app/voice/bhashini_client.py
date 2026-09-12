"""
Voice processing module powered exclusively by Google Gemini Multimodal Audio ASR and Google Text-to-Speech (gTTS).
Retained for backwards compatibility with any existing imports.
"""
from .voice_service import (
    transcribe_audio,
    synthesize_speech,
    get_language_code,
    LANG_CODE_MAP,
)

__all__ = [
    "transcribe_audio",
    "synthesize_speech",
    "get_language_code",
    "LANG_CODE_MAP",
]

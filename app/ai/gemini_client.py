import logging
import json
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("gemini_client")

# Active verified models on Google AI Studio
VERIFIED_GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
]


def is_gemini_configured() -> bool:
    """Check whether a real Gemini API key is configured."""
    key = settings.GEMINI_API_KEY or ""
    return bool(key and "your_gemini" not in key and len(key.strip()) > 10)

def call_gemini_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = 3
) -> str:
    """
    Call Google Gemini API using google-genai SDK.
    Supports system instructions, structured JSON, AFC suppression, and automatic model fallback.
    """
    if not is_gemini_configured():
        logger.info("[GEMINI] GEMINI_API_KEY not configured.")
        return ""

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai package not installed.")
        return ""

    clean_key = settings.GEMINI_API_KEY.strip()
    client = genai.Client(api_key=clean_key)

    # Separate system instruction and chat history
    system_instruction = None
    formatted_contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = content
        else:
            formatted_contents.append(content)

    prompt_content = "\n\n".join(formatted_contents) if formatted_contents else "Hello"

    config_kwargs: Dict[str, Any] = {
        "temperature": temperature,
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if response_format and response_format.get("type") == "json_object":
        config_kwargs["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**config_kwargs)

    # Prioritize configured model if specified, followed by verified available models
    configured_model = settings.GEMINI_MODEL.strip() if settings.GEMINI_MODEL else "gemini-2.5-flash"
    candidate_list = [configured_model] + VERIFIED_GEMINI_MODELS
    seen = set()
    models_to_try = [m for m in candidate_list if not (m in seen or seen.add(m))]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_content,
                config=config,
            )
            if response:
                # 1. Try .text attribute
                try:
                    if response.text and response.text.strip():
                        return response.text.strip()
                except Exception:
                    pass
                # 2. Extract from candidates/parts if .text accessor fails
                if hasattr(response, "candidates") and response.candidates:
                    parts = getattr(response.candidates[0].content, "parts", [])
                    text_parts = [p.text for p in parts if getattr(p, "text", None)]
                    if text_parts:
                        return "\n".join(text_parts).strip()
        except Exception as e:
            logger.warning(f"Gemini call to model '{model_name}' failed: {e}. Trying next candidate if available.")

    logger.error("All Gemini candidate models failed.")
    return ""

def transcribe_audio_gemini(
    audio_bytes: bytes,
    mime_type: str = "audio/ogg",
    source_language: str = "kannada"
) -> str:
    """
    Transcribe spoken regional language voice notes using Gemini Multimodal Audio.
    """
    if not is_gemini_configured() or not audio_bytes:
        return ""

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai package not installed.")
        return ""

    clean_key = settings.GEMINI_API_KEY.strip()
    client = genai.Client(api_key=clean_key)

    prompt = (
        f"You are an expert speech recognition system for rural Indian entrepreneurs. "
        f"Transcribe this audio recording accurately into text in its original spoken language "
        f"(such as {source_language}, Hindi, Marathi, Telugu, Tamil, or English). "
        f"Return ONLY the plain transcribed text without markdown, quotes, or explanations."
    )

    # Detect audio format from magic bytes if possible
    detected_mime = mime_type
    if audio_bytes.startswith(b"OggS"):
        detected_mime = "audio/ogg"
    elif audio_bytes.startswith(b"RIFF"):
        detected_mime = "audio/wav"
    elif audio_bytes.startswith(b"ID3") or audio_bytes[:2] in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"]:
        detected_mime = "audio/mp3"

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=detected_mime)

    config = types.GenerateContentConfig(
        temperature=0.1,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    AUDIO_MODELS = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3-flash-preview",
    ]

    for model_name in AUDIO_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[audio_part, prompt],
                config=config,
            )
            if response:
                try:
                    if response.text and response.text.strip():
                        transcript = response.text.strip()
                        logger.info(f"Gemini Audio Transcription ({model_name}): {transcript[:60]}...")
                        return transcript
                except Exception:
                    pass
                if hasattr(response, "candidates") and response.candidates:
                    parts = getattr(response.candidates[0].content, "parts", [])
                    text_parts = [p.text for p in parts if getattr(p, "text", None)]
                    if text_parts:
                        transcript = "\n".join(text_parts).strip()
                        logger.info(f"Gemini Audio Transcription ({model_name}): {transcript[:60]}...")
                        return transcript
        except Exception as e:
            logger.warning(f"Gemini audio transcription failed on {model_name}: {e}")

    return ""

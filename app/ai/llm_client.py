import logging
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.ai.gemini_client import is_gemini_configured, call_gemini_chat

logger = logging.getLogger("llm_client")

def call_llm_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = 3
) -> str:
    """
    Direct LLM caller using Google Gemini.
    Zero-cost tier, supports JSON schema and multilingual reasoning.
    Returns empty string if unavailable so the caller uses rich deterministic logic.
    """
    if is_gemini_configured():
        gemini_result = call_gemini_chat(
            messages=messages,
            temperature=temperature,
            response_format=response_format,
            max_retries=max_retries
        )
        if gemini_result and gemini_result.strip():
            return gemini_result.strip()
        logger.warning("Gemini returned empty or was rate-limited.")

    # If Gemini not configured or returned empty, return valid empty JSON or empty string
    if response_format and response_format.get("type") == "json_object":
        return json.dumps({
            "trade": None,
            "district": None,
            "state": None,
            "available_capital": None,
            "project_cost": None,
            "language": "kannada"
        })

    return ""

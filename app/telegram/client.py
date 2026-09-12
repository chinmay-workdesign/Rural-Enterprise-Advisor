import io
import logging
import requests
from typing import Optional, Dict, Any, Union
from app.config import settings

logger = logging.getLogger("telegram_client")

TELEGRAM_API_BASE = "https://api.telegram.org"

def _get_bot_url() -> str:
    return f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}"

def _split_telegram_message(text: str, max_len: int = 3800) -> list:
    """Split message into safe chunks under Telegram's 4096-character limit."""
    if not text or len(text) <= max_len:
        return [text] if text else []

    chunks = []
    current_chunk = ""
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_len:
            current_chunk += (para + "\n\n")
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            if len(para) > max_len:
                lines = para.split("\n")
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= max_len:
                        current_chunk += (line + "\n")
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        while len(line) > max_len:
                            chunks.append(line[:max_len])
                            line = line[max_len:]
                        current_chunk = line + "\n"
            else:
                current_chunk = para + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]

def _send_single_telegram_chunk(
    chat_id: Union[str, int],
    text_chunk: str,
    parse_mode: Optional[str] = "Markdown"
) -> Dict[str, Any]:
    """Send a single chunk to Telegram with markdown fallback."""
    url = f"{_get_bot_url()}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text_chunk,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload, timeout=12)
        # If markdown formatting failed, retry without markdown
        if response.status_code == 400 and parse_mode:
            payload.pop("parse_mode")
            response = requests.post(url, json=payload, timeout=12)

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram chunk to {chat_id}: {e}")
        return {"error": str(e), "success": False}

def send_telegram_text(
    chat_id: Union[str, int],
    text: str,
    parse_mode: Optional[str] = "Markdown"
) -> Dict[str, Any]:
    """Send text message to recipient via Telegram Bot API with automatic message chunking for 4096 character limit."""
    if not settings.TELEGRAM_BOT_TOKEN or not str(chat_id).lstrip("-").isdigit():
        logger.info(f"[MOCK TELEGRAM] To Chat: {chat_id} | Message: {text[:60]}...")
        return {"mock": True, "status": "sent", "chat_id": chat_id, "text": text}

    chunks = _split_telegram_message(text, max_len=3800)
    last_res = {}
    for idx, chunk in enumerate(chunks):
        last_res = _send_single_telegram_chunk(chat_id, chunk, parse_mode)
        if idx < len(chunks) - 1:
            import time
            time.sleep(0.3)

    logger.info(f"Sent Telegram message ({len(chunks)} chunk(s)) to {chat_id}")
    return last_res

def send_telegram_document(
    chat_id: Union[str, int],
    document: Union[str, bytes],
    filename: str = "Detailed_Project_Report.pdf",
    caption: str = ""
) -> Dict[str, Any]:
    """Send document (DPR PDF / Sanction letter) to recipient via Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN or not str(chat_id).lstrip("-").isdigit():
        logger.info(f"[MOCK TELEGRAM DOCUMENT] To: {chat_id} | Filename: {filename} | Caption: {caption}")
        return {"mock": True, "status": "sent", "chat_id": chat_id, "filename": filename}

    url = f"{_get_bot_url()}/sendDocument"

    try:
        # If document is a URL string
        if isinstance(document, str) and (document.startswith("http://") or document.startswith("https://")):
            payload = {
                "chat_id": str(chat_id),
                "document": document,
                "caption": caption
            }
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                return response.json()
            # If Telegram couldn't fetch remote URL directly, download and stream
            doc_resp = requests.get(document, timeout=15)
            if doc_resp.status_code == 200:
                document = doc_resp.content

        # If document is bytes (or downloaded)
        if isinstance(document, (bytes, bytearray)):
            files = {"document": (filename, io.BytesIO(document), "application/pdf")}
            data = {"chat_id": str(chat_id), "caption": caption}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return response.json()

        return {"error": "Invalid document type", "success": False}
    except Exception as e:
        logger.error(f"Failed to send Telegram document to {chat_id}: {e}")
        return {"error": str(e), "success": False}

def get_telegram_file_url(file_id: str) -> Optional[str]:
    """Retrieve temporary download URL for a file_id from Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return f"https://mock.telegram.org/file/{file_id}"

    url = f"{_get_bot_url()}/getFile"
    try:
        response = requests.get(url, params={"file_id": file_id}, timeout=10)
        response.raise_for_status()
        data = response.json()
        file_path = data.get("result", {}).get("file_path")
        if file_path:
            return f"{TELEGRAM_API_BASE}/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to get Telegram file URL for {file_id}: {e}")
        return None

def download_telegram_file(file_id: str) -> Optional[bytes]:
    """Download voice note (.oga/.ogg) or document bytes from Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info(f"[MOCK TELEGRAM] Downloading mock audio bytes for {file_id}")
        return b"MOCK_TELEGRAM_AUDIO_BYTES_FOR_GEMINI"

    file_url = get_telegram_file_url(file_id)
    if not file_url:
        return None

    try:
        response = requests.get(file_url, timeout=20)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to download Telegram file content: {e}")
        return None

def send_telegram_voice(chat_id: str, voice: Union[str, bytes], caption: Optional[str] = None) -> Dict[str, Any]:
    """Send voice audio note to Telegram chat via /sendVoice."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info(f"[MOCK TELEGRAM VOICE] To: {chat_id}")
        return {"mock": True, "status": "sent", "chat_id": chat_id}

    url = f"{_get_bot_url()}/sendVoice"
    try:
        if isinstance(voice, (bytes, bytearray)):
            files = {"voice": ("voice.mp3", io.BytesIO(voice), "audio/mpeg")}
            data = {"chat_id": str(chat_id)}
            if caption:
                data["caption"] = caption[:1024]
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        elif isinstance(voice, str) and (voice.startswith("http://") or voice.startswith("https://")):
            payload = {"chat_id": str(chat_id), "voice": voice}
            if caption:
                payload["caption"] = caption[:1024]
            response = requests.post(url, json=payload, timeout=20)
            return response.json()
        return {"error": "Invalid voice type", "success": False}
    except Exception as e:
        logger.error(f"Failed to send Telegram voice note to {chat_id}: {e}")
        return {"error": str(e), "success": False}


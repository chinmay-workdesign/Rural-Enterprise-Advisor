import logging
import requests
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("whatsapp_client")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

def send_whatsapp_text(recipient_phone: str, text_body: str) -> Dict[str, Any]:
    """Send text message to recipient via Meta WhatsApp Cloud API."""
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.PHONE_NUMBER_ID:
        logger.info(f"[MOCK WHATSAPP] To: {recipient_phone} | Message: {text_body}")
        return {"mock": True, "status": "sent", "to": recipient_phone, "body": text_body}

    url = f"{GRAPH_API_BASE}/{settings.PHONE_NUMBER_ID}/messages"
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {"preview_url": True, "body": text_body},
    }

    try:
        response = requests.post(url, json=data, headers=_headers(), timeout=10)
        response.raise_for_status()
        logger.info(f"Sent WhatsApp text to {recipient_phone}, status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp text to {recipient_phone}: {e}")
        return {"error": str(e), "success": False}

def send_whatsapp_document(
    recipient_phone: str,
    document_url: str,
    filename: str,
    caption: str
) -> Dict[str, Any]:
    """Send document (DPR PDF / Sanction letter) to recipient via Meta WhatsApp Cloud API."""
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.PHONE_NUMBER_ID:
        logger.info(f"[MOCK WHATSAPP DOCUMENT] To: {recipient_phone} | URL: {document_url} | Filename: {filename} | Caption: {caption}")
        return {"mock": True, "status": "sent", "to": recipient_phone, "document_url": document_url}

    url = f"{GRAPH_API_BASE}/{settings.PHONE_NUMBER_ID}/messages"
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "document",
        "document": {"link": document_url, "filename": filename, "caption": caption},
    }

    try:
        response = requests.post(url, json=data, headers=_headers(), timeout=10)
        response.raise_for_status()
        logger.info(f"Sent WhatsApp document to {recipient_phone}: {filename}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp document to {recipient_phone}: {e}")
        return {"error": str(e), "success": False}

def fetch_media_url(media_id: str) -> Optional[str]:
    """Retrieve temporary download URL for a media asset via Graph API."""
    if not settings.WHATSAPP_ACCESS_TOKEN:
        logger.info(f"[MOCK WHATSAPP] Fetch media URL for ID: {media_id}")
        return f"https://mock.graph.facebook.com/v21.0/{media_id}"

    url = f"{GRAPH_API_BASE}/{media_id}"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}, timeout=10)
        response.raise_for_status()
        return response.json().get("url")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch media URL for {media_id}: {e}")
        return None

def download_media_bytes(media_id: str) -> Optional[bytes]:
    """Download audio/media binary payload from Meta Graph API."""
    if not settings.WHATSAPP_ACCESS_TOKEN:
        logger.info(f"[MOCK WHATSAPP] Downloading mock media bytes for {media_id}")
        return b"MOCK_OGG_AUDIO_BYTES_FOR_TESTING"

    media_url = fetch_media_url(media_id)
    if not media_url:
        return None

    try:
        response = requests.get(media_url, headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}, timeout=20)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to download media bytes for {media_id}: {e}")
        return None

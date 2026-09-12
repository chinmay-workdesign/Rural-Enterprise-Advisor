import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.db import crud

logger = logging.getLogger("whatsapp_webhook")

router = APIRouter()

def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Validate X-Hub-Signature-256 HMAC against WHATSAPP_APP_SECRET."""
    if not settings.WHATSAPP_APP_SECRET:
        # In local dev / test if app secret not configured, bypass
        return True
    if not signature_header:
        return False
    parts = signature_header.split("sha256=")
    if len(parts) != 2:
        return False
    expected_hash = parts[1]
    computed_hash = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hash, computed_hash)

@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Meta webhook subscription verification endpoint."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification request: mode={mode}, token_match={token == settings.WHATSAPP_VERIFY_TOKEN}")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return Response(content="Verification failed", status_code=403)

@router.post("/webhook/whatsapp")
async def handle_whatsapp_message(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inbound WhatsApp webhook handler with signature validation and idempotency."""
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Security check: Validate signature if secret provided
    if settings.WHATSAPP_APP_SECRET and not verify_signature(body_bytes, signature):
        logger.warning("Rejected webhook: Invalid X-Hub-Signature-256")
        return Response(content="Invalid signature", status_code=403)

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to decode JSON payload: {e}")
        return Response(content="Invalid JSON", status_code=400)

    # Late import to prevent circular dependency
    from app.dialogue.conversation_state import process_user_query, process_voice_query

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    msg_id = msg.get("id")
                    from_phone = msg.get("from")
                    msg_type = msg.get("type")

                    # Idempotency check: Deduplicate retried webhook events
                    if msg_id:
                        if crud.is_webhook_processed(db, msg_id):
                            logger.info(f"Duplicate webhook message {msg_id} ignored.")
                            continue
                        crud.record_webhook_event(db, msg_id, from_phone, msg_type)

                    logger.info(f"Processing inbound message from {from_phone} of type {msg_type} (id: {msg_id})")

                    if msg_type == "text":
                        body = msg.get("text", {}).get("body", "").strip()
                        background_tasks.add_task(process_user_query, from_phone, body)
                    elif msg_type == "audio":
                        media_id = msg.get("audio", {}).get("id")
                        background_tasks.add_task(process_voice_query, from_phone, media_id)
                    else:
                        logger.info(f"Unhandled message type: {msg_type}")
    except Exception as e:
        logger.error(f"Error parsing WhatsApp payload: {e}", exc_info=True)

    return Response(content="EVENT_RECEIVED", status_code=200)

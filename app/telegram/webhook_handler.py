import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

logger = logging.getLogger("telegram_webhook")

router = APIRouter()

@router.post("/webhook/telegram")
async def handle_telegram_update(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inbound Telegram webhook update handler."""
    try:
        update = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Telegram webhook JSON: {e}")
        return Response(content="Invalid JSON", status_code=400)

    # Late import to prevent circular dependencies
    from app.dialogue.conversation_state import process_telegram_query, process_telegram_voice_query

    message = update.get("message") or update.get("edited_message")
    if not message:
        return Response(content="OK", status_code=200)

    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    from_user = message.get("from", {})
    first_name = from_user.get("first_name") or from_user.get("username") or "Entrepreneur"

    if "text" in message:
        text_body = message.get("text", "").strip()
        logger.info(f"Received Telegram text from {chat_id} ({first_name}): '{text_body}'")
        background_tasks.add_task(process_telegram_query, chat_id, text_body, first_name)
    elif "voice" in message:
        voice = message.get("voice", {})
        file_id = voice.get("file_id")
        logger.info(f"Received Telegram voice note from {chat_id} ({first_name}): file_id={file_id}")
        background_tasks.add_task(process_telegram_voice_query, chat_id, file_id, first_name)
    elif "audio" in message:
        audio = message.get("audio", {})
        file_id = audio.get("file_id")
        logger.info(f"Received Telegram audio file from {chat_id} ({first_name}): file_id={file_id}")
        background_tasks.add_task(process_telegram_voice_query, chat_id, file_id, first_name)

    return Response(content="OK", status_code=200)

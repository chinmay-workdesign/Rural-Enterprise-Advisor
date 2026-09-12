"""
Telegram Long-Polling Runner for Rural Micro-Enterprise Advisory System.
Zero-tunnel local execution: run this script to test the full system directly on Telegram!
Usage:
    python scripts/run_telegram_polling.py
"""
import os
import sys
import time
import logging
import requests

# Reconfigure stdout/stderr for UTF-8 on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.db.session import init_db
from app.dialogue.conversation_state import process_telegram_query, process_telegram_voice_query

import socket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telegram_polling")

_SINGLETON_PORT = 49153
_singleton_socket = None

def _kill_process_on_port(port: int):
    """Find and kill any process holding the singleton lock port."""
    if sys.platform == "win32":
        try:
            import subprocess
            res = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
            for line in res.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = int(parts[-1])
                    if pid != os.getpid():
                        logger.info(f"Terminating previous polling process on port {port} (PID {pid})...")
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        except Exception as e:
            logger.debug(f"Port scan exception: {e}")

def acquire_singleton_lock():
    """Acquire system-wide singleton socket lock to guarantee only ONE polling instance runs."""
    global _singleton_socket
    _singleton_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _singleton_socket.bind(("127.0.0.1", _SINGLETON_PORT))
        _singleton_socket.listen(1)
    except OSError:
        logger.warning(f"Port {_SINGLETON_PORT} in use by previous instance. Terminating...")
        _kill_process_on_port(_SINGLETON_PORT)
        time.sleep(1.0)
        try:
            _singleton_socket.bind(("127.0.0.1", _SINGLETON_PORT))
            _singleton_socket.listen(1)
        except OSError:
            logger.error(f"Cannot acquire singleton lock on port {_SINGLETON_PORT}. Another polling process is active.")
            sys.exit(0)
    logger.info(f"Singleton lock acquired on 127.0.0.1:{_SINGLETON_PORT} (PID {os.getpid()})")

def poll_telegram_updates():
    acquire_singleton_lock()
    if not settings.TELEGRAM_BOT_TOKEN:
        print("\n" + "="*70)
        print("⚠️  ERROR: TELEGRAM_BOT_TOKEN is not configured in .env!")
        print("Please open Telegram, chat with @BotFather, create a bot,")
        print("and paste your bot token into .env:")
        print("TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
        print("="*70 + "\n")
        sys.exit(1)

    # Initialize DB tables
    init_db()

    bot_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
    
    # Test bot credentials
    try:
        me_resp = requests.get(f"{bot_url}/getMe", timeout=10)
        me_resp.raise_for_status()
        bot_info = me_resp.json().get("result", {})
        bot_username = bot_info.get("username")
        bot_name = bot_info.get("first_name")
        print("\n" + "="*70, flush=True)
        print(f"🤖 Connected to Telegram Bot: {bot_name} (@{bot_username})", flush=True)
        print("Listening for messages & voice notes... Press Ctrl+C to stop.", flush=True)
        print("="*70 + "\n", flush=True)
    except Exception as e:
        logger.error(f"Failed to connect to Telegram Bot API: {e}")
        print("Please check your TELEGRAM_BOT_TOKEN in .env.", flush=True)
        sys.exit(1)

    offset = 0

    # Flush pending stale updates on startup so old session messages do not re-trigger
    try:
        flush_resp = requests.get(f"{bot_url}/getUpdates?offset=-1", timeout=10)
        if flush_resp.status_code == 200:
            flush_data = flush_resp.json().get("result", [])
            if flush_data:
                offset = flush_data[-1].get("update_id", 0) + 1
                logger.info(f"Flushed {len(flush_data)} stale updates. Starting from update_id {offset}")
    except Exception as e:
        logger.warning(f"Could not flush updates on startup: {e}")

    while True:
        try:
            url = f"{bot_url}/getUpdates?offset={offset}&timeout=20"
            resp = requests.get(url, timeout=25)
            if resp.status_code != 200:
                time.sleep(2)
                continue

            data = resp.json()
            updates = data.get("result", [])

            for update in updates:
                update_id = update.get("update_id", 0)
                offset = max(offset, update_id + 1)

                message = update.get("message")
                if not message:
                    continue

                chat = message.get("chat", {})
                chat_id = str(chat.get("id"))
                from_user = message.get("from", {})
                first_name = from_user.get("first_name") or "Entrepreneur"

                if "text" in message:
                    text_body = message.get("text", "").strip()
                    print(f"📩 [Text from @{from_user.get('username') or chat_id}]: {text_body}")
                    process_telegram_query(chat_id, text_body, first_name)
                elif "voice" in message:
                    voice = message.get("voice", {})
                    file_id = voice.get("file_id")
                    print(f"🎙️ [Voice note from @{from_user.get('username') or chat_id}]: file_id={file_id}")
                    process_telegram_voice_query(chat_id, file_id, first_name)
                elif "audio" in message:
                    audio = message.get("audio", {})
                    file_id = audio.get("file_id")
                    print(f"🎵 [Audio from @{from_user.get('username') or chat_id}]: file_id={file_id}")
                    process_telegram_voice_query(chat_id, file_id, first_name)

        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.ConnectionError:
            logger.warning("Connection lost. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped Telegram polling.")
            break
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            time.sleep(2)
        finally:
            pass

    if _singleton_socket:
        try:
            _singleton_socket.close()
        except Exception:
            pass

if __name__ == "__main__":
    import traceback
    try:
        poll_telegram_updates()
    except BaseException as e:
        logger.error(f"Fatal unhandled exception in poll_telegram_updates: {e}\n{traceback.format_exc()}")
        raise


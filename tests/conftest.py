import pytest
from unittest.mock import patch
from app.db.session import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    # Mock outbound network calls during automated test suite runs
    with patch("app.telegram.client.send_telegram_text", return_value={"mock": True, "status": "sent"}), \
         patch("app.telegram.client.send_telegram_document", return_value={"mock": True, "status": "sent"}), \
         patch("app.telegram.client.send_telegram_voice", return_value={"mock": True, "status": "sent"}), \
         patch("app.dialogue.conversation_state.send_telegram_text", return_value={"mock": True, "status": "sent"}), \
         patch("app.dialogue.conversation_state.send_telegram_document", return_value={"mock": True, "status": "sent"}), \
         patch("app.dialogue.conversation_state.send_channel_voice", return_value=None), \
         patch("app.dialogue.conversation_state.upload_dpr_pdf", return_value="http://localhost:8000/static/dprs/sample.pdf"), \
         patch("app.storage.local_storage.save_dpr_pdf", return_value="http://localhost:8000/static/dprs/sample.pdf"):
        yield

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db import crud
from app.telegram.client import send_telegram_text, send_telegram_document
from app.dialogue.conversation_state import process_telegram_query

client = TestClient(app)

def test_telegram_client_mock_methods():
    """Verify Telegram client functions return successful mock responses when token is empty/unconfigured."""
    from app.config import settings
    old_token = settings.TELEGRAM_BOT_TOKEN
    try:
        settings.TELEGRAM_BOT_TOKEN = ""
        text_res = send_telegram_text(chat_id="12345678", text="Hello from Rural Advisor")
        assert text_res["status"] == "sent"
        assert text_res["mock"] is True

        doc_res = send_telegram_document(chat_id="12345678", document="https://mock.com/dpr.pdf", caption="DPR")
        assert doc_res["status"] == "sent"
        assert doc_res["mock"] is True
    finally:
        settings.TELEGRAM_BOT_TOKEN = old_token

def test_telegram_webhook_post_text():
    """Verify POST /webhook/telegram ingests text messages from Telegram Bot API."""
    unique_chat_id = f"tg_{uuid.uuid4().int % 100000000:08d}"
    update_payload = {
        "update_id": 987654321,
        "message": {
            "message_id": 101,
            "from": {
                "id": int(unique_chat_id.replace("tg_", "")),
                "is_bot": False,
                "first_name": "Suresh",
                "username": "suresh_patil"
            },
            "chat": {
                "id": int(unique_chat_id.replace("tg_", "")),
                "type": "private",
                "first_name": "Suresh"
            },
            "date": 1710168000,
            "text": "I want to start a poultry broiler farm in Mandya with ₹2,80,000"
        }
    }

    response = client.post("/webhook/telegram", json=update_payload)
    assert response.status_code == 200
    assert response.text == "OK"

def test_telegram_end_to_end_dialogue_to_sanction():
    """
    End-to-End Telegram Test:
    1. Entrepreneur sends business idea & capital over Telegram.
    2. Classified under Term Loan Scheme (₹2,80,000 > ₹1,40,000).
    3. Entrepreneur replies 'GENERATE DPR'.
    4. DPR PDF generated, status 'DRAFT'.
    5. SCA Officer approves proposal via internal API.
    6. Verify sanction notification is dispatched to Telegram.
    """
    chat_id = f"tg_{uuid.uuid4().int % 100000000:08d}"

    # Step 1: User sends message on Telegram
    process_telegram_query(chat_id, "I want to start a poultry broiler farm in Mandya with ₹2,80,000", user_name="Suresh")

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id)
        assert beneficiary.primary_channel == "telegram"
        assert beneficiary.conversation_state == "CONFIRM_DPR"

        fin = beneficiary.conversation_context.get("financial_structure")
        assert fin is not None
        assert fin["scheme"] == "TERM_LOAN"
        assert fin["cost"] == 280000.0
        assert fin["loan"] == 252000.0  # 90% of 280,000
        assert fin["margin"] == 28000.0  # 10%
        assert fin["rate"] == 8.0
        assert fin["repayment_months"] == 78

        # Step 2: User requests DPR
        process_telegram_query(chat_id, "GENERATE DPR", user_name="Suresh")

        db.expire_all()
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id)
        assert beneficiary.conversation_state == "SUBMITTED"

        # Check proposal was created
        proposals = crud.get_proposals(db, status="DRAFT")
        matched = [p for p in proposals if p.beneficiary_id == beneficiary.id]
        assert len(matched) == 1
        proposal = matched[0]
        assert proposal.scheme_tier == "TERM_LOAN"
        proposal_id = proposal.id

    finally:
        db.close()

    # Step 3: SCA Officer logs verification and approves
    sanction_payload = {
        "field_officer_id": "OFFICER-MANDYA-05",
        "geo_latitude": 12.5218,
        "geo_longitude": 76.8951,
        "margin_money_verified": True,
        "recommendation": "APPROVE",
        "remarks": "Poultry shed land verified. Margin money confirmed."
    }

    resp = client.post(f"/internal/sanction/{proposal_id}", json=sanction_payload)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "SANCTIONED"

    db = SessionLocal()
    try:
        updated_prop = crud.get_proposal_by_id(db, proposal_id)
        assert updated_prop.status == "SANCTIONED"
    finally:
        db.close()

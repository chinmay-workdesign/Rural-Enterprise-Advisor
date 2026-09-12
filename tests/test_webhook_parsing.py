import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db.session import SessionLocal
from app.db import crud

client = TestClient(app)

def test_webhook_get_handshake_success():
    """Test Meta webhook verification handshake with correct verify token."""
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "challenge_code_98765"
        }
    )
    assert response.status_code == 200
    assert response.text == "challenge_code_98765"

def test_webhook_get_handshake_failure_invalid_token():
    """Test Meta webhook verification with invalid token returns 403."""
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_code_98765"
        }
    )
    assert response.status_code == 403

def test_webhook_post_text_message_and_idempotency():
    """Test text message ingestion and deduplication of repeated message_id."""
    msg_id = "wamid.HBgMOTExOTk4ODc3NjY1NRUCABEYEjA1RDIzNDU2Nzg5MDEyMzQ1NgA="
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "919988776655", "phone_number_id": "10001"},
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": msg_id,
                                    "timestamp": "1710168000",
                                    "type": "text",
                                    "text": {"body": "I want to start a dairy unit in Belagavi with ₹1,20,000"}
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    # First POST
    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.text == "EVENT_RECEIVED"

    # Verify idempotency DB record
    db = SessionLocal()
    try:
        assert crud.is_webhook_processed(db, msg_id) is True
    finally:
        db.close()

    # Second POST with identical message_id (simulating Meta retry)
    dup_response = client.post("/webhook/whatsapp", json=payload)
    assert dup_response.status_code == 200
    assert dup_response.text == "EVENT_RECEIVED"

def test_signature_verification_rejection():
    """Test rejection when X-Hub-Signature-256 does not match WHATSAPP_APP_SECRET."""
    old_secret = settings.WHATSAPP_APP_SECRET
    try:
        settings.WHATSAPP_APP_SECRET = "test_super_secret"
        payload = b'{"test": "payload"}'
        invalid_sig = "sha256=invalid_hash_value_123456"

        response = client.post(
            "/webhook/whatsapp",
            content=payload,
            headers={"X-Hub-Signature-256": invalid_sig, "Content-Type": "application/json"}
        )
        assert response.status_code == 403
    finally:
        settings.WHATSAPP_APP_SECRET = old_secret

import uuid
import pytest
from app.db.session import SessionLocal
from app.db import crud
from app.dialogue.conversation_state import process_user_query
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_full_dialogue_to_sanction_flow():
    """
    End-to-End Acceptance Criterion:
    1. Beneficiary texts business idea & capital.
    2. Correct MFS classification and deterministic numbers stored.
    3. Beneficiary responds 'GENERATE DPR'.
    4. Enterprise proposal created with status='DRAFT'.
    5. SCA Officer geo-verifies and approves via internal sanction API.
    """
    phone = f"91{uuid.uuid4().int % 10000000000:010d}"

    # Step 1: Initial user query
    user_msg = "I want to start a kirana stall in Belagavi with ₹1,20,000"
    process_user_query(phone, user_msg)

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, phone)
        assert beneficiary.district == "Belagavi"
        assert beneficiary.conversation_state == "CONFIRM_DPR"

        fin = beneficiary.conversation_context.get("financial_structure")
        assert fin is not None
        assert fin["scheme"] == "MICRO_FINANCE"
        assert fin["cost"] == 120000.0
        assert fin["loan"] == 108000.0
        assert fin["margin"] == 12000.0
        assert fin["rate"] == 6.5
        assert fin["repayment_months"] == 33

        # Step 2: Beneficiary triggers DPR generation
        process_user_query(phone, "GENERATE DPR")

        db.expire_all()
        beneficiary = crud.get_or_create_beneficiary(db, phone)
        assert beneficiary.conversation_state == "SUBMITTED"

        # Check proposal was created
        proposals = crud.get_proposals(db, status="DRAFT")
        matched = [p for p in proposals if p.beneficiary_id == beneficiary.id]
        assert len(matched) == 1
        prop = matched[0]
        assert "kirana" in prop.business_trade.lower()
        assert prop.status == "DRAFT"
        assert prop.dpr_pdf_url is not None
        proposal_id = prop.id

    finally:
        db.close()

    # Step 3: SCA Officer logs verification and approves via internal API
    sanction_payload = {
        "field_officer_id": "OFFICER-BELAGAVI-01",
        "geo_latitude": 15.8497,
        "geo_longitude": 74.4977,
        "margin_money_verified": True,
        "recommendation": "APPROVE",
        "remarks": "Shop visited. Margin money verified in Canara Bank account."
    }

    resp = client.post(f"/internal/sanction/{proposal_id}", json=sanction_payload)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "SANCTIONED"

    # Verify status in database
    db = SessionLocal()
    try:
        updated_prop = crud.get_proposal_by_id(db, proposal_id)
        assert updated_prop.status == "SANCTIONED"
        assert len(updated_prop.verifications) == 1
        verif = updated_prop.verifications[0]
        assert verif.field_officer_id == "OFFICER-BELAGAVI-01"
        assert verif.margin_money_verified is True
        assert verif.recommendation == "APPROVE"
    finally:
        db.close()

def test_language_detection_and_matching():
    """Verify that language detection accurately detects Kannada, Hindi, and English."""
    from app.dialogue.conversation_state import detect_message_language, _generate_clarification_question

    # 1. Kannada detection
    assert detect_message_language("ನಾನು ಬೆಳಗಾವಿಯಲ್ಲಿ ಬೇಕರಿ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ") == "kannada"
    assert detect_message_language("In kannada please") == "kannada"

    # 2. Hindi detection
    assert detect_message_language("मुझे बेलगावी में किराना दुकान शुरू करनी है") == "hindi"
    assert detect_message_language("In hindi please") == "hindi"

    # 3. Telugu detection
    assert detect_message_language("నేను కిరాణా దుకాణం ప్రారంభించాలనుకుంటున్నాను") == "telugu"

    # 4. English detection
    assert detect_message_language("In english please") == "english"

    # 5. Clarification questions in appropriate languages
    kn_q = _generate_clarification_question(["trade", "district", "project_cost"], None, None, "kannada")
    assert "ನಮಸ್ಕಾರ" in kn_q
    assert "ಕಿರಾಣಿ ಅಂಗಡಿ" in kn_q

    hi_q = _generate_clarification_question(["trade", "district", "project_cost"], None, None, "hindi")
    assert "नमस्ते" in hi_q
    assert "किराना दुकान" in hi_q

    en_q = _generate_clarification_question(["trade", "district", "project_cost"], None, None, "english")
    assert "Namaste" in en_q
    assert "Kirana store" in en_q


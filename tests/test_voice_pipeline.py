import pytest
from app.voice.voice_service import transcribe_audio, synthesize_speech, get_language_code
from app.dialogue.conversation_state import process_voice_query
from app.db.session import SessionLocal
from app.db import crud

def test_language_code_mapping():
    assert get_language_code("kannada") == "kn"
    assert get_language_code("hindi") == "hi"
    assert get_language_code("tamil") == "ta"
    assert get_language_code("telugu") == "te"
    assert get_language_code("english") == "en"

def test_voice_stt_transcription():
    mock_audio = b"MOCK_OPUS_AUDIO_BYTES_HEADER"
    transcript = transcribe_audio(mock_audio, source_language="kannada")
    assert transcript is not None
    assert len(transcript) > 5

def test_voice_tts_synthesis():
    text = "ನಿಮ್ಮ ಕಿರು-ಉದ್ಯಮ ಸಾಲ ಮಂಜೂರಾಗಿದೆ"
    audio_bytes = synthesize_speech(text, target_language="kannada")
    assert audio_bytes is not None
    assert len(audio_bytes) > 10

def test_voice_query_end_to_end():
    phone = "919876543299"
    media_id = "media_voice_note_12345"

    process_voice_query(phone, media_id)

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, phone)
        assert beneficiary.conversation_state in ["CONFIRM_DPR", "ADVISING"]
        assert beneficiary.conversation_context.get("financial_structure") is not None
    finally:
        db.close()

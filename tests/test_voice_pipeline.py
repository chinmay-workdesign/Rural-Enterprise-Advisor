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
    assert get_language_code("marathi") == "mr"
    assert get_language_code("english") == "en"

def test_voice_stt_transcription():
    mock_audio = b"MOCK_OPUS_AUDIO_BYTES_HEADER"
    transcript_kn = transcribe_audio(mock_audio, source_language="kannada")
    assert transcript_kn is not None
    assert len(transcript_kn) > 5

    transcript_te = transcribe_audio(mock_audio, source_language="telugu")
    assert "గుంటూరు" in transcript_te

    transcript_mr = transcribe_audio(mock_audio, source_language="marathi")
    assert "पुण्यात" in transcript_mr

def test_voice_tts_synthesis():
    text_kn = "ನಿಮ್ಮ ಕಿರು-ಉದ್ಯಮ ಸಾಲ ಮಂಜೂರಾಗಿದೆ"
    audio_kn = synthesize_speech(text_kn, target_language="kannada")
    assert audio_kn is not None
    assert len(audio_kn) > 10

    text_te = "మీ సూక్ష్మ వ్యాపార రుణం మంజూరైంది"
    audio_te = synthesize_speech(text_te, target_language="telugu")
    assert audio_te is not None
    assert len(audio_te) > 10

    text_mr = "आपले सूक्ष्म उद्योग कर्ज मंजूर झाले आहे"
    audio_mr = synthesize_speech(text_mr, target_language="marathi")
    assert audio_mr is not None
    assert len(audio_mr) > 10

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

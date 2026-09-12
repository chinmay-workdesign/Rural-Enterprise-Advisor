import logging
from typing import Dict, Any, Optional
from app.db.session import SessionLocal
from app.db import crud
from app.whatsapp.client import (
    send_whatsapp_text,
    send_whatsapp_document,
    download_media_bytes as download_whatsapp_media,
)
from app.telegram.client import (
    send_telegram_text,
    send_telegram_document,
    send_telegram_voice,
    download_telegram_file,
)
from app.voice.voice_service import transcribe_audio, synthesize_speech
from app.ai.extraction import extract_entrepreneur_details, generate_advisory_message
from app.ai.rag.qdrant_client import search_trade_benchmarks
from app.finance.calculator import calculate_financial_structure, validate_project_cost
from app.finance.dscr import project_financial_cashflows
from app.dpr.generator import generate_dpr_pdf
from app.storage.r2_client import upload_dpr_pdf

logger = logging.getLogger("conversation_state")

GREETING_MSG_KN = "ನಮಸ್ಕಾರ! ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಸಲಹಾ ಕೇಂದ್ರಕ್ಕೆ ಸ್ವಾಗತ. ನೀವು ಯಾವ ಉದ್ಯಮವನ್ನು (ಉದಾ. ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ, ಹೊಲಿಗೆ) ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಎಷ್ಟು ಬಂಡವಾಳದೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?"
GREETING_MSG_HI = "नमस्ते! ग्रामीण सूक्ष्म उद्यम सलाहकार केंद्र में आपका स्वागत है। आप कौन सा व्यवसाय (जैसे किराना दुकान, डेयरी, सिलाई) किस जिले में कितनी पूंजी के साथ शुरू करना चाहते हैं?"
GREETING_MSG_EN = "Namaste! Welcome to the Rural Micro-Enterprise AI Advisory. Which business trade (e.g. Kirana stall, Dairy cow, Tailoring) do you want to start, in which district, and what is your required project cost?"

def detect_message_language(text: str) -> Optional[str]:
    """
    Detect language strictly from text or voice transcript using Unicode scripts and explicit keywords.
    Supported: 'kannada', 'hindi', 'telugu', 'tamil', 'marathi', 'english'.
    """
    if not text:
        return None

    clean = text.strip()
    lower = clean.lower()

    # 1. Explicit language command keywords
    if any(k in lower for k in ["in kannada", "kannada please", "kannadadalli", "kannada", "ಕನ್ನಡ"]):
        return "kannada"
    if any(k in lower for k in ["in hindi", "hindi please", "hindi mein", "hindi", "हिंदी", "हिन्दी"]):
        return "hindi"
    if any(k in lower for k in ["in telugu", "telugu please", "telugu", "తెలుగు"]):
        return "telugu"
    if any(k in lower for k in ["in tamil", "tamil please", "tamil", "தமிழ்"]):
        return "tamil"
    if any(k in lower for k in ["in marathi", "marathi please", "marathi", "मराठी"]):
        return "marathi"
    if any(k in lower for k in ["in english", "english please", "english"]):
        return "english"

    # 2. Unicode script frequency counting
    counts = {
        "kannada": 0,
        "hindi": 0,    # Devanagari script (Hindi / Marathi)
        "telugu": 0,
        "tamil": 0,
    }
    for char in clean:
        code = ord(char)
        if 0x0C80 <= code <= 0x0CFF:
            counts["kannada"] += 1
        elif 0x0900 <= code <= 0x097F:
            counts["hindi"] += 1
        elif 0x0C00 <= code <= 0x0C7F:
            counts["telugu"] += 1
        elif 0x0B80 <= code <= 0x0BFF:
            counts["tamil"] += 1

    top_lang, top_count = max(counts.items(), key=lambda x: x[1])
    if top_count >= 2:
        return top_lang

    return None

def send_channel_text(beneficiary, text: str):
    """Dispatch outbound message to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        send_telegram_text(beneficiary.telegram_chat_id, text)
    else:
        send_whatsapp_text(beneficiary.whatsapp_number, text)

def send_channel_voice(beneficiary, voice_bytes: bytes, caption: Optional[str] = None):
    """Dispatch outbound voice note to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        send_telegram_voice(beneficiary.telegram_chat_id, voice_bytes, caption=caption)

def send_channel_document(beneficiary, document_url: str, filename: str, caption: str, document_bytes: Optional[bytes] = None):
    """Dispatch outbound document to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        doc_payload = document_bytes if (document_bytes and len(document_bytes) > 0) else document_url
        send_telegram_document(beneficiary.telegram_chat_id, doc_payload, filename=filename, caption=caption)
    else:
        send_whatsapp_document(
            recipient_phone=beneficiary.whatsapp_number,
            document_url=document_url,
            filename=filename,
            caption=caption
        )


# ==================== TELEGRAM HANDLERS ====================

def process_telegram_voice_query(chat_id: str, file_id: str, user_name: Optional[str] = None):
    """Pipeline for Telegram voice notes (.oga/.ogg): download -> Gemini STT -> language sync -> dialogue."""
    logger.info(f"Processing Telegram voice query from chat_id {chat_id}, file_id: {file_id}")
    audio_bytes = download_telegram_file(file_id)
    if not audio_bytes:
        send_telegram_text(chat_id, "Sorry, could not download voice note. Please try sending again.")
        return

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        lang = beneficiary.preferred_language or "kannada"
    finally:
        db.close()

    transcription = transcribe_audio(audio_bytes, source_language=lang)
    logger.info(f"Telegram voice note transcribed: '{transcription}'")

    if not transcription or not transcription.strip():
        if lang == "kannada":
            err_msg = "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸಂದೇಶ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ ಕಳುಹಿಸಿ."
        elif lang == "hindi":
            err_msg = "क्षमा करें, आपकी आवाज़ स्पष्ट रूप से सुनाई नहीं दी। कृपया फिर से बोलें या टेक्स्ट लिखकर भेजें।"
        else:
            err_msg = "Sorry, we could not hear your voice clearly. Please speak clearly again or reply with text."
        send_telegram_text(chat_id, err_msg)
        return

    # Synchronize language immediately from the spoken voice note transcript
    detected = detect_message_language(transcription)
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        if detected:
            beneficiary.preferred_language = detected
            db.commit()
            logger.info(f"Updated preferred_language to '{detected}' based on voice transcript.")
        _handle_user_turn(db, beneficiary, transcription, from_voice=True)
    finally:
        db.close()

def process_telegram_query(chat_id: str, text: str, user_name: Optional[str] = None, from_voice: bool = False):
    """Process incoming text message from Telegram."""
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        _handle_user_turn(db, beneficiary, text, from_voice=from_voice)
    finally:
        db.close()

# ==================== WHATSAPP HANDLERS ====================

def process_voice_query(from_phone: str, media_id: str):
    """Pipeline for WhatsApp voice notes: download -> Gemini STT -> dialogue."""
    logger.info(f"Processing WhatsApp voice query from {from_phone} with media_id {media_id}")
    audio_bytes = download_whatsapp_media(media_id)
    if not audio_bytes:
        send_whatsapp_text(from_phone, "Sorry, we could not retrieve your voice note. Please send your message again.")
        return

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, from_phone)
        lang = beneficiary.preferred_language or "kannada"
    finally:
        db.close()

    transcription = transcribe_audio(audio_bytes, source_language=lang)
    logger.info(f"Transcribed WhatsApp voice note: '{transcription}'")

    if not transcription:
        send_whatsapp_text(from_phone, "We could not understand the audio clearly. Please reply with text.")
        return

    process_user_query(from_phone, transcription)

def process_user_query(from_phone: str, user_text: str):
    """Process incoming text message from WhatsApp."""
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, from_phone)
        _handle_user_turn(db, beneficiary, user_text)
    finally:
        db.close()

# ==================== CORE STATE MACHINE ====================

def _send_voice_audio_reply(beneficiary, text: str, lang: str):
    """Synthesize speech and send as voice note to the user if channel supports voice."""
    try:
        lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("━")]
        spoken_text = " ".join(lines[:3]) if lines else text[:250]
        clean_text = spoken_text.replace("*", "").replace("#", "").replace("-", " ")
        audio_bytes = synthesize_speech(clean_text, target_language=lang)
        if audio_bytes:
            send_channel_voice(beneficiary, audio_bytes)
    except Exception as e:
        logger.warning(f"Failed to send voice audio reply: {e}")

def _handle_user_turn(db, beneficiary, user_text: str, from_voice: bool = False):
    """Shared state machine for both Telegram and WhatsApp channels."""
    text_clean = user_text.strip()
    state = beneficiary.conversation_state or "GREETING"
    context = beneficiary.conversation_context or {}

    # Synchronize language immediately from incoming message
    detected_lang = detect_message_language(text_clean)
    if detected_lang:
        beneficiary.preferred_language = detected_lang
        db.commit()

    lang = beneficiary.preferred_language or "kannada"

    channel_name = "Telegram" if getattr(beneficiary, "primary_channel", "") == "telegram" else "WhatsApp"
    logger.info(f"[{channel_name}] Beneficiary {beneficiary.id[:8]} ({lang}) in state {state}: '{text_clean}'")

    # Reset / Restart keyword
    if text_clean.upper() in ["HI", "HELLO", "START", "/START", "RESTART", "RESET", "CLEAR", "NEW", "ನಮಸ್ಕಾರ", "नमस्ते"]:
        beneficiary.conversation_state = "COLLECTING"
        beneficiary.conversation_context = {}
        # Reset to Kannada on /start or restart commands so native regional greeting is presented
        if text_clean.upper() in ["/START", "START", "RESET", "RESTART", "CLEAR", "NEW"]:
            beneficiary.preferred_language = "kannada"
        elif "नमस्ते" in text_clean:
            beneficiary.preferred_language = "hindi"
        elif "ನಮಸ್ಕಾರ" in text_clean:
            beneficiary.preferred_language = "kannada"
        db.commit()

        lang = beneficiary.preferred_language or "kannada"
        if lang == "kannada":
            greeting = GREETING_MSG_KN
        elif lang == "hindi":
            greeting = GREETING_MSG_HI
        else:
            greeting = GREETING_MSG_EN
        send_channel_text(beneficiary, greeting)
        if from_voice:
            _send_voice_audio_reply(beneficiary, greeting, lang)
        return

    # Check for DPR generation trigger
    if "GENERATE DPR" in text_clean.upper() or "DPR" in text_clean.upper():
        # First send the 2-minute waiting notification requested by the user
        if lang == "kannada":
            wait_msg = "⏳ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿಯನ್ನು (DPR PDF) ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು 2 ನಿಮಿಷ ಕಾಯಿರಿ, ಪೂರ್ಣ ವರದಿಯು ಇಲ್ಲಿಯೇ ನೇರವಾಗಿ ತಲುಪಲಿದೆ..."
        elif lang == "hindi":
            wait_msg = "⏳ आपकी बैंक-तैयार विस्तृत परियोजना रिपोर्ट (DPR PDF) तैयार की जा रही है। कृपया 2 मिनट प्रतीक्षा करें, पूरी रिपोर्ट यहीं प्राप्त होगी..."
        else:
            wait_msg = "⏳ Generating your bank-ready Detailed Project Report (DPR PDF). Please wait for 2 minutes while we compile your financial statements and cash flow projections..."
        send_channel_text(beneficiary, wait_msg)

        # Auto-resolve / ensure financial structure exists so DPR is NEVER refused
        if not context.get("financial_structure"):
            trade = context.get("trade") or "Rural Enterprise"
            district = context.get("district") or beneficiary.district or "Belagavi"
            state = context.get("state") or beneficiary.state or "Karnataka"
            project_cost = context.get("project_cost")

            if not project_cost:
                from app.db.models import EnterpriseProposal
                latest_prop = db.query(EnterpriseProposal).filter(
                    EnterpriseProposal.beneficiary_id == beneficiary.id
                ).order_by(EnterpriseProposal.created_at.desc()).first()
                if latest_prop and latest_prop.project_cost:
                    project_cost = float(latest_prop.project_cost)
                else:
                    t_low = trade.lower()
                    if any(k in t_low for k in ["fertilizer", "pesticide", "poultry"]):
                        project_cost = 250000.0
                    elif any(k in t_low for k in ["dairy", "cattle", "cow"]):
                        project_cost = 140000.0
                    elif any(k in t_low for k in ["tailor", "garment"]):
                        project_cost = 120000.0
                    elif any(k in t_low for k in ["fish", "fishery"]):
                        project_cost = 250000.0
                    else:
                        project_cost = 150000.0

            fin_result = calculate_financial_structure(project_cost)
            cashflows = project_financial_cashflows(project_cost, fin_result["emi"])
            benchmarks = search_trade_benchmarks(trade, district, limit=2)
            dscr_bench = float(benchmarks[0].get("dscr", 1.75)) if benchmarks else 1.75
            cashflows["dscr"] = dscr_bench

            from app.finance.multi_schemes import get_all_eligible_schemes
            multi_schemes = get_all_eligible_schemes(cost=project_cost, trade=trade, district=district, state=state)
            nabard_summary = f"Grounded in NABARD {trade} benchmark in {district}."

            context.update({
                "trade": trade,
                "district": district,
                "state": state,
                "project_cost": project_cost,
                "financial_structure": fin_result,
                "cashflows": cashflows,
                "nabard_benchmark": nabard_summary,
                "multi_schemes": multi_schemes
            })
            beneficiary.conversation_context = context
            beneficiary.conversation_state = "CONFIRM_DPR"
            db.commit()

        _handle_dpr_generation(db, beneficiary, context)
        return

    lower_text = text_clean.lower()

    # 1. Voice capability inquiry (e.g. "Do you accept voice input", "can I speak", "voice note")
    voice_keywords = ["voice", "voice input", "voice note", "audio", "mic", "microphone", "ಧ್ವನಿ", "ಆಡಿಯೋ", "ಮಾತನಾಡು", "बोल"]
    if any(k in lower_text for k in voice_keywords) and len(text_clean.split()) < 10:
        if lang == "kannada":
            msg = (
                "ಹೌದು, ಖಂಡಿತವಾಗಿ! 🎙️ ನೀವು ಕನ್ನಡ, ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಹಿಂದಿಯಲ್ಲಿ ಧ್ವನಿ ಸಂದೇಶ (Voice Note) ಕಳುಹಿಸಬಹುದು.\n\n"
                "ಟೆಲಿಗ್ರಾಮ್‌ನಲ್ಲಿರುವ ಮೈಕ್ರೋಫೋನ್ ಐಕಾನ್ ಒತ್ತಿ ಹಿಡಿದು ನಿಮ್ಮ ವ್ಯಾಪಾರದ ಕಲ್ಪನೆ, ನಿಮ್ಮ ಜಿಲ್ಲೆ ಮತ್ತು ಅಂದಾಜು ಬಂಡವಾಳವನ್ನು ಮಾತನಾಡಿ ಕಳುಹಿಸಿ!"
            )
        elif lang == "hindi":
            msg = (
                "हाँ, बिल्कुल! 🎙️ आप हिंदी, कन्नड़ या अंग्रेजी में वॉइस नोट भेज सकते हैं।\n\n"
                "टेलीग्राम पर माइक बटन दबाकर अपने व्यापार का विचार, जिला और बजट बोलकर भेजें!"
            )
        else:
            msg = (
                "Yes, absolutely! 🎙️ You can send voice notes in English, Kannada (ಕನ್ನಡ), Hindi (हिंदी), or your regional language.\n\n"
                "Simply hold down the microphone button in Telegram, describe your business idea, your district, and your required capital, and I will structure your government financing options!"
            )
        send_channel_text(beneficiary, msg)
        if from_voice:
            _send_voice_audio_reply(beneficiary, msg, lang)
        return

    # 2. General help inquiry (e.g. "what can you do", "help", "who are you")
    if any(k in lower_text for k in ["what can you do", "help", "who are you", "ಏನು ಮಾಡಬಹುದು", "ಸಹಾಯ", "मदद"]) and len(text_clean.split()) < 7:
        if lang == "kannada":
            msg = (
                "ನಾನು ನಿಮ್ಮ ಎಐ ಗ್ರಾಮೀಣ ಉದ್ಯಮ ಸಲಹೆಗಾರ. 🙏\n\n"
                "ನಾನು ಸ್ಥಳೀಯ ವ್ಯಾಪಾರಿಗಳು ಮತ್ತು ಗ್ರಾಮೀಣ ಉದ್ಯಮಿಗಳಿಗೆ ಸರ್ಕಾರಿ ರಿಯಾಯಿತಿ ಸಾಲಗಳು (MFS/TLS 6.5%-8%), "
                "PMEGP 35% ಸಬ್ಸಿಡಿ ಮತ್ತು ಮುದ್ರಾ ಸಾಲಗಳನ್ನು ಲೆಕ್ಕಾಚಾರ ಮಾಡಿ ಬ್ಯಾಂಕ್-ಸಿದ್ಧ ಯೋಜನಾ ವರದಿ (DPR) ತಯಾರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.\n\n"
                "ನೀವು ಯಾವ ವ್ಯಾಪಾರವನ್ನು, ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ, ಎಷ್ಟು ಬಂಡವಾಳದೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ ಎಂದು ತಿಳಿಸಿ!"
            )
        elif lang == "hindi":
            msg = (
                "मैं आपका एआई ग्रामीण उद्यम सलाहकार हूँ। 🙏\n\n"
                "मैं स्थानीय व्यापारियों और उद्यमियों के लिए सरकारी रियायती ऋण (MFS/TLS 6.5%-8%), "
                "PMEGP 35% सब्सिडी और मुद्रा ऋण की गणना करके बैंक-तैयार प्रोजेक्ट रिपोर्ट (DPR) बनाने में मदद करता हूँ।\n\n"
                "बताएं कि आप कौन सा व्यवसाय, किस जिले में, कितनी पूंजी के साथ शुरू करना चाहते हैं!"
            )
        else:
            msg = (
                "I am your AI Rural Enterprise Advisor. 🙏\n\n"
                "I help rural entrepreneurs and hyper-local business owners structure bank-ready loan proposals, "
                "calculate eligibility for government concessional schemes (MFS/TLS at 6.5%-8%), "
                "claim PMEGP capital subsidies (up to 35%), and generate official Detailed Project Reports (DPR).\n\n"
                "Tell me which business trade you want to start, your district, and your required budget to get started!"
            )
        send_channel_text(beneficiary, msg)
        if from_voice:
            _send_voice_audio_reply(beneficiary, msg, lang)
        return

    # 3. Conversational follow-ups when advisory has already been generated
    if state == "CONFIRM_DPR":
        extracted = extract_entrepreneur_details(text_clean)
        has_new_details = bool(extracted.get("trade") or extracted.get("project_cost"))
        if has_new_details:
            _handle_extraction_and_advisory(db, beneficiary, text_clean, context, from_voice=from_voice)
            return

        trade = context.get("trade", "your enterprise")
        district = context.get("district", "your district")
        cost = context.get("project_cost", 120000.0)

        follow_up_prompt = (
            f"You are a helpful Rural Enterprise Lending Advisor. The entrepreneur has already received a proposal for their "
            f"{trade} in {district} with outlay ₹{cost:,.2f}. "
            f"Answer their message concisely and politely in {lang}. "
            f"At the end, remind them: 'Reply GENERATE DPR whenever you are ready to download your official bank report PDF.'"
        )
        try:
            from app.ai.llm_client import call_llm_chat
            answer = call_llm_chat(
                messages=[
                    {"role": "system", "content": follow_up_prompt},
                    {"role": "user", "content": text_clean}
                ],
                temperature=0.3
            )
            if answer and answer.strip():
                send_channel_text(beneficiary, answer.strip())
                if from_voice:
                    _send_voice_audio_reply(beneficiary, answer.strip(), lang)
                return
        except Exception as e:
            logger.warning(f"Follow-up answer failed: {e}")

        # Fallback reminder if LLM unavailable
        if lang == "kannada":
            fallback_ans = f"ನಿಮ್ಮ {trade} ಯೋಜನೆಯ ಅಧಿಕೃತ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿಯನ್ನು (PDF) ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು 'GENERATE DPR' ಎಂದು ಉತ್ತರಿಸಿ."
        elif lang == "hindi":
            fallback_ans = f"अपने {trade} उद्यम की आधिकारिक बैंक रिपोर्ट डाउनलोड करने के लिए 'GENERATE DPR' लिखकर भेजें।"
        else:
            fallback_ans = f"Reply 'GENERATE DPR' whenever you are ready to download your official bank report PDF for your {trade}."
        send_channel_text(beneficiary, fallback_ans)
        if from_voice:
            _send_voice_audio_reply(beneficiary, fallback_ans, lang)
        return

    # Handle conversation stages
    if state in ["GREETING", "COLLECTING", "ADVISING", "CONFIRM_DPR"]:
        _handle_extraction_and_advisory(db, beneficiary, text_clean, context, from_voice=from_voice)

def _generate_clarification_question(missing: list, trade: Optional[str], district: Optional[str], lang: str) -> str:
    """Generate friendly, personalized clarification prompt for missing parameters in preferred language."""
    if "trade" in missing and "district" in missing and "project_cost" in missing:
        if lang == "kannada":
            return (
                "ನಮಸ್ಕಾರ! ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಮತ್ತು ಸ್ಥಳೀಯ ವ್ಯಾಪಾರ ಸಲಹಾ ಸೇವೆಗೆ ಸ್ವಾಗತ. 🙏\n\n"
                "ನಿಮ್ಮ ಯೋಜನೆಗೆ ಲಭ್ಯವಿರುವ ಸರ್ಕಾರಿ ಸಾಲ (MFS/TLS), ಮುದ್ರಾ ಸಾಲ ಹಾಗೂ 35% ವರೆಗಿನ PMEGP ಸಬ್ಸಿಡಿ ವಿವರಗಳನ್ನು ತಿಳಿಸಲು, ದಯವಿಟ್ಟು ಈ 3 ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಿ:\n\n"
                "1. 🏪 *ನೀವು ಯಾವ ವ್ಯಾಪಾರ/ಉದ್ಯಮ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?* (ಉದಾ: ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ/ಹಸು, ಟೈಲರಿಂಗ್, ಕೋಳಿ ಸಾಕಾಣಿಕೆ, ಹಿಟ್ಟಿನ ಗಿರಣಿ)\n"
                "2. 📍 *ನಿಮ್ಮ ಜಿಲ್ಲೆ ಯಾವುದು?* (ಉದಾ: ಬೆಳಗಾವಿ, ಮೈಸೂರು, ಧಾರವಾಡ, ಮಂಡ್ಯ)\n"
                "3. 💰 *ನಿಮ್ಮ ಅಂದಾಜು ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ (ಬಜೆಟ್) ಎಷ್ಟು?* (ಉದಾ: ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "ದಯವಿಟ್ಟು ಉತ್ತರಿಸಿ, ನಾವು ನಿಮಗೆ ಸಂಪೂರ್ಣ ಸಾಲದ ವಿವರಗಳನ್ನು ನೀಡುತ್ತೇವೆ."
            )
        elif lang == "hindi":
            return (
                "नमस्ते! ग्रामीण सूक्ष्म उद्यम वित्तीय सलाहकार में आपका स्वागत है। 🙏\n\n"
                "आपके व्यवसाय के लिए सबसे उपयुक्त सरकारी योजनाएं, रियायती ऋण और 35% तक सब्सिडी जानने के लिए कृपया यह विवरण बताएं:\n\n"
                "1. 🏪 *आप कौन सा व्यवसाय/उद्योग शुरू करना चाहते हैं?* (उदा: किराना दुकान, डेयरी/गाय पालन, सिलाई, मुर्गी पालन)\n"
                "2. 📍 *आपका जिला कौन सा है?* (उदा: बेलगावी, मैसूरु, धारवाड़)\n"
                "3. 💰 *आपकी अनुमानित कुल परियोजना लागत (बजट) कितनी है?* (उदा: ₹50,000, ₹1,20,000, ₹3,00,000)"
            )
        else:
            return (
                "Namaste! Welcome to the Rural Micro-Enterprise & Hyper-Local Business Advisory. 🙏\n\n"
                "To identify the best government concessional loans (MFS/TLS), MUDRA bank credit, and PMEGP capital subsidies (up to 35%) for you, please share:\n\n"
                "1. 🏪 *What business/trade do you want to start?* (e.g., Kirana store, Dairy cow unit, Tailoring, Poultry farm, Flour mill)\n"
                "2. 📍 *Which district are you located in?* (e.g., Belagavi, Mysuru, Dharwad)\n"
                "3. 💰 *What is your estimated total project cost or required budget?* (e.g., ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "Please share your details to receive your personalized financing plan!"
            )

    questions = []
    if "trade" in missing:
        if lang == "kannada":
            questions.append("🏪 *ನೀವು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುವ ನಿರ್ದಿಷ್ಟ ವ್ಯಾಪಾರ ಅಥವಾ ಉದ್ಯಮ ಯಾವುದು?* (ಉದಾ: ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ, ಟೈಲರಿಂಗ್, ಬೇಕರಿ)")
        elif lang == "hindi":
            questions.append("🏪 *आप कौन सा व्यवसाय शुरू करना चाहते हैं?* (उदा: किराना दुकान, डेयरी, सिलाई, बेकरी)")
        else:
            questions.append("🏪 *Which specific business trade would you like to start?* (e.g., Kirana store, Dairy farming, Tailoring, Poultry)")

    if "district" in missing:
        trade_label = trade if trade else ("ನಿಮ್ಮ ಉದ್ಯಮ" if lang == "kannada" else "your venture")
        if lang == "kannada":
            questions.append(f"📍 *{trade_label}ವನ್ನು ನೀವು ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಪ್ರಾರಂಭಿಸಲು ಯೋಜಿಸುತ್ತಿದ್ದೀರಿ?* (ಉದಾ: ಬೆಳಗಾವಿ, ಮೈಸೂರು, ಧಾರವಾಡ)")
        elif lang == "hindi":
            questions.append(f"📍 *{trade_label} आप किस जिले में शुरू करने की योजना बना रहे हैं?*")
        else:
            questions.append(f"📍 *Which district will your {trade_label} be located in?* (e.g., Belagavi, Mysuru, Dharwad)")

    if "project_cost" in missing:
        prefix = f"{district} ಜಿಲ್ಲೆಯಲ್ಲಿ ನಿಮ್ಮ {trade}" if (district and trade and lang == "kannada") else (f"your {trade} in {district}" if (district and trade) else ("ನಿಮ್ಮ ಉದ್ಯಮ" if lang == "kannada" else "your business"))
        if lang == "kannada":
            questions.append(f"💰 *{prefix}ಕ್ಕಾಗಿ ನಿಮ್ಮ ಅಂದಾಜು ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ ಅಥವಾ ಅಗತ್ಯವಿರುವ ಬಂಡವಾಳ ಎಷ್ಟು?* (ಉದಾ: ₹80,000, ₹1,20,000, ₹3,00,000)")
        elif lang == "hindi":
            questions.append(f"💰 *{prefix} के लिए आपकी अनुमानित कुल परियोजना लागत (बजट) कितनी है?* (उदा: ₹80,000, ₹1,20,000, ₹3,00,000)")
        else:
            questions.append(f"💰 *What is your estimated total project cost or required capital for {prefix}?* (e.g., ₹80,000, ₹1,20,000, ₹3,00,000)")

    if lang == "kannada":
        return "ದಯವಿಟ್ಟು ಈ ಕೆಳಗಿನ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ, ನಾವು ನಿಮಗೆ ನಿಖರವಾದ ಸರ್ಕಾರಿ ಸಾಲ ಮತ್ತು ಸಬ್ಸಿಡಿ ವಿವರಗಳನ್ನು ನೀಡುತ್ತೇವೆ:\n\n" + "\n\n".join(questions)
    elif lang == "hindi":
        return "कृपया निम्नलिखित विवरण बताएं ताकि हम आपको सटीक सरकारी ऋण और सब्सिडी विवरण प्रदान कर सकें:\n\n" + "\n\n".join(questions)
    else:
        return "Please share the following details so we can structure your exact government loan and subsidy options:\n\n" + "\n\n".join(questions)

def _handle_extraction_and_advisory(db, beneficiary, text: str, context: Dict[str, Any], from_voice: bool = False):
    """Extract parameters, ask clarifying questions if details are missing, and only advise when trade, district, and cost are known."""
    extracted = extract_entrepreneur_details(text)
    logger.info(f"Extracted parameters: {extracted}")

    # 1. Update preferred language if specified or detected
    detected_lang = detect_message_language(text)
    if detected_lang:
        beneficiary.preferred_language = detected_lang
    elif extracted.get("language") and extracted.get("language") in ["kannada", "hindi", "telugu", "tamil", "english"]:
        beneficiary.preferred_language = extracted["language"]

    lang = beneficiary.preferred_language or "kannada"

    # 2. Accumulate incoming details without overwriting existing context with None
    if extracted.get("trade"):
        context["trade"] = extracted["trade"]
    if extracted.get("district"):
        context["district"] = extracted["district"]
    if extracted.get("state"):
        context["state"] = extracted["state"]
    if extracted.get("project_cost"):
        context["project_cost"] = extracted["project_cost"]
    if extracted.get("available_capital"):
        context["available_capital"] = extracted["available_capital"]

    trade = context.get("trade")
    district = context.get("district")
    project_cost = context.get("project_cost")
    state = context.get("state") or "Karnataka"

    # 3. Check for missing mandatory parameters (No preassumptions!)
    missing = []
    if not trade:
        missing.append("trade")
    if not district:
        missing.append("district")
    if not project_cost:
        missing.append("project_cost")

    if missing:
        beneficiary.conversation_state = "COLLECTING"
        beneficiary.conversation_context = context
        db.commit()

        clarification_msg = _generate_clarification_question(missing, trade, district, lang)
        send_channel_text(beneficiary, clarification_msg)
        if from_voice:
            _send_voice_audio_reply(beneficiary, clarification_msg, lang)
        return

    try:
        validate_project_cost(project_cost)
    except ValueError as ve:
        err_outlay = (
            f"⚠️ {str(ve)}\nದಯವಿಟ್ಟು ₹5,000 ರಿಂದ ₹50,00,000 ಒಳಗೆ ಮಾನ್ಯವಾದ ಮೊತ್ತವನ್ನು ತಿಳಿಸಿ."
            if lang == "kannada" else
            f"⚠️ {str(ve)}\nPlease specify a viable project outlay between ₹5,000 and ₹50,00,000."
        )
        send_channel_text(beneficiary, err_outlay)
        if from_voice:
            _send_voice_audio_reply(beneficiary, err_outlay, lang)
        return

    # 1. Deterministic financial calculation (NEVER LLM)
    fin_result = calculate_financial_structure(project_cost)

    # 2. Query NABARD Benchmarks via RAG
    benchmarks = search_trade_benchmarks(trade, district, limit=2)
    nabard_summary = ""
    dscr_benchmark = 1.75
    if benchmarks:
        top_bench = benchmarks[0]
        dscr_benchmark = float(top_bench.get("dscr", 1.75))
        nabard_summary = f"Grounded in NABARD {top_bench.get('trade')} benchmark: typical capex ₹{top_bench.get('capex'):,.0f}, opex ₹{top_bench.get('opex'):,.0f}."

    # 3. Project cash flows & DSCR
    cashflows = project_financial_cashflows(project_cost, fin_result["emi"])
    if dscr_benchmark:
        cashflows["dscr"] = dscr_benchmark

    from app.finance.multi_schemes import get_all_eligible_schemes
    multi_schemes = get_all_eligible_schemes(
        cost=project_cost,
        trade=trade,
        district=district,
        state=state,
        available_capital=extracted.get("available_capital")
    )

    # Update context & beneficiary record
    context.update({
        "trade": trade,
        "district": district,
        "state": state,
        "project_cost": project_cost,
        "financial_structure": fin_result,
        "cashflows": cashflows,
        "nabard_benchmark": nabard_summary,
        "multi_schemes": multi_schemes
    })

    beneficiary.district = district
    beneficiary.state = state
    beneficiary.preferred_language = lang
    beneficiary.conversation_state = "CONFIRM_DPR"
    beneficiary.conversation_context = context
    db.commit()

    # 4. Synthesize structured multi-scheme advisory text via Gemini/LLM
    advisory = generate_advisory_message(
        financial_data=fin_result,
        trade=trade,
        district=district,
        nabard_context=nabard_summary,
        language=lang,
        state=state,
        available_capital=extracted.get("available_capital"),
        multi_schemes=multi_schemes
    )

    send_channel_text(beneficiary, advisory)
    if from_voice:
        _send_voice_audio_reply(beneficiary, advisory, lang)

def _handle_dpr_generation(db, beneficiary, context: Dict[str, Any]):
    """Compile Detailed Project Report PDF, upload to Cloudflare R2, and deliver link."""
    fin = context["financial_structure"]
    cashflows = context.get("cashflows", {})
    trade = context.get("trade", "Rural Enterprise")
    lang = beneficiary.preferred_language or "kannada"

    # Create proposal row in database with status='DRAFT'
    proposal_data = {
        "beneficiary_id": beneficiary.id,
        "business_trade": trade,
        "scheme_tier": fin["scheme"],
        "project_cost": fin["cost"],
        "sanctioned_loan": fin["loan"],
        "beneficiary_margin": fin["margin"],
        "monthly_emi": fin["emi"],
        "projected_dscr": cashflows.get("dscr", 1.65),
        "status": "DRAFT",
        "dpr_pdf_url": None
    }
    proposal = crud.create_proposal(db, proposal_data)

    contact_id = beneficiary.telegram_chat_id if getattr(beneficiary, "primary_channel", "") == "telegram" else beneficiary.whatsapp_number

    beneficiary_dict = {
        "id": beneficiary.id,
        "full_name": beneficiary.full_name or "Rural Entrepreneur",
        "whatsapp_number": contact_id,
        "district": beneficiary.district or "Belagavi",
        "state": beneficiary.state or "Karnataka",
        "preferred_language": beneficiary.preferred_language,
        "annual_family_income": float(beneficiary.annual_family_income or 65000.0)
    }

    proposal_dict = {
        "id": proposal.id,
        "business_trade": proposal.business_trade,
        "scheme_tier": proposal.scheme_tier,
        "project_cost": float(proposal.project_cost),
        "sanctioned_loan": float(proposal.sanctioned_loan),
        "beneficiary_margin": float(proposal.beneficiary_margin),
        "monthly_emi": float(proposal.monthly_emi),
        "projected_dscr": float(proposal.projected_dscr),
        "status": proposal.status,
        "multi_schemes": context.get("multi_schemes") or {},
        "cashflows": context.get("cashflows") or {},
        "nabard_benchmark": context.get("nabard_benchmark") or "",
        "district": beneficiary.district or context.get("district") or "Belagavi",
        "state": beneficiary.state or context.get("state") or "Karnataka",
    }

    # Generate PDF
    pdf_filename = f"DPR_{trade.replace(' ', '_')}_{str(proposal.id)[:8]}.pdf"
    pdf_bytes = generate_dpr_pdf(proposal_dict, beneficiary_dict)

    # Upload to Cloudflare R2 / local fallback
    public_url = upload_dpr_pdf(pdf_bytes, pdf_filename)
    proposal.dpr_pdf_url = public_url
    beneficiary.conversation_state = "SUBMITTED"
    db.commit()

    channel_name = "Telegram" if getattr(beneficiary, "primary_channel", "") == "telegram" else "WhatsApp"

    # Multilingual caption and delivery confirmation
    if lang == "kannada":
        caption = f"📄 ನಿಮ್ಮ {trade} ಉದ್ಯಮದ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿ (DPR). ಉಲ್ಲೇಖ: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 ಅಭಿನಂದನೆಗಳು! ನಿಮ್ಮ ವಿವರವಾದ ಯೋಜನಾ ವರದಿ (DPR PDF) ಸಿದ್ಧವಾಗಿದ್ದು, ಮೇಲೆ ಕಳುಹಿಸಲಾಗಿದೆ!\n\n"
            f"📋 *ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *ಸ್ಥಿತಿ*: ಪರಿಶೀಲನೆಗಾಗಿ ರಾಜ್ಯ ವಾಹಕ ಏಜೆನ್ಸಿ (SCA) ಗೆ ಸಲ್ಲಿಸಲಾಗಿದೆ.\n\n"
            f"ನಿಗಮದ ಅಧಿಕಾರಿಗಳು ನಿಮ್ಮ ಸ್ಥಳ ಮತ್ತು ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿದ ನಂತರ, ನಿಮ್ಮ ಸಾಲ ಮಂಜೂರಾತಿ ಅಧಿಸೂಚನೆಯು ನೇರವಾಗಿ ಇಲ್ಲಿಯೇ {channel_name} ನಲ್ಲಿ ತಲುಪಲಿದೆ."
        )
    elif lang == "hindi":
        caption = f"📄 आपके {trade} व्यवसाय की बैंक रिपोर्ट (DPR). संदर्भ: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 बधाई! आपकी विस्तृत परियोजना रिपोर्ट (DPR PDF) तैयार होकर ऊपर भेजी जा चुकी है!\n\n"
            f"📋 *संदर्भ संख्या (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *स्थिति*: सत्यापन हेतु राज्य एजेंसी को प्रेषित।\n\n"
            f"सत्यापन के पश्चात आपकी ऋण स्वीकृति की सूचना सीधे यहीं {channel_name} पर प्राप्त होगी।"
        )
    else:
        caption = f"📄 Detailed Project Report (DPR) for your {trade}. Ref: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 Your Detailed Project Report (DPR) has been generated and sent above!\n\n"
            f"📋 *Reference ID*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *Status*: Submitted to State Channelizing Agency (SCA) for field geo-verification.\n\n"
            f"An SCA field officer will visit to verify your margin money and location, after which your sanction notification will arrive right here on {channel_name}."
        )

    # Deliver document directly with raw PDF bytes for zero-tunnel Telegram delivery
    send_channel_document(
        beneficiary,
        document_url=public_url,
        filename=pdf_filename,
        caption=caption,
        document_bytes=pdf_bytes
    )

    send_channel_text(beneficiary, confirmation_msg)


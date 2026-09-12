import re
import json
import logging
from typing import Dict, Any, Optional
from .llm_client import call_llm_chat
from app.finance.multi_schemes import get_all_eligible_schemes

logger = logging.getLogger("ai_extraction")

EXTRACTION_SYSTEM_PROMPT = """You are an AI data extractor for a rural micro-enterprise lending portal in India.
Your job is to read the user's message (which may be in English, Hindi, Kannada, or code-mixed) and extract:
1. "trade": the specific business or micro-enterprise (e.g. Kirana stall, Dairy cow, Tailoring, Flour mill, Weaving).
2. "district": district in India (e.g. Belagavi, Mysuru, Dharwad, Pune, Varanasi, etc. or null if unknown).
3. "state": Indian state (e.g. Karnataka, Maharashtra, Uttar Pradesh, etc. or null if unknown).
4. "available_capital": the money or savings the user says they have on hand (numeric, or null).
5. "project_cost": total estimated cost or capital needed for the venture (numeric, or null).
6. "language": language of interaction (e.g. kannada, hindi, english, marathi, tamil).

CRITICAL INSTRUCTIONS:
- You must NEVER compute, calculate, or estimate loan amounts, EMIs, or interest rates.
- Only extract explicitly mentioned or directly implied numerical values.
- Respond with STRICT JSON matching this schema:
{
  "trade": "string or null",
  "district": "string or null",
  "state": "string or null",
  "available_capital": number or null,
  "project_cost": number or null,
  "language": "string"
}
"""

def extract_entrepreneur_details(user_text: str) -> Dict[str, Any]:
    """Extract structured entrepreneur parameters from conversational input."""
    from app.config import settings
    from app.ai.gemini_client import is_gemini_configured

    if not is_gemini_configured():
        return fallback_regex_extractor(user_text)

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"User message: {user_text}"}
    ]

    try:
        raw_output = call_llm_chat(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        if raw_output and raw_output.strip():
            # Clean possible markdown wrapping
            clean_json = raw_output.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?", "", clean_json)
                clean_json = re.sub(r"```$", "", clean_json).strip()
            data = json.loads(clean_json)
            return data
    except Exception as e:
        logger.warning(f"LLM extraction failed or returned invalid JSON ({e}). Using regex heuristics.")

    return fallback_regex_extractor(user_text)

def fallback_regex_extractor(text: str) -> Dict[str, Any]:
    """Heuristic regex extractor when LLM API is unavailable or offline. Returns None for missing fields."""
    numbers = [float(n.replace(',', '')) for n in re.findall(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', text, re.I) if float(n.replace(',', '')) > 500]

    project_cost = numbers[0] if numbers else None
    capital = numbers[1] if len(numbers) > 1 else None

    trade = None
    lower_t = text.lower()
    if any(w in lower_t for w in ["kirana", "grocery", "provision", "store", "stall", "shop"]):
        trade = "Kirana Store"
    elif any(w in lower_t for w in ["dairy", "cow", "milk", "buffalo", "cattle", "ಹಸು", "ಹೈನುಗಾರಿಕೆ"]):
        trade = "Dairy Farming"
    elif any(w in lower_t for w in ["tailor", "tailoring", "garment", "clothes", "ಹೊಲಿಗೆ"]):
        trade = "Tailoring Unit"
    elif any(w in lower_t for w in ["poultry", "chicken", "broiler", "egg", "ಕೋಳಿ"]):
        trade = "Poultry Farm"
    elif any(w in lower_t for w in ["flour", "mill", "atta", "ಹಿಟ್ಟು", "ಗಿರಣಿ"]):
        trade = "Flour Mill"
    elif any(w in lower_t for w in ["weave", "weaver", "loom", "handloom", "ಮಗ್ಗ"]):
        trade = "Handloom Weaving"

    district = None
    if "belagavi" in lower_t or "belgaum" in lower_t or "ಬೆಳಗಾವಿ" in text:
        district = "Belagavi"
    elif "mysuru" in lower_t or "mysore" in lower_t or "ಮೈಸೂರು" in text:
        district = "Mysuru"
    elif "dharwad" in lower_t or "hubballi" in lower_t or "ಧಾರವಾಡ" in text:
        district = "Dharwad"
    elif "mandya" in lower_t or "ಮಂಡ್ಯ" in text:
        district = "Mandya"
    elif "shivamogga" in lower_t or "shimoga" in lower_t or "ಶಿವಮೊಗ್ಗ" in text:
        district = "Shivamogga"
    elif "hassan" in lower_t or "ಹಾಸನ" in text:
        district = "Hassan"

    # Language detection
    lang = "english"
    if any(w in lower_t for w in ["kannada", "ಕನ್ನಡ"]) or any(0x0C80 <= ord(c) <= 0x0CFF for c in text):
        lang = "kannada"
    elif any(w in lower_t for w in ["hindi", "हिंदी"]) or any(0x0900 <= ord(c) <= 0x097F for c in text):
        lang = "hindi"

    return {
        "trade": trade,
        "district": district,
        "state": "Karnataka" if district else None,
        "available_capital": capital,
        "project_cost": project_cost,
        "language": lang
    }

ADVISORY_SYSTEM_PROMPT = """You are a senior Rural Enterprise Advisory Officer for Indian Government Financial Inclusion Programs.
You provide rural micro-entrepreneurs with an inspiring, highly structured, and personalized financial sanctioning roadmap.

MANDATORY RULES:
1. Quote the pre-calculated primary lending figures VERBATIM. DO NOT alter or recalculate:
   - Primary Scheme: {scheme_name}
   - Project Cost: ₹{cost:,.2f}
   - Sanctioned Agency Loan: ₹{loan:,.2f}
   - Entrepreneur Margin Money Required: ₹{margin:,.2f} ({margin_pct}%)
   - Annual Interest Rate: {rate}% p.a. (reducing balance)
   - Total Tenure: {tenure} months (with {morat} months moratorium)
   - Monthly Installment (EMI): ₹{emi:,.2f} for {repay_mos} months

2. Present MULTIPLE eligible government schemes tailored to their project:
   - 🌟 Primary Direct Scheme: {scheme_name} (Low-interest State Channelising Agency loan)
   - 🏦 Alternative 1 (Zero-Collateral Bank Loan): {mudra_name} (No collateral or third-party guarantee, covers ₹{mudra_loan:,.2f})
   - 🎁 Alternative 2 (Government Subsidy Grant): PMEGP (KVIC/DIC) with {pmegp_subsidy}% Government Margin Subsidy (₹{pmegp_subsidy_amount:,.2f} grant! Beneficiary only invests 5% own savings)
   {sectoral_scheme_info}

3. Include actionable, step-by-step instructions on HOW TO REDEEM / APPLY for these schemes:
   - Application platforms (JanSamarth portal www.jansamarth.in, KVIC portal www.kviconline.gov.in, or District SCA/DIC office)
   - Required documents (Aadhaar, Bank Passbook, Caste/Income Certificate, Asset Quotation, and Bankable DPR)

4. Format using clean Telegram/WhatsApp Markdown with emojis, bold headers, and structured bullet lists.
5. Ground business viability in NABARD benchmarks if provided: {nabard_benchmark}
6. Always end with: "Reply *GENERATE DPR* to instantly download your bank-ready Detailed Project Report (PDF) with 5-year financial projections and DSCR viability."
7. STRICT LANGUAGE MANDATE (TARGET LANGUAGE: {language}):
   - If {language} is "kannada": You MUST write 100% of your response in fluent KANNADA SCRIPT (ಕನ್ನಡ ಲಿಪಿ). Every greeting, heading, explanation, bullet point, and call-to-action MUST be in Kannada. Keep only scheme acronyms (e.g. MFS, PMEGP, MUDRA, KVIC) and web links (www.jansamarth.in) in Latin script. Absolutely NEVER reply in English!
   - If {language} is "hindi": You MUST write 100% of your response in DEVANAGARI SCRIPT (हिन्दी लिपि). Absolutely NEVER reply in English!
   - If {language} is "english": Write your response in professional English.
8. Keep the message concise and punchy (under 2,800 characters) so it reads effortlessly on mobile chat screens while covering all key points.
"""

def generate_advisory_message(
    financial_data: Dict[str, Any],
    trade: str,
    district: str,
    nabard_context: Optional[str] = None,
    language: str = "english",
    state: str = "Karnataka",
    available_capital: Optional[float] = None,
    multi_schemes: Optional[Dict[str, Any]] = None
) -> str:
    """Generate structured plain-language multi-scheme advisory with redemption instructions."""
    cost = float(financial_data.get("cost", 120000.0))

    if not multi_schemes:
        multi_schemes = get_all_eligible_schemes(
            cost=cost,
            trade=trade,
            district=district,
            state=state,
            available_capital=available_capital
        )

    mudra = multi_schemes.get("mudra", {})
    pmegp = multi_schemes.get("pmegp", {})
    sectoral = multi_schemes.get("sectoral")

    sectoral_info = ""
    if sectoral:
        sectoral_info = (
            f"- 🐄 Sector-Specific Scheme: {sectoral['name']} ({sectoral['type']})\n"
            f"  * Concession: {sectoral['highlights']}\n"
            f"  * Interest: {sectoral['interest_rate']}\n"
            f"  * How to Redeem: {sectoral['how_to_redeem'][0]}"
        )

    prompt = ADVISORY_SYSTEM_PROMPT.format(
        scheme_name=financial_data.get("scheme_name", "Government Scheme"),
        cost=cost,
        loan=financial_data.get("loan", 0),
        margin=financial_data.get("margin", 0),
        margin_pct=financial_data.get("margin_pct", 10),
        rate=financial_data.get("rate", 6.5),
        tenure=financial_data.get("tenure", 36),
        morat=financial_data.get("morat", 3),
        repay_mos=financial_data.get("repayment_months", 33),
        emi=financial_data.get("emi", 0),
        language=language,
        mudra_name=mudra.get("name", "PMMY Mudra"),
        mudra_loan=mudra.get("loan_amount", 0.0),
        pmegp_subsidy=pmegp.get("subsidy_pct", 35),
        pmegp_subsidy_amount=pmegp.get("subsidy_amount", 0.0),
        sectoral_scheme_info=sectoral_info,
        nabard_benchmark=nabard_context or "Standard rural enterprise viability benchmark."
    )

    user_content = (
        f"Beneficiary Business Trade: {trade}\n"
        f"District: {district}, {state}\n"
        f"Available Own Savings: ₹{available_capital or 'Not specified'}\n"
        f"NABARD Context: {nabard_context or 'Financially viable rural unit'}\n"
        f"Required Reply Language Script: {language.upper()} SCRIPT ONLY"
    )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        advisory_text = call_llm_chat(messages=messages, temperature=0.3)
        if advisory_text and len(advisory_text.strip()) > 50:
            clean_adv = advisory_text.strip()
            # Strict language script verification
            if language == "kannada":
                kn_chars = sum(1 for c in clean_adv if 0x0C80 <= ord(c) <= 0x0CFF)
                if kn_chars < 50:
                    logger.warning(f"LLM produced insufficient Kannada characters ({kn_chars}). Falling back to verified Kannada template.")
                    raise ValueError("LLM response failed Kannada script verification")
            elif language == "hindi":
                hi_chars = sum(1 for c in clean_adv if 0x0900 <= ord(c) <= 0x097F)
                if hi_chars < 50:
                    logger.warning(f"LLM produced insufficient Hindi characters ({hi_chars}). Falling back to verified Hindi template.")
                    raise ValueError("LLM response failed Hindi script verification")
            return clean_adv
    except Exception as e:
        logger.warning(f"Advisory generation fallback triggered ({e}). Using verified regional template.")

    # Rich, structured deterministic fallback response
    scheme_name = financial_data.get("scheme_name", "Micro Finance Scheme (MFS)")
    loan_val = financial_data.get("loan", cost * 0.90)
    margin_val = financial_data.get("margin", cost * 0.10)
    margin_pct_val = financial_data.get("margin_pct", 10)
    rate_val = financial_data.get("rate", 6.5)
    tenure_val = financial_data.get("tenure", 36)
    morat_val = financial_data.get("morat", 3)
    repay_mos_val = financial_data.get("repayment_months", 33)
    emi_val = financial_data.get("emi", 0)

    pmegp_sub = pmegp.get("subsidy_amount", cost * 0.35)
    mudra_loan_val = mudra.get("loan_amount", cost * 0.85)

    if language == "kannada":
        sectoral_block_kn = ""
        if sectoral:
            sectoral_block_kn = (
                f"\n🎯 *ವಿಶೇಷ ವಲಯ ಯೋಜನೆ: {sectoral['name']}*\n"
                f"• *ಪ್ರಯೋಜನ*: {sectoral['highlights']}\n"
                f"• *ಬಡ್ಡಿದರ*: {sectoral['interest_rate']}\n"
                f"• *ಪಡೆಯುವುದು ಹೇಗೆ*: {sectoral['how_to_redeem'][0]}\n"
            )

        return (
            f"🌾 *ವೈಯಕ್ತಿಕ ಉದ್ಯಮ ಸಾಲ ಸಲಹೆ: {trade} ({district}, {state})*\n\n"
            f"ನಿಮ್ಮ ಉದ್ಯಮ ಯೋಜನೆಯನ್ನು ಹಂಚಿಕೊಂಡಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ *₹{cost:,.2f}* ಕ್ಕೆ, "
            f"ನೀವು ಈ ಕೆಳಗಿನ ಸರ್ಕಾರಿ ಸಾಲ ಮತ್ತು ಸಬ್ಸಿಡಿ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿದ್ದೀರಿ:\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏛️ *ಯೋಜನೆ 1 (ಅತ್ಯಂತ ಕಡಿಮೆ ಬಡ್ಡಿ ನೇರ ಸಾಲ): {scheme_name}*\n"
            f"• *ಸಂಸ್ಥೆ*: ರಾಜ್ಯ ವಾಹಕ ಏಜೆನ್ಸಿ (ಹಿಂದುಳಿದ ವರ್ಗಗಳ / ಅಲ್ಪಸಂಖ್ಯಾತರ ಅಭಿವೃದ್ಧಿ ನಿಗಮ)\n"
            f"• *ಮಂಜೂರಾಗುವ ಸಾಲ (90%)*: ₹{loan_val:,.2f}\n"
            f"• *ನಿಮ್ಮ ಸ್ವಂತ ಬಂಡವಾಳ (ಮಾರ್ಜಿನ್)*: ₹{margin_val:,.2f} ({margin_pct_val}%)\n"
            f"• *ಬಡ್ಡಿ ದರ*: ವಾರ್ಷಿಕ {rate_val}% (ಕಡಿಮೆ ಬಡ್ಡಿದರ)\n"
            f"• *ಅವಧಿ*: {tenure_val} ತಿಂಗಳುಗಳು ({morat_val} ತಿಂಗಳ ಮೊರಟೋರಿಯಂ ಸೇರಿ)\n"
            f"• *ಮಾಸಿಕ ಕಂತು (EMI)*: ₹{emi_val:,.2f} ({repay_mos_val} ತಿಂಗಳುಗಳ ಕಾಲ)\n"
            f"📍 *ಪಡೆಯುವುದು ಹೇಗೆ*: {district} ಜಿಲ್ಲೆಯ ನಿಗಮದ ಕಚೇರಿಗೆ ಅಥವಾ ಜಿಲ್ಲಾ ಕೈಗಾರಿಕಾ ಕೇಂದ್ರಕ್ಕೆ (DIC) ಭೇಟಿ ನೀಡಿ. "
            f"ಆಧಾರ್, ಜಾತಿ/ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ, ದರಪಟ್ಟಿ (Quotations) ಮತ್ತು ಡಿಪಿಆರ್ ಸಲ್ಲಿಸಿ.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 *ಯೋಜನೆ 2 (ಹೆಚ್ಚಿನ ಬಂಡವಾಳ ಸಬ್ಸಿಡಿ): PMEGP (KVIC / DIC)*\n"
            f"• *ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ ಅನುದಾನ*: *35% (₹{pmegp_sub:,.2f})* ಗ್ರಾಮೀಣ ಪ್ರದೇಶಕ್ಕೆ ನೇರ ಸಬ್ಸಿಡಿ\n"
            f"• *ಉದ್ಯಮಿಯ ಪಾಲು*: ಕೇವಲ 5% (ಮಹಿಳೆಯರು/ವಿಶೇಷ ವರ್ಗಗಳಿಗೆ)\n"
            f"• *ಬ್ಯಾಂಕ್ ಸಾಲ*: ಉಳಿದ 60% ಅವಧಿ ಸಾಲ\n"
            f"📍 *ಪಡೆಯುವುದು ಹೇಗೆ*: KVIC ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ (*www.kviconline.gov.in*) ಅರ್ಜಿ ಸಲ್ಲಿಸಿ. "
            f"ಡಿಪಿಆರ್ ಮತ್ತು ಕೆವೈಸಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ; ಜಿಲ್ಲಾ ಸಮಿತಿ ಪರಿಶೀಲಿಸಿ {district} ಬ್ಯಾಂಕ್‌ಗೆ ಕಳುಹಿಸುತ್ತದೆ.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 *ಯೋಜನೆ 3 (ಶ್ಯೂರಿಟಿ ರಹಿತ ಬ್ಯಾಂಕ್ ಸಾಲ): {mudra.get('name', 'PMMY ಮುದ್ರಾ')}*\n"
            f"• *ಸಾಲದ ಮೊತ್ತ*: ₹{mudra_loan_val:,.2f} ವರೆಗೆ\n"
            f"• *ಶ್ಯೂರಿಟಿ*: ಶೂನ್ಯ (ಸರ್ಕಾರದ CGFMU ಖಾತರಿ)\n"
            f"• *ಬಡ್ಡಿ ದರ*: {mudra.get('interest_rate', '9.5% - 10.5% p.a.')}\n"
            f"📍 *ಪಡೆಯುವುದು ಹೇಗೆ*: JanSamarth ಪೋರ್ಟಲ್‌ನಲ್ಲಿ (*www.jansamarth.in*) ಅರ್ಜಿ ಸಲ್ಲಿಸಿ ಅಥವಾ {district} ನಲ್ಲಿರುವ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಶಾಖೆಗೆ ಭೇಟಿ ನೀಡಿ.\n"
            f"{sectoral_block_kn}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *ಸಿದ್ಧವಾಗಿಟ್ಟುಕೊಳ್ಳಬೇಕಾದ ದಾಖಲೆಗಳು*:\n"
            f"1. ಆಧಾರ್ ಕಾರ್ಡ್ & ಪ್ಯಾನ್ ಕಾರ್ಡ್\n"
            f"2. ಜಾತಿ ಮತ್ತು ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ\n"
            f"3. ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ / 6 ತಿಂಗಳ ಸ್ಟೇಟ್‌ಮೆಂಟ್\n"
            f"4. ಉಪಕರಣಗಳು/ಸರಕುಗಳ ದರಪಟ್ಟಿ (Quotations)\n"
            f"5. ಅಧಿಕೃತ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿ (DPR)\n\n"
            f"🚀 *ಮುಂದಿನ ಹಂತ*: 5 ವರ್ಷಗಳ ಆದಾಯ, ಲಾಭ-ನಷ್ಟ ಹಾಗೂ DSCR ಲೆಕ್ಕಾಚಾರವುಳ್ಳ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿಯನ್ನು (PDF) "
            f"ತಕ್ಷಣ ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು *GENERATE DPR* ಎಂದು ಉತ್ತರಿಸಿ!"
        )

    if language == "hindi":
        sectoral_block_hi = ""
        if sectoral:
            sectoral_block_hi = (
                f"\n🎯 *विशेष क्षेत्र योजना: {sectoral['name']}*\n"
                f"• *लाभ*: {sectoral['highlights']}\n"
                f"• *ब्याज दर*: {sectoral['interest_rate']}\n"
                f"• *आवेदन कैसे करें*: {sectoral['how_to_redeem'][0]}\n"
            )

        return (
            f"🌾 *व्यक्तिगत उद्यम ऋण सलाह: {trade} ({district}, {state})*\n\n"
            f"अपनी उद्यम योजना साझा करने के लिए धन्यवाद। आपकी ₹{cost:,.2f} की परियोजना लागत के आधार पर, "
            f"आप केंद्र और राज्य सरकार की निम्नलिखित ऋण एवं सब्सिडी योजनाओं के लिए पात्र हैं:\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏛️ *योजना 1 (अनुशंसित सबसे सस्ता ऋण): {scheme_name}*\n"
            f"• *संस्था*: राज्य चैनलाइजिंग एजेंसी (पिछड़ा वर्ग / अल्पसंख्यक विकास निगम)\n"
            f"• *स्वीकृत ऋण (90%)*: ₹{loan_val:,.2f}\n"
            f"• *आपका अंशदान*: ₹{margin_val:,.2f} ({margin_pct_val}%)\n"
            f"• *ब्याज दर*: {rate_val}% प्रति वर्ष (घटते शेष पर)\n"
            f"• *अवधि*: {tenure_val} महीने ({morat_val} महीने की छूट अवधि सहित)\n"
            f"• *मासिक किस्त (EMI)*: ₹{emi_val:,.2f} ({repay_mos_val} महीनों के लिए)\n"
            f"📍 *आवेदन कैसे करें*: {district} जिले में निगम कार्यालय या जिला उद्योग केंद्र (DIC) से संपर्क करें। "
            f"आधार, जाति/आय प्रमाण पत्र, कोटेशन और अपनी डीपीआर जमा करें।\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 *योजना 2 (उच्च पूंजी सब्सिडी): PMEGP (KVIC / DIC)*\n"
            f"• *सरकारी सब्सिडी अनुदान*: *35% (₹{pmegp_sub:,.2f})* ग्रामीण क्षेत्र के लिए सीधा अनुदान\n"
            f"• *उद्यमी का अंशदान*: केवल 5% (महिलाओं एवं आरक्षित वर्गों हेतु)\n"
            f"• *बैंक ऋण*: शेष 60% मियादी ऋण\n"
            f"📍 *आवेदन कैसे करें*: KVIC के आधिकारिक पोर्टल (*www.kviconline.gov.in*) पर ऑनलाइन आवेदन करें। "
            f"डीपीआर और केवाईसी अपलोड करें; जिला टास्क फोर्स समिति {district} में आपके बैंक को प्रेषित करेगी।\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 *योजना 3 (बिना गारंटी बैंक ऋण): {mudra.get('name', 'PMMY मुद्रा')}*\n"
            f"• *ऋण सीमा*: ₹{mudra_loan_val:,.2f} तक\n"
            f"• *गारंटी*: शून्य (सरकार के CGFMU के तहत सुरक्षित)\n"
            f"• *ब्याज दर*: {mudra.get('interest_rate', '9.5% - 10.5% p.a.')}\n"
            f"📍 *आवेदन कैसे करें*: जनसमर्थ पोर्टल (*www.jansamarth.in*) पर आवेदन करें या {district} में अपने बैंक की शाखा में संपर्क करें।\n"
            f"{sectoral_block_hi}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *आवश्यक दस्तावेजों की सूची*:\n"
            f"1. आधार कार्ड एवं पैन कार्ड\n"
            f"2. जाति एवं आय प्रमाण पत्र\n"
            f"3. बैंक पासबुक / 6 माह का विवरण\n"
            f"4. उपकरण/सामग्री के कोटेशन\n"
            f"5. आधिकारिक बैंक विस्तृत परियोजना रिपोर्ट (DPR)\n\n"
            f"🚀 *अगला कदम*: 5-वर्षीय वित्तीय अनुमान एवं DSCR व्यवहार्यता रिपोर्ट (PDF) "
            f"तुरंत डाउनलोड करने के लिए *GENERATE DPR* लिखकर भेजें!"
        )

    # English fallback
    sectoral_block = ""
    if sectoral:
        sectoral_block = (
            f"\n🎯 *Specialized Sector Scheme: {sectoral['name']}*\n"
            f"• *Benefit*: {sectoral['highlights']}\n"
            f"• *Interest*: {sectoral['interest_rate']}\n"
            f"• *Redemption*: {sectoral['how_to_redeem'][0]}\n"
        )

    return (
        f"🌾 *Personalized Enterprise Advisory: {trade} ({district}, {state})*\n\n"
        f"Thank you for sharing your enterprise plan. Based on your project outlay of *₹{cost:,.2f}*, "
        f"you are eligible for multiple central and state government credit-linked schemes:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ *SCHEME 1 (Recommended Direct Loan): {scheme_name}*\n"
        f"• *Agency*: State Channelising Agency (NBCFDC / NMDFC / Backward Classes Corp)\n"
        f"• *Sanctioned Loan (90%)*: ₹{loan_val:,.2f}\n"
        f"• *Your Margin Contribution*: ₹{margin_val:,.2f} ({margin_pct_val}%)\n"
        f"• *Interest Rate*: {rate_val}% p.a. (reducing balance - lowest rate)\n"
        f"• *Tenure*: {tenure_val} months (includes {morat_val} months moratorium)\n"
        f"• *Monthly EMI*: ₹{emi_val:,.2f} (for {repay_mos_val} months)\n"
        f"📍 *How to Redeem*: Visit the District SCA / Backward Classes Development Corporation office or DIC in {district}. "
        f"Submit KYC, caste/income certificate, asset quotations, and your DPR. Loan is disbursed directly to asset vendors.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 *SCHEME 2 (High Capital Subsidy): PMEGP (KVIC / DIC)*\n"
        f"• *Government Subsidy Grant*: *35% (₹{pmegp_sub:,.2f})* direct back-ended grant in rural areas\n"
        f"• *Beneficiary Contribution*: Only 5% required for special categories (SC/ST/OBC/Women)\n"
        f"• *Bank Financing*: Balance 60% term loan\n"
        f"📍 *How to Redeem*: Apply online on the official KVIC portal (*www.kviconline.gov.in*). "
        f"Upload your DPR and KYC; District Task Force Committee (DTFC) screens and forwards to your bank branch in {district}.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *SCHEME 3 (Zero-Collateral Bank Loan): {mudra.get('name', 'PMMY MUDRA')}*\n"
        f"• *Loan Coverage*: Up to ₹{mudra_loan_val:,.2f}\n"
        f"• *Collateral*: Zero (Guaranteed under Government CGFMU)\n"
        f"• *Interest Rate*: {mudra.get('interest_rate', '9.5% - 10.5% p.a.')}\n"
        f"📍 *How to Redeem*: Apply on the JanSamarth portal (*www.jansamarth.in*) or visit any SBI, Canara Bank, "
        f"or Karnataka Gramin Bank branch in {district} with your DPR and Udyam registration.\n"
        f"{sectoral_block}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Checklist of Documents to Keep Ready*:\n"
        f"1. Aadhaar Card & PAN Card\n"
        f"2. Caste & Income Certificate (from Tahsildar / Nadakacheri)\n"
        f"3. Bank Passbook / 6-month statement\n"
        f"4. Quotations for equipment/cattle/inventory\n"
        f"5. Official Detailed Project Report (DPR)\n\n"
        f"🚀 *Next Step*: Reply *GENERATE DPR* to instantly create your official bankable Detailed Project Report (PDF) "
        f"complete with 5-year cash flows, profit-loss projections, and DSCR debt-servicing viability!"
    )

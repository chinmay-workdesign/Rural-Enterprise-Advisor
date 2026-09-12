import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import engine, Base, get_db, init_db
from app.db import crud, models
from app.whatsapp.webhook_handler import router as whatsapp_router
from app.whatsapp.client import send_whatsapp_text, send_whatsapp_document

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rural_advisor_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    init_db()
    yield
    logger.info("Shutting down Rural Advisor API...")

app = FastAPI(
    title="Rural Micro-Enterprise WhatsApp AI Advisory & Structuring API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure local static directory for DPRs exists and mount it
static_dir = os.path.join(os.getcwd(), "static", "dprs")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/dprs", StaticFiles(directory=static_dir), name="static_dprs")

# Include WhatsApp and Telegram Webhook routers
from app.whatsapp.webhook_handler import router as whatsapp_router
from app.telegram.webhook_handler import router as telegram_router

app.include_router(whatsapp_router)
app.include_router(telegram_router)

# Request schemas for internal SCA dashboard
class VerificationRequest(BaseModel):
    field_officer_id: str
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None
    margin_money_verified: bool = True
    recommendation: str = "APPROVE"  # APPROVE, REJECT, REVISIT
    remarks: Optional[str] = None

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Rural Micro-Enterprise WhatsApp AI Advisory",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/internal/proposals")
def list_proposals(
    status: Optional[str] = None,
    district: Optional[str] = None,
    scheme: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve proposals with beneficiary details for SCA field dashboard."""
    proposals = crud.get_proposals(db, status=status, district=district, scheme=scheme)
    results = []
    for p in proposals:
        b = p.beneficiary
        results.append({
            "id": p.id,
            "beneficiary_id": p.beneficiary_id,
            "beneficiary_name": b.full_name or "Rural Entrepreneur",
            "whatsapp_number": b.whatsapp_number,
            "district": b.district,
            "state": b.state,
            "business_trade": p.business_trade,
            "scheme_tier": p.scheme_tier,
            "project_cost": float(p.project_cost),
            "sanctioned_loan": float(p.sanctioned_loan),
            "beneficiary_margin": float(p.beneficiary_margin),
            "monthly_emi": float(p.monthly_emi),
            "projected_dscr": float(p.projected_dscr),
            "status": p.status,
            "dpr_pdf_url": p.dpr_pdf_url,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    return results

@app.post("/internal/sanction/{proposal_id}")
def sanction_proposal(
    proposal_id: str,
    payload: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    SCA Field Officer approval endpoint:
    1. Log geo-verification and margin money status
    2. Transition status to SANCTIONED
    3. Trigger automated WhatsApp sanction notification to beneficiary
    """
    proposal = crud.get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Record field verification
    verification_data = {
        "proposal_id": proposal.id,
        "field_officer_id": payload.field_officer_id,
        "geo_latitude": payload.geo_latitude,
        "geo_longitude": payload.geo_longitude,
        "margin_money_verified": payload.margin_money_verified,
        "recommendation": payload.recommendation
    }
    crud.record_field_verification(db, verification_data)

    if payload.recommendation == "APPROVE":
        crud.update_proposal_status(db, proposal_id, "SANCTIONED")
        beneficiary = proposal.beneficiary

        # Automated Multi-Channel Sanction Dispatch (Telegram or WhatsApp)
        from app.dialogue.conversation_state import send_channel_text, send_channel_document

        sanction_msg = (
            f"🎉 *CONGRATULATIONS! LOAN SANCTION NOTIFICATION* 🎉\n\n"
            f"Dear {beneficiary.full_name or 'Entrepreneur'},\n"
            f"Your enterprise proposal for *{proposal.business_trade}* has been officially *SANCTIONED* by the State Channelizing Agency!\n\n"
            f"📋 *Sanction Summary*:\n"
            f"• Reference ID: DPR-{str(proposal.id)[:8].upper()}\n"
            f"• Scheme: {proposal.scheme_tier}\n"
            f"• Sanctioned Agency Loan: ₹{float(proposal.sanctioned_loan):,.2f}\n"
            f"• Verified Margin Money: ₹{float(proposal.beneficiary_margin):,.2f}\n"
            f"• Monthly EMI: ₹{float(proposal.monthly_emi):,.2f}\n\n"
            f"📍 Verified by Field Officer: {payload.field_officer_id}\n\n"
            f"Please visit your local SCA district office or nodal branch with your original Aadhaar and bank passbook for disbursement release."
        )

        send_channel_text(beneficiary, sanction_msg)

        if proposal.dpr_pdf_url:
            send_channel_document(
                beneficiary=beneficiary,
                document_url=proposal.dpr_pdf_url,
                filename=f"Sanction_Letter_{str(proposal.id)[:8]}.pdf",
                caption="Official Sanctioned DPR Letter"
            )

        return {"status": "success", "proposal_id": proposal_id, "new_status": "SANCTIONED"}

    elif payload.recommendation == "REJECT":
        crud.update_proposal_status(db, proposal_id, "REJECTED")
        beneficiary = proposal.beneficiary
        rejection_msg = (
            f"Notification from State Channelizing Agency:\n"
            f"Your proposal for {proposal.business_trade} could not be approved at this stage.\n"
            f"Reason / Remarks: {payload.remarks or 'Field verification requirements unmet.'}\n"
            f"You may submit a revised proposal or visit the district office for guidance."
        )
        from app.dialogue.conversation_state import send_channel_text
        send_channel_text(beneficiary, rejection_msg)
        return {"status": "success", "proposal_id": proposal_id, "new_status": "REJECTED"}

    else:
        crud.update_proposal_status(db, proposal_id, "REVISIT")
        return {"status": "success", "proposal_id": proposal_id, "new_status": "REVISIT"}

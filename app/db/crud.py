from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from .models import Beneficiary, EnterpriseProposal, SCAFieldVerification, WebhookEvent, User

def get_or_create_beneficiary(db: Session, whatsapp_number: str, default_lang: Optional[str] = None) -> Beneficiary:
    """Find existing beneficiary by whatsapp number or create a new one."""
    beneficiary = db.query(Beneficiary).filter(Beneficiary.whatsapp_number == whatsapp_number).first()
    if not beneficiary:
        beneficiary = Beneficiary(
            whatsapp_number=whatsapp_number,
            primary_channel="whatsapp",
            preferred_language=default_lang,
            conversation_state="LANGUAGE_SELECTION" if not default_lang else "COLLECTING",
            conversation_context={}
        )
        db.add(beneficiary)
        db.commit()
        db.refresh(beneficiary)
    return beneficiary

def get_or_create_telegram_beneficiary(
    db: Session,
    chat_id: str,
    full_name: Optional[str] = None,
    default_lang: Optional[str] = None
) -> Beneficiary:
    """Find existing beneficiary by Telegram chat_id or create a new one."""
    beneficiary = db.query(Beneficiary).filter(Beneficiary.telegram_chat_id == str(chat_id)).first()
    if not beneficiary:
        beneficiary = Beneficiary(
            telegram_chat_id=str(chat_id),
            whatsapp_number=f"tg_{chat_id}",  # unique fallback
            full_name=full_name,
            primary_channel="telegram",
            preferred_language=default_lang,
            conversation_state="LANGUAGE_SELECTION" if not default_lang else "COLLECTING",
            conversation_context={}
        )
        db.add(beneficiary)
        db.commit()
        db.refresh(beneficiary)
    elif full_name and not beneficiary.full_name:
        beneficiary.full_name = full_name
        db.commit()
        db.refresh(beneficiary)
    return beneficiary

def update_beneficiary(db: Session, beneficiary_id: str, **kwargs) -> Beneficiary:
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if beneficiary:
        for k, v in kwargs.items():
            if hasattr(beneficiary, k):
                setattr(beneficiary, k, v)
        db.commit()
        db.refresh(beneficiary)
    return beneficiary

def create_proposal(db: Session, proposal_data: Dict[str, Any]) -> EnterpriseProposal:
    proposal = EnterpriseProposal(**proposal_data)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal

def get_proposals(
    db: Session,
    status: Optional[str] = None,
    district: Optional[str] = None,
    scheme: Optional[str] = None
) -> List[EnterpriseProposal]:
    query = db.query(EnterpriseProposal)
    if status:
        query = query.filter(EnterpriseProposal.status == status)
    if scheme:
        query = query.filter(EnterpriseProposal.scheme_tier == scheme)
    if district:
        query = query.join(Beneficiary).filter(Beneficiary.district == district)
    return query.order_by(EnterpriseProposal.created_at.desc()).all()

def get_proposal_by_id(db: Session, proposal_id: str) -> Optional[EnterpriseProposal]:
    return db.query(EnterpriseProposal).filter(EnterpriseProposal.id == proposal_id).first()

def update_proposal_status(db: Session, proposal_id: str, status: str) -> Optional[EnterpriseProposal]:
    proposal = get_proposal_by_id(db, proposal_id)
    if proposal:
        proposal.status = status
        db.commit()
        db.refresh(proposal)
    return proposal

def record_field_verification(db: Session, verification_data: Dict[str, Any]) -> SCAFieldVerification:
    verification = SCAFieldVerification(**verification_data)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

def is_webhook_processed(db: Session, message_id: str) -> bool:
    """Check if a webhook event with message_id was already processed (idempotency)."""
    return db.query(WebhookEvent).filter(WebhookEvent.message_id == message_id).first() is not None

def record_webhook_event(db: Session, message_id: str, from_phone: str, msg_type: str) -> WebhookEvent:
    event = WebhookEvent(
        message_id=message_id,
        from_phone=from_phone,
        msg_type=msg_type
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by normalized lowercase email."""
    if not email:
        return None
    return db.query(User).filter(User.email == email.strip().lower()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Retrieve user by unique UUID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """Create and persist a new user."""
    normalized_data = dict(user_data)
    if "email" in normalized_data:
        normalized_data["email"] = normalized_data["email"].strip().lower()
    user = User(**normalized_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_default_users(db: Session) -> None:
    """Pre-seed default demo accounts for instant evaluation if they don't exist."""
    from app.auth.security import hash_password

    # Default Field Officer
    officer_email = "officer.belagavi@sca.gov.in"
    if not get_user_by_email(db, officer_email):
        create_user(db, {
            "email": officer_email,
            "hashed_password": hash_password("Officer@123"),
            "full_name": "Ramesh Rao",
            "role": "FIELD_OFFICER",
            "district": "Belagavi",
            "badge_number": "SCA-FO-8842",
            "is_active": True
        })

    # Default State Administrator
    admin_email = "admin@sca.gov.in"
    if not get_user_by_email(db, admin_email):
        create_user(db, {
            "email": admin_email,
            "hashed_password": hash_password("Admin@123"),
            "full_name": "Dr. Priya Deshmukh",
            "role": "ADMIN",
            "district": "State HQ (Bengaluru)",
            "badge_number": "SCA-DIR-001",
            "is_active": True
        })


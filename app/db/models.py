import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base

# Universal UUID column type helper that works on Postgres and SQLite
def make_uuid():
    return str(uuid.uuid4())

class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(String(36), primary_key=True, default=make_uuid)
    whatsapp_number = Column(String(50), unique=True, nullable=True, index=True)
    telegram_chat_id = Column(String(50), unique=True, nullable=True, index=True)
    primary_channel = Column(String(20), default="telegram")
    full_name = Column(String(100), nullable=True)
    preferred_language = Column(String(20), default="kannada")
    district = Column(String(60), nullable=True)
    state = Column(String(60), nullable=True)
    annual_family_income = Column(Numeric(12, 2), nullable=True)
    conversation_state = Column(String(30), default="GREETING")
    conversation_context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proposals = relationship("EnterpriseProposal", back_populates="beneficiary", cascade="all, delete-orphan")


class EnterpriseProposal(Base):
    __tablename__ = "enterprise_proposals"

    id = Column(String(36), primary_key=True, default=make_uuid)
    beneficiary_id = Column(String(36), ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False, index=True)
    business_trade = Column(String(100), nullable=False)
    scheme_tier = Column(String(30), nullable=False)  # MICRO_FINANCE or TERM_LOAN
    project_cost = Column(Numeric(12, 2), nullable=False)
    sanctioned_loan = Column(Numeric(12, 2), nullable=False)
    beneficiary_margin = Column(Numeric(12, 2), nullable=False)
    monthly_emi = Column(Numeric(10, 2), nullable=False)
    projected_dscr = Column(Numeric(4, 2), nullable=False)
    status = Column(String(30), default="DRAFT", index=True)  # DRAFT, SANCTIONED, REJECTED, REVISIT
    dpr_pdf_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    beneficiary = relationship("Beneficiary", back_populates="proposals")
    verifications = relationship("SCAFieldVerification", back_populates="proposal", cascade="all, delete-orphan")


class SCAFieldVerification(Base):
    __tablename__ = "sca_field_verifications"

    id = Column(String(36), primary_key=True, default=make_uuid)
    proposal_id = Column(String(36), ForeignKey("enterprise_proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    field_officer_id = Column(String(50), nullable=False)
    geo_latitude = Column(Numeric(10, 7), nullable=True)
    geo_longitude = Column(Numeric(10, 7), nullable=True)
    margin_money_verified = Column(Boolean, default=False)
    recommendation = Column(String(20), nullable=False)  # APPROVE, REJECT, REVISIT
    verified_at = Column(DateTime(timezone=True), server_default=func.now())

    proposal = relationship("EnterpriseProposal", back_populates="verifications")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=make_uuid)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    from_phone = Column(String(30), nullable=False)
    msg_type = Column(String(20), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

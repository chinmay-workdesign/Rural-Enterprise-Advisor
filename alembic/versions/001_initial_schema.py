"""Initial schema for beneficiaries, enterprise_proposals, sca_field_verifications, webhook_events

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-11 21:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Attempt to create uuid extension on Postgres
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.create_table(
        'beneficiaries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('whatsapp_number', sa.String(length=20), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('preferred_language', sa.String(length=20), server_default='kannada', nullable=True),
        sa.Column('district', sa.String(length=60), nullable=True),
        sa.Column('state', sa.String(length=60), nullable=True),
        sa.Column('annual_family_income', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('conversation_state', sa.String(length=30), server_default='GREETING', nullable=True),
        sa.Column('conversation_context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_beneficiaries_whatsapp_number', 'beneficiaries', ['whatsapp_number'], unique=True)

    op.create_table(
        'enterprise_proposals',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('beneficiary_id', sa.String(length=36), sa.ForeignKey('beneficiaries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_trade', sa.String(length=100), nullable=False),
        sa.Column('scheme_tier', sa.String(length=30), nullable=False),
        sa.Column('project_cost', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('sanctioned_loan', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('beneficiary_margin', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('monthly_emi', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('projected_dscr', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='DRAFT', nullable=True),
        sa.Column('dpr_pdf_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_enterprise_proposals_beneficiary_id', 'enterprise_proposals', ['beneficiary_id'])
    op.create_index('ix_enterprise_proposals_status', 'enterprise_proposals', ['status'])

    op.create_table(
        'sca_field_verifications',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('proposal_id', sa.String(length=36), sa.ForeignKey('enterprise_proposals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_officer_id', sa.String(length=50), nullable=False),
        sa.Column('geo_latitude', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('geo_longitude', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('margin_money_verified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('recommendation', sa.String(length=20), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_sca_field_verifications_proposal_id', 'sca_field_verifications', ['proposal_id'])

    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('message_id', sa.String(length=100), nullable=False),
        sa.Column('from_phone', sa.String(length=30), nullable=False),
        sa.Column('msg_type', sa.String(length=20), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_webhook_events_message_id', 'webhook_events', ['message_id'], unique=True)

def downgrade() -> None:
    op.drop_table('webhook_events')
    op.drop_table('sca_field_verifications')
    op.drop_table('enterprise_proposals')
    op.drop_table('beneficiaries')

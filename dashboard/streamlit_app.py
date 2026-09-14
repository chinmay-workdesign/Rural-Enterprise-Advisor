import sys
import os
import requests
import streamlit as st
import pandas as pd

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.db.session import SessionLocal
from app.db import crud

st.set_page_config(
    page_title="SCA Field Officer Console | Rural Enterprise Sanctions",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #4a5568;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #f7fafc;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #3182ce;
    }
    .status-badge-draft {
        background-color: #fefcbf;
        color: #744210;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;
    }
    .status-badge-sanctioned {
        background-color: #c6f6d5;
        color: #22543d;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

from app.auth.security import verify_password, hash_password

st.markdown('<div class="main-header">🌾 State Channelizing Agency (SCA) - Field Officer Console</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Rural Micro-Enterprise Advisory & Direct Loan Sanction Portal</div>', unsafe_allow_html=True)

# Authentication State Gate
if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None

if not st.session_state["authenticated_user"]:
    st.info("🔒 **Authentication Required**: Please sign in with your official SCA officer credentials to access the loan appraisal console.")

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Register Officer"])

    with auth_tab1:
        st.write("##### Official SCA Officer Sign In")

        # Instant demo access buttons
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("👤 Quick Demo: Belagavi Field Officer", use_container_width=True):
                db = SessionLocal()
                try:
                    crud.seed_default_users(db)
                    user = crud.get_user_by_email(db, "officer.belagavi@sca.gov.in")
                    if user:
                        st.session_state["authenticated_user"] = {
                            "id": user.id,
                            "email": user.email,
                            "full_name": user.full_name,
                            "role": user.role,
                            "district": user.district,
                            "badge_number": user.badge_number
                        }
                        st.success("Authenticated as Belagavi Field Officer!")
                        st.rerun()
                finally:
                    db.close()

        with d_col2:
            if st.button("🛡️ Quick Demo: State Administrator", use_container_width=True):
                db = SessionLocal()
                try:
                    crud.seed_default_users(db)
                    user = crud.get_user_by_email(db, "admin@sca.gov.in")
                    if user:
                        st.session_state["authenticated_user"] = {
                            "id": user.id,
                            "email": user.email,
                            "full_name": user.full_name,
                            "role": user.role,
                            "district": user.district,
                            "badge_number": user.badge_number
                        }
                        st.success("Authenticated as State Administrator!")
                        st.rerun()
                finally:
                    db.close()

        with st.form("login_form"):
            login_email = st.text_input("Official Email Address", placeholder="officer@sca.gov.in")
            login_pwd = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Secure Sign In", use_container_width=True)

            if login_submit:
                if not login_email or not login_pwd:
                    st.error("Please provide both email and password.")
                else:
                    db = SessionLocal()
                    try:
                        crud.seed_default_users(db)
                        user = crud.get_user_by_email(db, login_email)
                        if user and verify_password(login_pwd, user.hashed_password):
                            st.session_state["authenticated_user"] = {
                                "id": user.id,
                                "email": user.email,
                                "full_name": user.full_name,
                                "role": user.role,
                                "district": user.district,
                                "badge_number": user.badge_number
                            }
                            st.success(f"Welcome, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error("Invalid official email or password.")
                    finally:
                        db.close()

    with auth_tab2:
        st.write("##### Register New Officer / Manager")
        with st.form("signup_form"):
            s_name = st.text_input("Full Officer Name", placeholder="e.g. Ramesh Patil")
            s_email = st.text_input("Official Email", placeholder="e.g. ramesh.patil@sca.gov.in")
            s_role = st.selectbox("Designation", ["FIELD_OFFICER", "DISTRICT_MANAGER", "ADMIN"])
            s_district = st.selectbox("Assigned District", ["Belagavi", "Mandya", "Mysuru", "Dharwad", "Kalaburagi", "State HQ (Bengaluru)"])
            s_badge = st.text_input("Official Badge / Employee ID", placeholder="e.g. SCA-FO-9042")
            s_pwd = st.text_input("Create Password (min. 6 characters)", type="password")
            signup_submit = st.form_submit_button("Register & Enter", use_container_width=True)

            if signup_submit:
                if not s_name or not s_email or not s_pwd:
                    st.error("Please fill in all required fields.")
                elif len(s_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    db = SessionLocal()
                    try:
                        existing = crud.get_user_by_email(db, s_email)
                        if existing:
                            st.error("An account with this official email already exists.")
                        else:
                            new_user = crud.create_user(db, {
                                "email": s_email.strip().lower(),
                                "hashed_password": hash_password(s_pwd),
                                "full_name": s_name.strip(),
                                "role": s_role,
                                "district": s_district,
                                "badge_number": s_badge.strip() if s_badge else None,
                                "is_active": True
                            })
                            st.session_state["authenticated_user"] = {
                                "id": new_user.id,
                                "email": new_user.email,
                                "full_name": new_user.full_name,
                                "role": new_user.role,
                                "district": new_user.district,
                                "badge_number": new_user.badge_number
                            }
                            st.success("Account registered successfully!")
                            st.rerun()
                    finally:
                        db.close()

    st.stop()

# When authenticated, render officer status and logout option in sidebar
current_officer = st.session_state["authenticated_user"]
st.sidebar.markdown(f"""
<div style="background: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #0d5c3a; margin-bottom: 15px;">
    <div style="font-size: 11px; color: #083c25; font-weight: 700;">VERIFIED OFFICER</div>
    <div style="font-size: 14px; font-weight: 600; color: #0f172a;">{current_officer['full_name']}</div>
    <div style="font-size: 12px; color: #64748b;">{current_officer['district']} • {current_officer['role']}</div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state["authenticated_user"] = None
    st.rerun()


# Sidebar Filters
st.sidebar.header("🔍 Filter Proposals")
status_filter = st.sidebar.selectbox("Application Status", ["DRAFT", "SANCTIONED", "REJECTED", "ALL"], index=0)
scheme_filter = st.sidebar.selectbox("Scheme Tier", ["ALL", "MICRO_FINANCE", "TERM_LOAN"])
district_filter = st.sidebar.text_input("Filter by District (e.g. Belagavi)", "")
backend_api_url = st.sidebar.text_input("Backend API Endpoint", settings.BACKEND_INTERNAL_URL)

# Fetch proposals from DB
db = SessionLocal()
try:
    status_query = None if status_filter == "ALL" else status_filter
    scheme_query = None if scheme_filter == "ALL" else scheme_filter
    district_query = district_filter.strip() if district_filter.strip() else None

    proposals = crud.get_proposals(db, status=status_query, district=district_query, scheme=scheme_query)
    all_proposals = crud.get_proposals(db)
finally:
    db.close()

# Key Metrics
col1, col2, col3, col4 = st.columns(4)
total_apps = len(all_proposals)
draft_count = sum(1 for p in all_proposals if p.status == "DRAFT")
sanctioned_count = sum(1 for p in all_proposals if p.status == "SANCTIONED")
total_sanctioned_loan = sum(float(p.sanctioned_loan) for p in all_proposals if p.status == "SANCTIONED")

with col1:
    st.metric("Total Enterprise Proposals", total_apps)
with col2:
    st.metric("Pending Verification (DRAFT)", draft_count)
with col3:
    st.metric("Sanctioned Loans", sanctioned_count)
with col4:
    st.metric("Total Sanctioned Capital", f"₹{total_sanctioned_loan:,.0f}")

st.divider()

if not proposals:
    st.info("No proposals found matching the selected filter criteria. (Rural entrepreneurs submitting 'GENERATE DPR' via WhatsApp will appear here).")
else:
    st.subheader(f"📋 Proposals Requiring Action ({len(proposals)})")

    for p in proposals:
        b = p.beneficiary
        with st.expander(
            f"📍 [{p.status}] {p.business_trade} - {b.full_name or 'Beneficiary'} ({b.district or 'Rural Dist'}) | ₹{float(p.project_cost):,.0f}",
            expanded=(p.status == "DRAFT")
        ):
            c_left, c_right = st.columns([1.2, 1])

            with c_left:
                st.markdown("#### 👤 Beneficiary & Trade Details")
                st.write(f"**Beneficiary Name:** {b.full_name or 'Rural Entrepreneur'}")
                contact_info = f"Telegram Chat: `{b.telegram_chat_id}`" if getattr(b, 'primary_channel', '') == 'telegram' else f"WhatsApp: `{b.whatsapp_number}`"
                st.write(f"**Contact:** {contact_info}")
                st.write(f"**Location:** {b.district}, {b.state or 'Karnataka'}")
                st.write(f"**Preferred Language:** {(b.preferred_language or 'kannada').capitalize()}")
                st.write(f"**Target Enterprise:** **{p.business_trade}**")
                st.write(f"**Classification:** `{p.scheme_tier}`")

                st.markdown("#### 💰 Financial Structuring (Deterministic Rules)")
                f_df = pd.DataFrame([
                    {"Metric": "Total Project Cost", "Amount": f"₹{float(p.project_cost):,.2f}", "Notes": "100% Outlay"},
                    {"Metric": "SCA Agency Loan", "Amount": f"₹{float(p.sanctioned_loan):,.2f}", "Notes": "90% Capped"},
                    {"Metric": "Beneficiary Margin Money", "Amount": f"₹{float(p.beneficiary_margin):,.2f}", "Notes": f"{(float(p.beneficiary_margin)/float(p.project_cost))*100:.2f}% dynamic absorption"},
                    {"Metric": "Monthly EMI", "Amount": f"₹{float(p.monthly_emi):,.2f}", "Notes": "Reducing-balance annuity"},
                    {"Metric": "Projected DSCR", "Amount": f"{float(p.projected_dscr):.2f}", "Notes": "Debt Service Coverage Ratio"}
                ])
                st.table(f_df)

                ctx = b.conversation_context or {}
                multi = ctx.get("multi_schemes", {}) if isinstance(ctx, dict) else {}
                schemes = multi.get("schemes", [])
                if schemes:
                    st.markdown("#### 🏛️ Recommended Schemes & Capital Subsidies")
                    for s in schemes:
                        st.info(f"**{s.get('name', s.get('type'))}** ({s.get('interest_rate', 'Concessional')})\n\n{s.get('highlights', '')}")

                if p.dpr_pdf_url:
                    st.markdown(f"📄 **Detailed Project Report (PDF):** [Open / Download DPR]({p.dpr_pdf_url})")

            with c_right:
                st.markdown("#### 🛡️ Field Officer Geo-Verification")

                with st.form(key=f"verif_form_{p.id}"):
                    officer_id = st.text_input("Field Officer ID", value="SCA-OFFICER-KA-09", key=f"off_{p.id}")

                    # Geo coordinates with defaults for local testing
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        lat = st.number_input("GPS Latitude (±5m)", value=15.8497, format="%.6f", key=f"lat_{p.id}")
                    with g_col2:
                        lon = st.number_input("GPS Longitude (±5m)", value=74.4977, format="%.6f", key=f"lon_{p.id}")

                    margin_verified = st.checkbox(
                        "Beneficiary Margin Money Verified In-Hand (10%+)",
                        value=True,
                        key=f"margin_{p.id}"
                    )

                    recommendation = st.selectbox(
                        "Officer Recommendation",
                        ["APPROVE", "REJECT", "REVISIT"],
                        index=0,
                        key=f"rec_{p.id}"
                    )

                    remarks = st.text_area("Verification Remarks", "Beneficiary premises inspected. Enterprise viable and margin verified in bank passbook.", key=f"rem_{p.id}")

                    submit_btn = st.form_submit_button("⚡ Submit Verification & Trigger Sanction Notification")

                    if submit_btn:
                        payload = {
                            "field_officer_id": officer_id,
                            "geo_latitude": lat,
                            "geo_longitude": lon,
                            "margin_money_verified": margin_verified,
                            "recommendation": recommendation,
                            "remarks": remarks
                        }

                        try:
                            resp = requests.post(
                                f"{backend_api_url}/internal/sanction/{p.id}",
                                json=payload,
                                timeout=15
                            )
                            if resp.status_code == 200:
                                st.success(f"✅ Success! Proposal marked as {recommendation}. Automated WhatsApp sanction letter sent to {b.whatsapp_number}!")
                                st.rerun()
                            else:
                                st.error(f"Error submitting sanction: {resp.text}")
                        except Exception as e:
                            st.error(f"Could not connect to backend API at {backend_api_url}: {e}")

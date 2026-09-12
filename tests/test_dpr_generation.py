import os
import pytest
from app.dpr.generator import generate_dpr_pdf

def test_generate_mfs_dpr_pdf():
    """Test generating a Detailed Project Report PDF for Micro Finance Scheme."""
    proposal = {
        "id": "11111111-2222-3333-4444-555555555555",
        "business_trade": "Kirana Stall",
        "scheme_tier": "MICRO_FINANCE",
        "project_cost": 120000.0,
        "sanctioned_loan": 108000.0,
        "beneficiary_margin": 12000.0,
        "monthly_emi": 3584.22,
        "projected_dscr": 1.85,
        "status": "DRAFT"
    }
    beneficiary = {
        "id": "beneficiary-uuid-1",
        "full_name": "Basavaraj Patil",
        "whatsapp_number": "919876543210",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "kannada",
        "annual_family_income": 75000.0
    }

    test_output_file = os.path.join("tests", "output_sample_dpr.pdf")
    pdf_bytes = generate_dpr_pdf(proposal, beneficiary, output_path=test_output_file)

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    # Check standard PDF header
    assert pdf_bytes[:4] == b"%PDF"
    assert os.path.exists(test_output_file)

    # Cleanup
    if os.path.exists(test_output_file):
        os.remove(test_output_file)

def test_generate_tls_dpr_pdf():
    """Test generating a DPR PDF for Term Loan Scheme (Commercial Dairy)."""
    proposal = {
        "id": "22222222-3333-4444-5555-666666666666",
        "business_trade": "Commercial Dairy Unit (10 Cows)",
        "scheme_tier": "TERM_LOAN",
        "project_cost": 750000.0,
        "sanctioned_loan": 675000.0,
        "beneficiary_margin": 75000.0,
        "monthly_emi": 11172.63,
        "projected_dscr": 1.65,
        "status": "DRAFT"
    }
    beneficiary = {
        "id": "beneficiary-uuid-2",
        "full_name": "Ramesh Gowda",
        "whatsapp_number": "919845012345",
        "district": "Mysuru",
        "state": "Karnataka",
        "preferred_language": "kannada",
        "annual_family_income": 120000.0
    }

    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes[:4] == b"%PDF"

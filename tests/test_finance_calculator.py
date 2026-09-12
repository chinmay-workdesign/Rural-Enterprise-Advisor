import pytest
from app.finance.calculator import calculate_financial_structure, validate_project_cost
from app.finance.dscr import calculate_dscr, project_financial_cashflows

def test_mfs_typical_case_120k():
    """Test standard MFS case of ₹1,20,000 project cost."""
    result = calculate_financial_structure(120000.0)
    assert result["scheme"] == "MICRO_FINANCE"
    assert result["cost"] == 120000.0
    assert result["loan"] == 108000.0  # 90% of 120,000
    assert result["margin"] == 12000.0  # 10%
    assert result["margin_pct"] == 10.0
    assert result["rate"] == 6.5
    assert result["tenure"] == 36
    assert result["morat"] == 3
    assert result["repayment_months"] == 33
    assert result["emi"] > 0
    # loan + margin must strictly equal cost
    assert result["loan"] + result["margin"] == result["cost"]

def test_mfs_boundary_case_caps_loan_and_raises_margin():
    """
    CRITICAL EDGE CASE from Section 2 & Section 6.1:
    At project cost = ₹1,40,000, 90% = ₹1,26,000, which exceeds ₹1,25,000 cap.
    Loan is capped at ₹1,25,000 and margin rises dynamically to ₹15,000 (10.71%).
    """
    result = calculate_financial_structure(140000.0)
    assert result["scheme"] == "MICRO_FINANCE"
    assert result["loan"] == 125000.0
    assert result["margin"] == 15000.0
    assert round(result["margin_pct"], 2) == 10.71
    assert result["repayment_months"] == 33
    assert result["loan"] + result["margin"] == 140000.0

def test_tls_standard_case_500k():
    """Test standard Term Loan Scheme case of ₹5,00,000."""
    result = calculate_financial_structure(500000.0)
    assert result["scheme"] == "TERM_LOAN"
    assert result["cost"] == 500000.0
    assert result["loan"] == 450000.0  # 90% of 500,000
    assert result["margin"] == 50000.0  # 10%
    assert result["margin_pct"] == 10.0
    assert result["rate"] == 8.0
    assert result["tenure"] == 84
    assert result["morat"] == 6
    assert result["repayment_months"] == 78
    assert result["loan"] + result["margin"] == result["cost"]

def test_tls_max_ceiling_50_lakhs():
    """Test TLS maximum ceiling at ₹50,00,000."""
    result = calculate_financial_structure(5000000.0)
    assert result["scheme"] == "TERM_LOAN"
    assert result["loan"] == 4500000.0  # Capped at 45 lakhs
    assert result["margin"] == 500000.0  # 10%
    assert result["margin_pct"] == 10.0
    assert result["repayment_months"] == 78

def test_validation_errors():
    """Test boundary validation rules."""
    with pytest.raises(ValueError, match="below minimum"):
        calculate_financial_structure(2000.0)

    with pytest.raises(ValueError, match="exceeds Term Loan Scheme maximum"):
        calculate_financial_structure(6000000.0)

    with pytest.raises(ValueError, match="valid number"):
        validate_project_cost(None)

def test_dscr_calculation():
    """Test Debt Service Coverage Ratio computation."""
    res = calculate_financial_structure(100000.0)
    cashflows = project_financial_cashflows(res["cost"], res["emi"])
    assert cashflows["dscr"] > 1.0
    assert cashflows["is_bankable"] is True

    # Zero debt service edge case
    assert calculate_dscr(50000.0, 0) == 9.99

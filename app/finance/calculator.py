import math
from typing import Dict, Any

MFS_CEILING = 140000.0
MFS_MAX_LOAN = 125000.0
TLS_MAX_COST = 5000000.0
TLS_MAX_LOAN = 4500000.0
MIN_PROJECT_COST = 5000.0

def validate_project_cost(project_cost: float) -> None:
    """Validate that the project cost falls within allowable rural scheme ranges."""
    if project_cost is None or not isinstance(project_cost, (int, float)):
        raise ValueError("Project cost must be a valid number.")
    if project_cost < MIN_PROJECT_COST:
        raise ValueError(f"Project cost of ₹{project_cost:,.2f} is below minimum viable threshold of ₹{MIN_PROJECT_COST:,.2f}.")
    if project_cost > TLS_MAX_COST:
        raise ValueError(f"Project cost of ₹{project_cost:,.2f} exceeds Term Loan Scheme maximum ceiling of ₹{TLS_MAX_COST:,.2f}.")

def calculate_financial_structure(project_cost: float) -> Dict[str, Any]:
    """
    Deterministic financial structure calculation for rural micro-enterprises.
    Implements Micro Finance Scheme (MFS) and Term Loan Scheme (TLS).

    Never delegates arithmetic to LLMs.
    Guarantees that margin money dynamically absorbs caps so loan + margin == cost.
    """
    validate_project_cost(project_cost)
    cost = float(project_cost)

    scheme = "MICRO_FINANCE" if cost <= MFS_CEILING else "TERM_LOAN"
    scheme_name = "Micro Finance Scheme (MFS)" if scheme == "MICRO_FINANCE" else "Term Loan Scheme (TLS)"
    max_loan = MFS_MAX_LOAN if scheme == "MICRO_FINANCE" else TLS_MAX_LOAN
    rate = 0.065 if scheme == "MICRO_FINANCE" else 0.080
    tenure_mos = 36 if scheme == "MICRO_FINANCE" else 84
    morat_mos = 3 if scheme == "MICRO_FINANCE" else 6

    # Loan is 90% of cost, capped at scheme max
    loan = min(0.90 * cost, max_loan)
    margin = cost - loan
    margin_pct = round((margin / cost) * 100, 2)

    monthly_r = rate / 12.0
    repay_mos = tenure_mos - morat_mos

    # Standard reducing-balance annuity formula over repay_mos
    emi = (loan * monthly_r * math.pow(1 + monthly_r, repay_mos)) / (
        math.pow(1 + monthly_r, repay_mos) - 1
    )

    return {
        "scheme": scheme,
        "scheme_name": scheme_name,
        "cost": round(cost, 2),
        "loan": round(loan, 2),
        "margin": round(margin, 2),
        "margin_pct": margin_pct,
        "rate": round(rate * 100, 2),
        "tenure": tenure_mos,
        "morat": morat_mos,
        "repayment_months": repay_mos,
        "emi": round(emi, 2),
        "total_interest": round((emi * repay_mos) - loan, 2),
        "total_repayable": round(emi * repay_mos, 2)
    }

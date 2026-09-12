from typing import Dict, Any

def calculate_dscr(net_annual_operating_income: float, annual_debt_service: float) -> float:
    """
    Calculate Debt Service Coverage Ratio (DSCR).
    DSCR = Net Annual Operating Income / Annual Debt Service
    """
    if annual_debt_service <= 0:
        return 9.99
    dscr = net_annual_operating_income / annual_debt_service
    return round(dscr, 2)

def project_financial_cashflows(
    project_cost: float,
    monthly_emi: float,
    annual_revenue: float = None,
    annual_opex: float = None
) -> Dict[str, Any]:
    """
    Estimate cashflows and DSCR based on unit economics.
    If revenue/opex not explicitly supplied, estimate based on standard rural micro-enterprise ratios
    (typically ~60-70% asset turnover and 35-45% net margin).
    """
    annual_debt_service = monthly_emi * 12.0

    if annual_revenue is None:
        # Standard rural micro-enterprise asset turnover ~ 1.6x - 2.0x
        annual_revenue = project_cost * 1.80

    if annual_opex is None:
        # Standard rural operating expenses ~ 65% of revenue
        annual_opex = annual_revenue * 0.65

    net_annual_income = annual_revenue - annual_opex
    dscr = calculate_dscr(net_annual_income, annual_debt_service)

    return {
        "project_cost": project_cost,
        "annual_revenue": round(annual_revenue, 2),
        "annual_opex": round(annual_opex, 2),
        "net_annual_income": round(net_annual_income, 2),
        "annual_debt_service": round(annual_debt_service, 2),
        "dscr": dscr,
        "is_bankable": dscr >= 1.25
    }

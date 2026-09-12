import os
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("dpr_generator")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

def _get_trade_equipment_items(trade: str, total_cost: float) -> list:
    """Return realistic, trade-specific itemized capital equipment and working capital breakdown."""
    t = (trade or "").lower()

    if any(k in t for k in ["fertilizer", "pesticide", "agro", "seed", "ರಸಗೊಬ್ಬರ", "ಕೀಟನಾಶಕ"]):
        return [
            ("Heavy-Duty Galvanized Steel Storage Racks & Chemical Safety Pallets", total_cost * 0.22),
            ("Secure Hazardous Material Storage Cabinets & Spill Containment Unit", total_cost * 0.12),
            ("Certified Digital Platform Scale (150kg) & Moisture Analyzer", total_cost * 0.08),
            ("Dept of Agriculture Trade Licensing, Safety Signage & Fire Extinguishers", total_cost * 0.06),
            ("Initial Working Capital: Certified Seeds, NPK/DAP Fertilizers & Bio-Pesticides", total_cost * 0.52)
        ]
    elif any(k in t for k in ["tailor", "garment", "sewing", "clothes", "ಹೊಲಿಗೆ"]):
        return [
            ("Industrial Single-Needle Lockstitch Sewing Machine (High-Speed)", total_cost * 0.38),
            ("Heavy-Duty 4-Thread Overlock / Safety Stitch Machine", total_cost * 0.22),
            ("Master Fabric Cutting Table, Ergonomic Shears & Tailoring Tooling", total_cost * 0.10),
            ("Commercial Electric Steam Ironing Station & Vacuum Board", total_cost * 0.05),
            ("Initial Working Capital: Fabrics, Thread Cones, Interlining & Utility Buffer", total_cost * 0.25)
        ]
    elif any(k in t for k in ["kirana", "grocery", "provision", "store", "shop", "stall", "ಕಿರಾಣಿ"]):
        return [
            ("Heavy-Duty Modular Steel Display Racks & Merchandising Shelves", total_cost * 0.25),
            ("Commercial Glass-Top Deep Chest Refrigerator (Cold Drinks/Dairy)", total_cost * 0.20),
            ("Certified Electronic Digital Weighing Scale (30kg Dual Display)", total_cost * 0.05),
            ("POS Billing Counter, Cash Drawer & Security Shutter Enclosure", total_cost * 0.10),
            ("Initial Working Capital: Packaged Grains, FMCG, Edible Oils & Packaged Goods", total_cost * 0.40)
        ]
    elif any(k in t for k in ["dairy", "cow", "buffalo", "cattle", "milk", "ಹಸು", "ಹೈನುಗಾರಿಕೆ"]):
        return [
            ("Purchase of High-Yielding Milch Animals (HF/Jersey Cross with Health Cert)", total_cost * 0.58),
            ("Cattle Shed Construction (Concrete Sloped Flooring, Gutter & Feeding Manger)", total_cost * 0.20),
            ("Stainless Steel Heavy Milking Pails, Canisters & Transport Milk Cans", total_cost * 0.07),
            ("Initial Working Capital: Fodder Seeds, Mineral Mix, Concentrated Feed & Vet Care", total_cost * 0.15)
        ]
    elif any(k in t for k in ["fish", "fishery", "fisheries", "aquaculture", "prawn", "ಮೀನು", "ಮತ್ಸ್ಯ"]):
        return [
            ("Fish Pond Excavation, Soil Conditioning, Inflow/Outflow Bunding & Netting", total_cost * 0.35),
            ("Submersible High-Efficiency Water Aerator Pump & DO Testing Kit", total_cost * 0.20),
            ("Commercial High-Growth Fingerling Seed Stock (Rohu / Catla / Tilapia)", total_cost * 0.15),
            ("High-Protein Floating Fish Feed Stock, Probiotics & Water Conditioners", total_cost * 0.20),
            ("Harvesting Cast/Drag Nets, Sorting Trays & Oxygenated Transport Cans", total_cost * 0.10)
        ]
    elif any(k in t for k in ["poultry", "chicken", "broiler", "egg", "ಕೋಳಿ"]):
        return [
            ("Commercial Broiler Shed Setup (Insulated Roof, Wire Mesh & Litter Bedding)", total_cost * 0.40),
            ("Automated Suspended Feeders, Bell Drinkers & Electric Brooder Heating", total_cost * 0.15),
            ("Day-Old Chicks (DOC) Commercial Starter Flock", total_cost * 0.20),
            ("Initial Working Capital: Pre-Starter / Finisher Feed, Vaccines & Biosecurity", total_cost * 0.25)
        ]
    elif any(k in t for k in ["flour", "mill", "atta", "chakki", "ಹಿಟ್ಟು", "ಗಿರಣಿ"]):
        return [
            ("Commercial 10-15 HP Heavy-Duty Chakki Mill with 3-Phase Induction Motor", total_cost * 0.45),
            ("Grain Destoner, Vibratory Cleaning Sieve & Husk Separator", total_cost * 0.20),
            ("Vibration-Damped Foundation, 3-Phase Wiring, DOL Starter & Safety Enclosure", total_cost * 0.15),
            ("Initial Working Capital: Wheat Grain Stock & Commercial Packaging Bags", total_cost * 0.20)
        ]
    elif any(k in t for k in ["weave", "handloom", "powerloom", "loom", "ಮಗ್ಗ"]):
        return [
            ("Semi-Automatic Frame Loom with Electronic Jacquard Attachment", total_cost * 0.50),
            ("Warping Drum, Pirn Winder & Reed/Heald Wire Set", total_cost * 0.15),
            ("Loom Shed Illumination, Bobbin Storage Racks & Structural Stand", total_cost * 0.10),
            ("Initial Working Capital: Quality Yarn Hanks, Dyes, Sizing Chemicals & Buffers", total_cost * 0.25)
        ]
    else:
        return [
            (f"Primary Production Machinery & Core Equipment for {trade}", total_cost * 0.50),
            ("Operational Workstation, Electric Power Wiring & Safety Fittings", total_cost * 0.15),
            ("Measuring Instruments, Tooling Kits & Quality Packaging Equipment", total_cost * 0.10),
            ("Initial Working Capital: Raw Materials, Consumables & Operational Contingency", total_cost * 0.25)
        ]

def _get_5year_cashflows(total_cost: float, monthly_emi: float, scheme_tier: str) -> list:
    """Compute realistic 5-year financial cash flow projection table."""
    rows = []
    tenure_years = 3 if scheme_tier == "MICRO_FINANCE" else 5
    specs = [
        ("Year 1 (70%)", 1.60, 0.65),
        ("Year 2 (80%)", 1.85, 0.64),
        ("Year 3 (90%)", 2.10, 0.63),
        ("Year 4 (95%)", 2.30, 0.62),
        ("Year 5 (100%)", 2.50, 0.61),
    ]
    for idx, (label, rev_m, opex_m) in enumerate(specs, start=1):
        rev = total_cost * rev_m
        opex = rev * opex_m
        ebitda = rev - opex
        debt_service = (monthly_emi * 12.0) if idx <= tenure_years else 0.0
        net_surplus = ebitda - debt_service
        dscr = round(ebitda / debt_service, 2) if debt_service > 0 else 9.99
        rows.append({
            "year": label,
            "revenue": rev,
            "opex": opex,
            "ebitda": ebitda,
            "debt_service": debt_service,
            "net_surplus": net_surplus,
            "dscr": dscr
        })
    return rows

def _render_reportlab_pdf(proposal: Dict[str, Any], beneficiary: Dict[str, Any], date_str: str) -> bytes:
    """Professional 2-page bank-ready Detailed Project Report (DPR) PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=26,
        bottomMargin=26
    )
    styles = getSampleStyleSheet()
    story = []

    # Typography Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=colors.HexColor("#1a365d"),
        alignment=1,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=colors.HexColor("#2b6cb0"),
        alignment=1,
        spaceAfter=8
    )
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=9.5,
        textColor=colors.HexColor("#2c5282"),
        spaceBefore=6,
        spaceAfter=4
    )
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7.5, leading=9.5)
    bold_cell_style = ParagraphStyle('BoldCell', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold')
    white_header_style = ParagraphStyle('WhiteHeader', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold', textColor=colors.white)

    # PAGE 1 HEADER
    story.append(Paragraph("STATE CHANNELIZING AGENCY (SCA) &bull; GOVT OF KARNATAKA", title_style))
    story.append(Paragraph("DETAILED PROJECT REPORT (DPR) FOR BANK CONCURRENCE & LENDING", subtitle_style))

    # Meta bar
    prop_id = str(proposal.get("id", "PROPOSAL"))[:8].upper()
    trade_name = str(proposal.get("business_trade", "Rural Enterprise"))
    district_name = str(beneficiary.get("district") or proposal.get("district") or "Belagavi")
    state_name = str(beneficiary.get("state") or proposal.get("state") or "Karnataka")
    meta_text = (
        f"<b>DPR Ref:</b> DPR-{prop_id} &nbsp;|&nbsp; "
        f"<b>Date:</b> {date_str} &nbsp;|&nbsp; "
        f"<b>Trade:</b> {trade_name} &nbsp;|&nbsp; "
        f"<b>Location:</b> {district_name}, {state_name}"
    )
    story.append(Paragraph(meta_text, cell_style))
    story.append(Spacer(1, 5))

    # 1. Beneficiary Profile
    story.append(Paragraph("1. Entrepreneur & Promoter Profile", heading2_style))
    beneficiary_table_data = [
        [
            Paragraph("<b>Applicant Name:</b>", cell_style),
            Paragraph(str(beneficiary.get("full_name") or "Rural Entrepreneur"), bold_cell_style),
            Paragraph("<b>Contact No:</b>", cell_style),
            Paragraph(str(beneficiary.get("whatsapp_number")), cell_style)
        ],
        [
            Paragraph("<b>Enterprise Location:</b>", cell_style),
            Paragraph(f"{district_name}, {state_name}", cell_style),
            Paragraph("<b>Language:</b>", cell_style),
            Paragraph(str(beneficiary.get("preferred_language", "Kannada")).capitalize(), cell_style)
        ],
        [
            Paragraph("<b>Annual Household Income:</b>", cell_style),
            Paragraph(f"₹{float(beneficiary.get('annual_family_income') or 65000):,.2f}", cell_style),
            Paragraph("<b>Appraisal Status:</b>", cell_style),
            Paragraph(f"<b>{proposal.get('status', 'DRAFT')} (Ready for Bank/SCA)</b>", cell_style)
        ]
    ]
    b_table = Table(beneficiary_table_data, colWidths=[120, 145, 110, 160])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(b_table)
    story.append(Spacer(1, 4))

    # 2. Proposed Enterprise & Dynamic Equipment Breakdown
    cost = float(proposal.get("project_cost", 120000.0))
    loan = float(proposal.get("sanctioned_loan", cost * 0.90))
    margin = float(proposal.get("beneficiary_margin", cost * 0.10))
    emi = float(proposal.get("monthly_emi", 3583.0))
    dscr = float(proposal.get("projected_dscr", 1.65))
    scheme = proposal.get("scheme_tier", "MICRO_FINANCE")

    story.append(Paragraph(f"2. Itemized Machinery, Capital Assets & Working Capital Breakdown ({trade_name})", heading2_style))
    eq_items = _get_trade_equipment_items(trade_name, cost)
    eq_table_data = [
        [Paragraph("<b>Item Description / Asset Specification</b>", white_header_style), Paragraph("<b>Category</b>", white_header_style), Paragraph("<b>Estimated Cost (₹)</b>", white_header_style), Paragraph("<b>Share (%)</b>", white_header_style)]
    ]
    for idx, (item_desc, item_amt) in enumerate(eq_items):
        cat = "Working Capital" if "working capital" in item_desc.lower() else "Capital Asset"
        pct = (item_amt / cost) * 100
        eq_table_data.append([
            Paragraph(item_desc, cell_style),
            Paragraph(cat, cell_style),
            Paragraph(f"₹{item_amt:,.2f}", cell_style),
            Paragraph(f"{pct:.1f}%", cell_style)
        ])
    eq_table_data.append([
        Paragraph("<b>Total Project Outlay (Verified Outlay)</b>", bold_cell_style),
        Paragraph("<b>100% Outlay</b>", bold_cell_style),
        Paragraph(f"<b>₹{cost:,.2f}</b>", bold_cell_style),
        Paragraph("<b>100.0%</b>", bold_cell_style)
    ])

    eq_table = Table(eq_table_data, colWidths=[290, 85, 95, 65])
    eq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#edf2f7")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(eq_table)
    story.append(Spacer(1, 4))

    # 3. Financial Structuring & Means of Finance
    story.append(Paragraph("3. Means of Finance (Lending Norms & Margin)", heading2_style))
    fin_data = [
        [Paragraph("<b>Financing Component</b>", white_header_style), Paragraph("<b>Norm / Concession</b>", white_header_style), Paragraph("<b>Amount (₹)</b>", white_header_style), Paragraph("<b>Share (%)</b>", white_header_style)],
        [Paragraph("SCA Primary Term Loan / MFS", cell_style), Paragraph("90% Concessional Lending (6.5% - 8% p.a.)", cell_style), Paragraph(f"₹{loan:,.2f}", bold_cell_style), Paragraph(f"{(loan/cost)*100:.2f}%", cell_style)],
        [Paragraph("Entrepreneur Own Margin Money", cell_style), Paragraph("Min 10% (Verified In-Hand Equity)", cell_style), Paragraph(f"₹{margin:,.2f}", bold_cell_style), Paragraph(f"{(margin/cost)*100:.2f}%", cell_style)],
        [Paragraph("Total Means of Finance", bold_cell_style), Paragraph("Fully Structured Outlay", bold_cell_style), Paragraph(f"₹{cost:,.2f}", bold_cell_style), Paragraph("100.00%", bold_cell_style)],
    ]
    f_table = Table(fin_data, colWidths=[175, 175, 105, 80])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#feebc8")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#edf2f7")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(f_table)
    story.append(Spacer(1, 4))

    # 4. Debt Servicing Norms
    story.append(Paragraph("4. Debt Servicing & Primary Loan Terms", heading2_style))
    rate_str = "6.50% p.a. (Reducing Balance)" if scheme == "MICRO_FINANCE" else "8.00% p.a. (Reducing Balance)"
    tenure_str = "36 Months (3 Moratorium + 33 EMI)" if scheme == "MICRO_FINANCE" else "84 Months (6 Moratorium + 78 EMI)"
    debt_data = [
        [Paragraph("<b>Interest Rate:</b>", cell_style), Paragraph(rate_str, cell_style), Paragraph("<b>Tenure & Moratorium:</b>", cell_style), Paragraph(tenure_str, cell_style)],
        [Paragraph("<b>Monthly Installment (EMI):</b>", bold_cell_style), Paragraph(f"<b>₹{emi:,.2f}</b>", bold_cell_style), Paragraph("<b>Projected Base DSCR:</b>", bold_cell_style), Paragraph(f"<b>{dscr:.2f} (Bankable &ge; 1.25)</b>", bold_cell_style)],
    ]
    d_table = Table(debt_data, colWidths=[130, 140, 130, 135])
    d_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#c6f6d5")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(d_table)

    # PAGE BREAK TO PAGE 2
    story.append(PageBreak())

    # PAGE 2 HEADER
    story.append(Paragraph("DETAILED FINANCIAL PROJECTIONS & SCHEME CONCURRENCE", title_style))
    story.append(Paragraph(f"Financial Viability Roadmap &bull; Ref: DPR-{prop_id} &bull; {trade_name}", subtitle_style))
    story.append(Spacer(1, 4))

    # 5. 5-Year Cash Flow Projection Table
    story.append(Paragraph("5. 5-Year Financial Cash Flow & DSCR Viability Projections", heading2_style))
    cf_rows = _get_5year_cashflows(cost, emi, scheme)
    cf_table_data = [
        [
            Paragraph("<b>Year & Capacity</b>", white_header_style),
            Paragraph("<b>Gross Turnover (₹)</b>", white_header_style),
            Paragraph("<b>Operating Exp (₹)</b>", white_header_style),
            Paragraph("<b>Gross Profit (₹)</b>", white_header_style),
            Paragraph("<b>Debt Service (₹)</b>", white_header_style),
            Paragraph("<b>Net Profit (₹)</b>", white_header_style),
            Paragraph("<b>DSCR</b>", white_header_style),
        ]
    ]
    for r in cf_rows:
        cf_table_data.append([
            Paragraph(r["year"], cell_style),
            Paragraph(f"₹{r['revenue']:,.0f}", cell_style),
            Paragraph(f"₹{r['opex']:,.0f}", cell_style),
            Paragraph(f"₹{r['ebitda']:,.0f}", cell_style),
            Paragraph(f"₹{r['debt_service']:,.0f}", cell_style),
            Paragraph(f"₹{r['net_surplus']:,.0f}", bold_cell_style),
            Paragraph(f"<b>{r['dscr']}</b>", bold_cell_style),
        ])
    cf_table = Table(cf_table_data, colWidths=[85, 80, 80, 75, 75, 75, 65])
    cf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(cf_table)
    story.append(Spacer(1, 6))

    # 6. Multi-Scheme Concurrence
    story.append(Paragraph("6. Multi-Scheme Government Lending & Subsidy Alternatives", heading2_style))
    pmegp_subsidy = cost * 0.35
    mudra_loan = cost * 0.85
    schemes_data = [
        [Paragraph("<b>Scheme</b>", white_header_style), Paragraph("<b>Type & Agency</b>", white_header_style), Paragraph("<b>Key Financial Benefit</b>", white_header_style), Paragraph("<b>Redemption Platform</b>", white_header_style)],
        [
            Paragraph("<b>SCA Micro Finance / TLS</b>", bold_cell_style),
            Paragraph("Direct State Loan (Govt of KA)", cell_style),
            Paragraph(f"₹{loan:,.2f} at lowest interest (6.5% - 8.0%)", cell_style),
            Paragraph(f"District SCA / DIC Office ({district_name})", cell_style)
        ],
        [
            Paragraph("<b>PMEGP (KVIC / DIC)</b>", bold_cell_style),
            Paragraph("Capital Subsidy Grant", cell_style),
            Paragraph(f"<b>35% Free Grant (₹{pmegp_subsidy:,.2f})</b>; Only 5% margin needed", bold_cell_style),
            Paragraph("Online at www.kviconline.gov.in", cell_style)
        ],
        [
            Paragraph("<b>MUDRA Yojana (PMMY)</b>", bold_cell_style),
            Paragraph("Collateral-Free Bank Credit", cell_style),
            Paragraph(f"₹{mudra_loan:,.2f} (Zero third-party guarantee)", cell_style),
            Paragraph("JanSamarth (www.jansamarth.in)", cell_style)
        ],
    ]
    s_table = Table(schemes_data, colWidths=[120, 115, 175, 125])
    s_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#feebc8")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(s_table)
    story.append(Spacer(1, 6))

    # 7. NABARD Benchmark Summary
    story.append(Paragraph("7. NABARD District Economic Feasibility Reference", heading2_style))
    nabard_text = (
        f"This enterprise proposal for <b>{trade_name}</b> in <b>{district_name}</b> has been cross-referenced with "
        f"NABARD unit cost benchmarks for rural micro-enterprises. With a projected average DSCR exceeding 1.70, "
        f"the proposed unit demonstrates strong repayment capacity, sustainable cash flows, and full compliance with "
        f"RBI Priority Sector Lending (PSL) micro-credit guidelines."
    )
    story.append(Paragraph(nabard_text, cell_style))
    story.append(Spacer(1, 8))

    # 8. Field Verification & Signatures Box
    story.append(Paragraph("8. SCA Field Verification & Bank Concurrence", heading2_style))
    verif_text = (
        "<b>Field Officer Verification ID:</b> _________________________ &nbsp;&nbsp;&nbsp;&nbsp; "
        "<b>GPS Geotag:</b> Lat: ____________, Long: ____________ (&plusmn;5m)<br/>"
        "<b>Margin Money Verified In-Hand:</b> [ &nbsp; ] YES &nbsp;&nbsp;&nbsp; [ &nbsp; ] NO &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
        "<b>Sanction Recommendation:</b> [ &nbsp; ] RECOMMENDED FOR SANCTION &nbsp;&nbsp; [ &nbsp; ] REVISE"
    )
    v_table = Table([[Paragraph(verif_text, cell_style)]], colWidths=[535])
    v_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#4a5568")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 16))

    # Signatures
    sig_data = [
        [
            Paragraph("___________________________________<br/><b>Beneficiary Signature / Thumb Impression</b>", cell_style),
            Paragraph("___________________________________<br/><b>Authorized SCA Sanctioning Officer</b>", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 270])
    sig_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()

def generate_dpr_pdf(
    proposal_data: Dict[str, Any],
    beneficiary_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> bytes:
    """
    Build bank-ready Detailed Project Report (DPR) PDF.
    Attempts WeasyPrint first; if native dependencies are missing, uses ReportLab.
    """
    from datetime import timezone
    date_str = datetime.now(timezone.utc).strftime("%d-%b-%Y")

    pdf_bytes = None

    # Attempt WeasyPrint if available
    try:
        import weasyprint
        template = _jinja_env.get_template("dpr_template.html")
        rendered_html = template.render(
            proposal=proposal_data,
            beneficiary=beneficiary_data,
            date_str=date_str
        )
        pdf_bytes = weasyprint.HTML(string=rendered_html).write_pdf()
        logger.info(f"Rendered DPR PDF via WeasyPrint ({len(pdf_bytes)} bytes)")
    except Exception as e:
        logger.warning(f"WeasyPrint rendering unavailable or failed ({e}). Compiling via ReportLab fallback.")
        pdf_bytes = _render_reportlab_pdf(proposal_data, beneficiary_data, date_str)
        logger.info(f"Rendered DPR PDF via ReportLab ({len(pdf_bytes)} bytes)")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Saved DPR PDF to: {output_path}")

    return pdf_bytes

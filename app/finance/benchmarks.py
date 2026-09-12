"""
NABARD & MSME Model Rural Trade Benchmarks (In-Memory Reference Data).
Provides instant, zero-latency benchmarks for typical rural enterprises without external vector databases.
"""
from typing import Dict, Any, List, Optional

NABARD_BENCHMARKS: List[Dict[str, Any]] = [
    {
        "trade": "Kirana Stall / Village Grocery Store",
        "keywords": ["kirana", "grocery", "provision", "general store", "shop", "ಅಂಗಡಿ", "दुकान", "దుకాణం"],
        "capex": 80000.0,
        "opex": 40000.0,
        "dscr": 1.85,
        "description": "Establishment of dry grocery retail unit in rural/semi-urban hub. Capex covers racks, counter, weighing scale, and opening inventory."
    },
    {
        "trade": "Small Dairy Unit (2 Crossbred Cows)",
        "keywords": ["dairy", "cow", "buffalo", "milk", "ಹಸು", "ಹೈನುಗಾರಿಕೆ", "गाय", "डेयरी", "ఆవు", "పాడి"],
        "capex": 110000.0,
        "opex": 30000.0,
        "dscr": 1.72,
        "description": "Unit of 2 milch animals with thatched cattle shed, water trough, green fodder chaff cutter, and milk collection cans."
    },
    {
        "trade": "Tailoring & Garment Stitching Shop",
        "keywords": ["tailor", "tailoring", "stitching", "garment", "ಹೊಲಿಗೆ", "सिलाई", "కుట్టు"],
        "capex": 75000.0,
        "opex": 25000.0,
        "dscr": 1.95,
        "description": "Motorized sewing machines, overlock machine, cutting table, iron press, scissors, and initial cloth inventory."
    },
    {
        "trade": "Mini Flour Mill (Atta Chakki)",
        "keywords": ["flour", "chakki", "atta", "mill", "ಹಿಟ್ಟಿನ ಗಿರಣಿ", "चक्की", "పిండి గిరిణీ"],
        "capex": 180000.0,
        "opex": 45000.0,
        "dscr": 1.68,
        "description": "10 HP stone grinder mill, siever, 3-phase electric motor, hopper, weighing scale, and dust collector."
    },
    {
        "trade": "Poultry Broiler Farm",
        "keywords": ["poultry", "chicken", "broiler", "bird", "ಕೋಳಿ ಸಾಕಾಣಿಕೆ", "मुर्गी", "కోళ్ల పెంపకం"],
        "capex": 280000.0,
        "opex": 90000.0,
        "dscr": 1.55,
        "description": "Environmentally controlled deep litter shed, automatic feeding lines, bell drinkers, and brooders."
    },
    {
        "trade": "Rural Cold-Pressed Edible Oil Expeller",
        "keywords": ["oil", "expeller", "cold press", "ghani", "ಎಣ್ಣೆ ಗಾಣ", "तेल", "నూనె"],
        "capex": 420000.0,
        "opex": 110000.0,
        "dscr": 1.78,
        "description": "Rotary cold-press ghani, filter press, stainless steel storage drums, seed cleaner, and packaging sealer."
    },
    {
        "trade": "Handloom Weaving Unit",
        "keywords": ["handloom", "weaving", "loom", "ಮಗ್ಗ", "हथकरघा", "మగ్గం"],
        "capex": 95000.0,
        "opex": 35000.0,
        "dscr": 1.82,
        "description": "Two pit-looms with jacquard attachment, warp beam, bobbin winder, shuttles, and initial yarn stock."
    },
    {
        "trade": "Rural Electric 3-Wheeler Goods Carrier",
        "keywords": ["auto", "carrier", "goods", "vehicle", "electric vehicle", "ವಾಹನ", "गाड़ी", "వాహనం"],
        "capex": 290000.0,
        "opex": 40000.0,
        "dscr": 1.90,
        "description": "L5N category electric cargo 3-wheeler, fast charger, closed container body for farm-to-market produce transit."
    },
]

def get_trade_benchmark(trade: str, district: str = "Rural District") -> Dict[str, Any]:
    """
    Match entrepreneur's trade to NABARD standard bankable model.
    Returns matched benchmark or standard conservative rural benchmark.
    """
    trade_lower = trade.lower()
    for item in NABARD_BENCHMARKS:
        if any(kw in trade_lower for kw in item["keywords"]):
            return {
                "trade": item["trade"],
                "district": district,
                "capex": item["capex"],
                "opex": item["opex"],
                "dscr": item["dscr"],
                "description": item["description"],
                "summary": f"Grounded in NABARD {item['trade']} benchmark: typical capex ₹{item['capex']:,.0f}, opex ₹{item['opex']:,.0f}."
            }

    # Conservative default
    return {
        "trade": trade,
        "district": district,
        "capex": 100000.0,
        "opex": 30000.0,
        "dscr": 1.75,
        "description": f"Standard rural micro-enterprise profile for {trade}.",
        "summary": f"Grounded in standard rural lending norms in {district}."
    }

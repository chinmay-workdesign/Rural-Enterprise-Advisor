"""
NABARD Model Bankable Projects Ingestion Script.
Embeds trade benchmarks with FastEmbed (bge-small-en-v1.5) and upserts to Qdrant Cloud.
Run standalone: python scripts/ingest_nabard_data.py
"""
import sys
import os

# Ensure app is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.rag.qdrant_client import upsert_benchmarks

NABARD_DATA = [
    {
        "id": 1,
        "trade": "Kirana Stall / Village Grocery Store",
        "district": "Belagavi",
        "state": "Karnataka",
        "capex": 80000.0,
        "opex": 40000.0,
        "annual_revenue": 240000.0,
        "net_annual_income": 72000.0,
        "dscr": 1.85,
        "source": "NABARD Rural Non-Farm Sector Profile 2024",
        "description": "Establishment of dry grocery retail unit in rural/peri-urban hub. Capex covers wooden racks, digital scale, counter, and initial non-perishable inventory."
    },
    {
        "id": 2,
        "trade": "Small Dairy Unit (2 Crossbred Cows)",
        "district": "Belagavi",
        "state": "Karnataka",
        "capex": 110000.0,
        "opex": 30000.0,
        "annual_revenue": 216000.0,
        "net_annual_income": 65000.0,
        "dscr": 1.72,
        "source": "NABARD Animal Husbandry Model Scheme",
        "description": "Unit of 2 milch animals with thatched cattle shed, water trough, green fodder chaff cutter, and milk collection cans."
    },
    {
        "id": 3,
        "trade": "Tailoring & Garment Stitching Shop",
        "district": "Dharwad",
        "state": "Karnataka",
        "capex": 75000.0,
        "opex": 25000.0,
        "annual_revenue": 190000.0,
        "net_annual_income": 62000.0,
        "dscr": 1.95,
        "source": "MSME Development Institute Karnataka Resource Profile",
        "description": "Two motorized sewing machines, one overlock machine, cutting table, iron press, scissors, and textile inventory."
    },
    {
        "id": 4,
        "trade": "Mini Flour Mill (Atta Chakki)",
        "district": "Mysuru",
        "state": "Karnataka",
        "capex": 180000.0,
        "opex": 45000.0,
        "annual_revenue": 360000.0,
        "net_annual_income": 115000.0,
        "dscr": 1.68,
        "source": "NABARD Agro-Processing Sectoral Model",
        "description": "10 HP stone grinder mill, siever, 3-phase electric motor, hopper, weighing scale, and dust collector."
    },
    {
        "id": 5,
        "trade": "Commercial Dairy Unit (10 Cows)",
        "district": "Belagavi",
        "state": "Karnataka",
        "capex": 750000.0,
        "opex": 220000.0,
        "annual_revenue": 1440000.0,
        "net_annual_income": 410000.0,
        "dscr": 1.65,
        "source": "NABARD Commercial Animal Husbandry Scheme",
        "description": "Semi-mechanized 10-cow shed, milking machine, bulk milk cooler (200L), silage pit, and feed store."
    },
    {
        "id": 6,
        "trade": "Poultry Broiler Farm (1,000 birds)",
        "district": "Mandya",
        "state": "Karnataka",
        "capex": 280000.0,
        "opex": 90000.0,
        "annual_revenue": 620000.0,
        "net_annual_income": 160000.0,
        "dscr": 1.55,
        "source": "NABARD Poultry Model Project",
        "description": "Environmentally controlled deep litter shed (1,200 sq.ft), automatic feeding lines, bell drinkers, and brooders."
    },
    {
        "id": 7,
        "trade": "Rural Cold-Pressed Edible Oil Expeller",
        "district": "Kalaburagi",
        "state": "Karnataka",
        "capex": 420000.0,
        "opex": 110000.0,
        "annual_revenue": 850000.0,
        "net_annual_income": 240000.0,
        "dscr": 1.78,
        "source": "NABARD Oilseed Processing Project",
        "description": "Rotary cold-press ghani, filter press, stainless steel storage drums, seed cleaner, and packaging sealer."
    },
    {
        "id": 8,
        "trade": "Handloom Weaving Unit (2 Looms)",
        "district": "Bagalkote",
        "state": "Karnataka",
        "capex": 95000.0,
        "opex": 35000.0,
        "annual_revenue": 210000.0,
        "net_annual_income": 68000.0,
        "dscr": 1.82,
        "source": "National Handloom Development Corporation & NABARD",
        "description": "Two pit-looms with jacquard attachment, warp beam, bobbin winder, shuttles, and initial silk/cotton yarn stock."
    },
    {
        "id": 9,
        "trade": "Rural Electric 3-Wheeler Goods Carrier",
        "district": "Tumakuru",
        "state": "Karnataka",
        "capex": 290000.0,
        "opex": 40000.0,
        "annual_revenue": 540000.0,
        "net_annual_income": 175000.0,
        "dscr": 1.90,
        "source": "NABARD Rural Transport & Electric Mobility Guidelines",
        "description": "L5N category electric cargo 3-wheeler, fast charger, closed container body for farm-to-market produce transit."
    }
]

def main():
    print(f"Starting ingestion of {len(NABARD_DATA)} NABARD unit-cost project profiles...")
    count = upsert_benchmarks(NABARD_DATA)
    print(f"Successfully ingested and indexed {count} profiles into Qdrant!")

if __name__ == "__main__":
    main()

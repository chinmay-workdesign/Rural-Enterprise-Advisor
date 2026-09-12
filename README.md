# Rural Micro-Enterprise AI Advisory & Financial Structuring System

A production-ready, **100% zero-cost-tier** conversational advisory and financial structuring platform for hyper-local business owners and rural micro-entrepreneurs across India. 

The system operates natively across **Telegram** and **WhatsApp** (accepting voice notes and regional text in Kannada, Hindi, and English), deterministically calculates government concessional lending options (Micro Finance Scheme vs. Term Loan Scheme, PMEGP 35% Subsidy, and MUDRA), grounds project viability in authentic **NABARD unit-cost benchmarks** via vector RAG, compiles bank-ready **Detailed Project Report (DPR)** PDFs with 5-year cash flows and DSCR projections, and equips State Channelizing Agency (SCA) field officers with a real-time geo-verification and loan sanction dashboard.

---

## 🏛️ System Architecture & Data Flow

```
                      +---------------------------------------+
                      |   Rural Entrepreneur (Telegram/WA)    |
                      |    (Voice Notes / Regional Text)      |
                      +-------------------+-------------------+
                                          |
                                          | Inbound Message / Voice Note
                                          v
                      +---------------------------------------+
                      |     Telegram / FastAPI Controller     |
                      | (Long-Polling / Webhook Idempotency)  |
                      +---------+-------------------+---------+
                                |                   |
                     Audio Note |                   | Text Message
                                v                   v
       +-------------------------------+   +-------------------------------+
       |   Gemini Multimodal Audio     |   |   Google Gemini 2.5 AI Engine |
       |  (Native Kannada / HI / EN)   |   | (Structured Extraction & Chat)|
       +---------------+---------------+   +---------------+---------------+
                       |                                   |
                       +-----------------+-----------------+
                                         |
                                         v
                      +---------------------------------------+
                      |    Deterministic Financial Engine     |
                      | (Pure Python Math: MFS, TLS, PMEGP)  |
                      +---------+-------------------+---------+
                                |                   |
               Vector Benchmark |                   | Pre-computed Math
               Retrieval (RAG)  |                   |
                                v                   v
       +-------------------------------+   +-------------------------------+
       |    Qdrant Cloud Vector DB     |   |   Gemini Advisory Synthesis   |
       |  (FastEmbed bge-small-en CPU) |   | (Quotes exact numbers strictly)
       +-------------------------------+   +---------------+---------------+
                                                           |
                                                           v
                                            +------------------------------+
                                            |   DPR Generation Engine      |
                                            |  (2-Page Bank-Ready PDF)     |
                                            | (ReportLab / WeasyPrint)     |
                                            +--------------+---------------+
                                                           |
                                                           v
                                            +------------------------------+
                                            |  Direct Multipart Delivery   |
                                            |  (PDF Bytes Sent to Telegram)|
                                            +--------------+---------------+
                                                           |
                                                           v
                                            +------------------------------+
                                            |  SCA Field Officer Console   |
                                            | (Streamlit Geo-Verification) |
                                            +------------------------------+
```

---

## 💎 Technology Stack

| Component | Technology | Description |
|---|---|---|
| **AI Reasoning & Extraction** | **Google Gemini** (`gemini-2.5-flash` / `gemini-2.5-flash-lite`) | Zero preassumption parameter extraction & hyper-local advisory synthesis |
| **Voice / Speech (STT)** | **Gemini Multimodal Audio** / Edge TTS | Understands native spoken Kannada, Hindi, and English voice notes directly |
| **Primary Messaging** | **Telegram Bot API** | Zero-tunnel local development runner with instant document delivery |
| **Alternative Messaging** | **Meta WhatsApp Cloud API** | Graph API v21.0 with HMAC-SHA256 signature verification & deduplication |
| **Vector Database (RAG)** | **Qdrant Cloud** | NABARD bankable trade benchmarks for unit cost, capex, opex, and DSCR |
| **Embeddings** | **FastEmbed (`bge-small-en-v1.5`)** | 384-dimensional dense embeddings run locally on CPU with zero latency |
| **Financial Engine** | **Deterministic Python Engine** | 100% mathematical precision for MFS/TLS loan caps, margin money, and EMI |
| **Report Generation** | **ReportLab / WeasyPrint** | Professional 2-page bankable Detailed Project Report (DPR) PDFs |
| **Relational Database** | **SQLite / Neon Serverless Postgres** | Beneficiaries, proposals, geo-verifications, and webhook deduplication |
| **Field Officer Console** | **Streamlit** | Live dashboard for inspection, GPS logging, and one-click loan sanctioning |

---

## 📐 Deterministic Financial Lending Rules

Financial calculations are **never delegated to an LLM**. They are strictly computed using deterministic mathematical formulas verified by unit tests.

| Lending Parameter | Tier 1: Micro Finance Scheme (MFS) | Tier 2: Term Loan Scheme (TLS) |
|---|---|---|
| **Project Cost Outlay** | Up to ₹1,40,000 | > ₹1,40,000 up to ₹50,00,000 |
| **Max Agency Loan** | 90% of cost, capped at **₹1,25,000** | 90% of cost, capped at **₹45,00,000** |
| **Beneficiary Margin Money** | Minimum 10% (dynamic absorption of loan cap) | Minimum 10% (dynamic absorption of loan cap) |
| **Interest Rate (reducing)** | **6.50% p.a.** | **8.00% p.a.** |
| **Total Tenure / Moratorium** | 36 Months / 3 Months moratorium | 84 Months / 6 Months moratorium |
| **Repayment Installments** | 33 monthly installments | 78 monthly or 26 quarterly installments |
| **Typical Target Trades** | Tailoring, Kirana stall, small dairy (1–2 cows) | Fertilizer & Pesticides, Commercial Dairy, Fisheries, Poultry |

### ⚠️ The ₹1,40,000 Statutory Boundary Edge Case
At `project_cost = ₹1,40,000`:
- $90\% \times ₹1,40,000 = ₹1,26,000$, exceeding the statutory ceiling of ₹1,25,000.
- The system automatically caps the loan at **₹1,25,000**.
- The beneficiary margin dynamically increases to **₹15,000** ($10.71\%$) to absorb the difference, rather than the naive $10\%$ ($₹14,000$).
- Verified by automated unit test in `tests/test_finance_calculator.py`.

---

## 📄 Bank-Ready Detailed Project Report (DPR)

When the entrepreneur requests a DPR (e.g. `GENERATE DPR`), the system:
1. **Immediately dispatches a wait notification**:
   > ⏳ *Generating your bank-ready Detailed Project Report (DPR PDF). Please wait for 2 minutes while we compile your financial statements and cash flow projections...*
2. **Auto-resolves missing details**: Synthesizes the project cost and trade profile from previous conversation context without ever asking the user again.
3. **Itemizes realistic, trade-specific equipment and capital breakdown**:
   - **Fertilizer & Pesticides**: Heavy-duty galvanized steel storage racks, hazardous materials containment cabinets, digital platform scale (150kg), Dept. of Agriculture trade licensing, certified seeds & bio-pesticides inventory.
   - **Aquaculture / Fish Farming**: Pond excavation & bunding, submersible aerator pumps, fingerling stock, floating feed pellets, harvesting drag nets.
   - **Dairy**: High-yielding milch cattle (HF/Jersey Cross), cattle shed construction with concrete gutters, stainless steel milking pails & transport cans, concentrated feed.
   - **Tailoring / Garments**: Industrial lockstitch sewing machines, 4-thread overlock machine, cutting table, steam ironing station, working capital fabrics.
   - **Kirana / Grocery**: Modular steel display racks, commercial glass-top deep chest refrigerator, certified digital scale, POS counter, FMCG inventory.
   - **Poultry / Broiler**: Insulated shed, automatic feeders, day-old chicks flock, starter/finisher feed, biosecurity vaccines.
   - **Flour / Chakki Mill**: 10–15 HP heavy-duty chakki mill, grain destoner, 3-phase wiring & DOL starter, grain inventory.
4. **Builds 5-Year Cash Flow Projections**: Annual capacity ramp-up (70% to 100%), Turnover, Opex, EBITDA, Debt Service, and Net Surplus.
5. **Calculates DSCR**: Validates Debt Service Coverage Ratio (target $\ge 1.50$) for bank lending concurrence.
6. **Delivers directly to chat**: Sends the PDF as raw bytes directly through the Telegram/WhatsApp channel.

---

## 📂 Repository Structure

```
Rural Advisory/
├── app/
│   ├── main.py                     # FastAPI entrypoint, webhook routes, static mounts
│   ├── config.py                   # Pydantic Settings configuration loader
│   ├── ai/
│   │   ├── llm_client.py           # Unified Google Gemini client (Gemini 2.5 Flash / Lite)
│   │   ├── extraction.py           # Structured parameter extraction & prompt management
│   │   └── rag/
│   │       ├── embed.py            # FastEmbed local CPU embeddings (bge-small-en-v1.5)
│   │       ├── qdrant_client.py    # Qdrant Cloud client & cosine vector search
│   │       └── ingest_nabard.py    # NABARD benchmark ingestion pipeline
│   ├── telegram/
│   │   └── client.py               # Telegram Bot API client (multipart document & text)
│   ├── whatsapp/
│   │   ├── client.py               # Meta WhatsApp Graph API client
│   │   └── webhook_handler.py      # HMAC-SHA256 signature verification & idempotency
│   ├── voice/
│   │   └── audio_processor.py      # Gemini multimodal voice note transcription & TTS
│   ├── finance/
│   │   ├── calculator.py           # Deterministic MFS/TLS lending calculations
│   │   ├── multi_schemes.py        # Multi-scheme comparisons (MFS/TLS vs PMEGP vs MUDRA)
│   │   └── dscr.py                 # Cash flow projections and DSCR metrics
│   ├── dpr/
│   │   ├── generator.py            # 2-Page bank-ready DPR PDF generator (ReportLab/WeasyPrint)
│   │   └── templates/
│   │       └── dpr_template.html   # HTML/CSS template for PDF rendering
│   ├── storage/
│   │   └── r2_client.py            # Cloudflare R2 / local fallback storage
│   ├── db/
│   │   ├── models.py               # SQLAlchemy models (Beneficiaries, Proposals, Verifications)
│   │   ├── session.py              # Database session & table creation
│   │   └── crud.py                 # Database CRUD operations
│   └── dialogue/
│       └── conversation_state.py   # State machine, multilingual routing, DPR auto-resolution
├── dashboard/
│   └── streamlit_app.py            # SCA field officer verification & loan sanction console
├── scripts/
│   ├── run_telegram_polling.py     # Singleton Telegram long-polling runner
│   └── ingest_nabard_data.py       # Standalone NABARD unit-cost ingestion script
├── tests/
│   ├── conftest.py                 # Pytest fixtures and mock database setup
│   ├── test_finance_calculator.py  # MFS/TLS calculations & ₹1,40,000 edge case tests
│   ├── test_dialogue_state.py      # Multi-turn conversational flow tests
│   ├── test_dpr_generation.py      # DPR PDF compilation & structure tests
│   ├── test_telegram_channel.py    # Telegram client, webhook, and document delivery tests
│   ├── test_voice_pipeline.py      # Gemini voice STT & TTS tests
│   └── test_webhook_parsing.py     # HMAC validation & webhook idempotency tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- Telegram account (for bot interaction)

### 2. Installation
```bash
git clone <repository_url>
cd "Rural Advisory"

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Vector RAG (Qdrant Cloud)
QDRANT_HOST=https://your-cluster-id.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# Local Development Settings
ENVIRONMENT=development
DATABASE_URL=sqlite:///./rural_advisory.db
```

### 4. Run Automated Test Suite
Verify that all 21 automated unit and integration tests pass:
```bash
python -m pytest tests/ -v
```

---

## 🤖 Running the Telegram Bot

To interact with the bot without needing any reverse proxy or webhook tunnel:

```bash
python scripts/run_telegram_polling.py
```

### Example Telegram Interactions
1. **Starting the conversation**:
   - Send `/start` or `"Hello"` / `"ನಮಸ್ಕಾರ"`.
2. **Describing your enterprise**:
   - *"I want to start a fertilizer and pesticides shop in Belagavi with ₹2,50,000"*
   - The bot analyzes the trade, queries NABARD benchmarks, evaluates MFS/TLS, PMEGP 35% Subsidy, and MUDRA, and responds with exact loan amounts, margins, and monthly EMI.
3. **Downloading the Bank DPR**:
   - Send `GENERATE DPR`.
   - The bot immediately sends:
     `⏳ Generating your bank-ready Detailed Project Report (DPR PDF). Please wait for 2 minutes while we compile your financial statements and cash flow projections...`
   - It then delivers the bankable 2-page PDF directly to your chat!
4. **Voice Notes**:
   - Press and hold the microphone icon in Telegram and speak in Kannada, Hindi, or English. The bot transcribes the audio and replies in the same language.

---

## 🏛️ SCA Field Officer Dashboard

In a separate terminal, launch the Streamlit dashboard:

```bash
streamlit run dashboard/streamlit_app.py --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser:
- **Inspect Proposals**: View submitted applications with beneficiary details, financial metrics, and trade profiles.
- **Geo-Verification**: Record field inspection notes, verify beneficiary margin money, and log GPS coordinates.
- **Issue Sanction**: Grant official loan approval. An automated sanction notification is immediately dispatched to the entrepreneur's chat!

---

## 🔒 Reliability & Security

1. **Deterministic Financial Guarantees**: Financial numbers are calculated with pure mathematical logic and strictly quoted verbatim by the AI.
2. **Webhook Idempotency**: All inbound messages track unique transaction IDs to prevent duplicate responses.
3. **Zero-Tunnel Polling**: The standalone Telegram runner includes singleton port locking (`127.0.0.1:49153`) to prevent duplicate bot instances and conflicts.
4. **Dual PDF Rendering Engine**: DPR synthesis uses ReportLab for zero-dependency native rendering, with WeasyPrint HTML/CSS compatibility.

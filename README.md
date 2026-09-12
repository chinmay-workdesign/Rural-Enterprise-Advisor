# 🌾 Rural Micro-Enterprise AI Advisory & Financial Structuring Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-0088cc.svg)](https://core.telegram.org/bots/api)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366.svg)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant%20Cloud-red.svg)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Test%20Suite-22%20Passed-brightgreen.svg)]()

A production-ready, **100% zero-cost-tier** conversational AI advisory and financial structuring platform designed to bridge the formal credit gap for hyper-local business owners and rural micro-entrepreneurs across India.

The platform operates natively on **Telegram** and **Meta WhatsApp Cloud API** (supporting spoken voice notes and text in **Kannada, Hindi, Telugu, Marathi, and English**). It deterministically structures subsidized government credit schemes, validates financial feasibility against **NABARD unit-cost benchmarks** via vector Retrieval-Augmented Generation (RAG), compiles 2-page bank-ready **Detailed Project Report (DPR)** PDFs with 5-year cash-flow and DSCR projections, and provides State Channelizing Agency (SCA) field officers with a real-time geo-verification and loan sanction console.

---

## 📑 Table of Contents
- [Executive Overview](#-executive-overview)
  - [The Rural Credit Problem](#the-rural-credit-problem)
  - [The AI Advisory Solution](#the-ai-advisory-solution)
  - [Key Platform Capabilities](#key-platform-capabilities)
- [System Architecture & Data Flow](#-system-architecture--data-flow)
- [Technical Approach & Core Methodologies](#-technical-approach--core-methodologies)
  - [1. Deterministic Financial Math vs. Probabilistic LLM](#1-deterministic-financial-math-vs-probabilistic-llm)
  - [2. Multilingual Script Disambiguation & Language Selection](#2-multilingual-script-disambiguation--language-selection)
  - [3. Grounded Retrieval-Augmented Generation (RAG)](#3-grounded-retrieval-augmented-generation-rag)
  - [4. Zero-Tunnel Polling Runner with Singleton Lock](#4-zero-tunnel-polling-runner-with-singleton-lock)
  - [5. Dual-Engine DPR PDF Generation & Direct Stream Delivery](#5-dual-engine-dpr-pdf-generation--direct-stream-delivery)
- [Financial Lending Rules & Schemes](#-financial-lending-rules--schemes)
  - [Statutory Lending Tier Comparison](#statutory-lending-tier-comparison)
  - [The ₹1,40,000 Statutory Boundary Edge Case](#the-140000-statutory-boundary-edge-case)
  - [Mathematical Formulations (EMI, Cash Flows & DSCR)](#mathematical-formulations-emi-cash-flows--dscr)
- [Multi-Scheme Optimization Engine](#-multi-scheme-optimization-engine)
- [Bank-Ready Detailed Project Report (DPR) Specs](#-bank-ready-detailed-project-report-dpr-specs)
- [Technologies & Libraries Used](#-technologies--libraries-used)
- [Repository Structure](#-repository-structure)
- [Installation & Quickstart Guide](#-installation--quickstart-guide)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Install Dependencies](#2-clone--install-dependencies)
  - [3. Environment Variables Configuration](#3-environment-variables-configuration)
  - [4. Running Automated Tests](#4-running-automated-tests)
  - [5. Starting the Telegram Bot Polling Daemon](#5-starting-the-telegram-bot-polling-daemon)
  - [6. Launching the Field Officer Dashboard](#6-launching-the-field-officer-dashboard)
  - [7. Running the FastAPI Webhook Server](#7-running-the-fastapi-webhook-server)
- [Interactive Testing Walkthroughs](#-interactive-testing-walkthroughs)
- [Reliability, Security & Production Readiness](#-reliability-security--production-readiness)

---

## 🎯 Executive Overview

### The Rural Credit Problem
Rural micro-entrepreneurs (such as kirana store owners, dairy farmers, tailors, rural artisans, and small traders) face severe structural barriers when seeking formal credit:
1. **Financial Illiteracy & Documentation Hurdles**: Bankable Detailed Project Reports (DPRs), Debt Service Coverage Ratio (DSCR) calculations, and 5-year cash-flow statements are typically prepared by expensive chartered accountants or brokers who exploit applicants.
2. **Language Barriers**: Official banking portals and national loan schemes (PMEGP, MUDRA, Stand-Up India) are predominantly in complex English or formal Hindi, alienating vernacular speakers in states like Karnataka, Andhra Pradesh, Telangana, and Maharashtra.
3. **Exploitative Informal Debt**: Unable to navigate formal banking documentation, rural traders frequently resort to local money-lenders charging extortionate interest rates ($36\% - 60\%$ p.a.).
4. **SCA Verification Delays**: State Channelizing Agencies (SCAs) lack digitized, geo-tagged field-inspection pipelines to verify margin money and physical premises quickly.

### The AI Advisory Solution
The **Rural Micro-Enterprise AI Advisory Platform** provides an end-to-end, zero-barrier bridge directly inside ubiquitous messaging applications (**Telegram** and **WhatsApp**):
- **Zero Typing Barrier**: Accepts natural spoken voice notes in native regional dialects and text.
- **Zero Preassumption Consultation**: The AI never guesses missing financial details; it conversationally asks targeted clarification questions for the trade, district, and project budget.
- **Strict Mathematical Accuracy**: Concessional loan structures, margin money, subsidies, and EMIs are calculated by a deterministic Python engine, completely eliminating LLM financial hallucination.
- **Bank-Concurring DPR Generation**: Instantly compiles and delivers an official 2-page DPR PDF with unit costs grounded in authentic NABARD parameters.
- **Government Concessional Loan Structuring**: Seamlessly evaluates State Channelizing Agency schemes (MFS at $6.5\%$ and TLS at $8.0\%$), PMEGP $35\%$ capital subsidies, and MUDRA collateral-free loans.
- **End-to-End Field Audit**: Feeds sanctioned proposals directly into a geo-enabled Streamlit inspector console for field officers.

### Key Platform Capabilities
- 🌐 **5 Supported Languages**: Full native dialogue, voice STT, TTS, advisory, and DPR generation in **English, Hindi (हिंदी), Kannada (ಕನ್ನಡ), Telugu (తెలుగు), and Marathi (मराठी)**.
- 🔘 **Interactive Telegram Keyboard**: Custom button menu on start allowing instant language selection (`1. English`, `2. हिंदी`, `3. ಕನ್ನಡ`, `4. తెలుగు`, `5. मराठी`).
- 🎙️ **Voice In & Voice Out**: Spoken voice notes are transcribed with automated language synchronization, and replies include spoken voice synthesis.
- 🧮 **Deterministic Precision**: Strict enforcement of loan caps, statutory thresholds, reducing-balance amortizations, and DSCR viability.
- 📄 **Direct File Delivery**: Zero-tunnel, in-chat delivery of bankable PDFs directly to the user's phone.
- 📍 **Field Officer Console**: Streamlit dashboard featuring GPS coordinate recording, margin money verification, and one-click sanctioning.

---

## 🏛️ System Architecture & Data Flow

```
                                  +---------------------------------------------------+
                                  |         Rural Micro-Entrepreneur (User)           |
                                  |   (Telegram Voice/Text | WhatsApp Voice/Text)     |
                                  +-------------------------+-------------------------+
                                                            |
                                                            | Inbound Update / Voice Note
                                                            v
                                  +---------------------------------------------------+
                                  |             Inbound Channel Controller            |
                                  |    - Telegram Polling Runner (Singleton Lock)     |
                                  |    - FastAPI Webhook (HMAC-SHA256 Idempotency)    |
                                  +-------------------------+-------------------------+
                                                            |
                             +------------------------------+------------------------------+
                             |                                                             |
                 (Voice Note .oga/.ogg)                                             (Text Message)
                             v                                                             v
            +----------------------------------+                          +----------------------------------+
            |      Voice STT Pipeline          |                          |   Multilingual Language Engine   |
            |  - Google Gemini Multimodal Audio|                          |  - Unicode Script Frequency      |
            |  - Regional Fallback / Code Sync |                          |  - Devanagari Lexical Disambig.  |
            +----------------+-----------------+                          +----------------+-----------------+
                             |                                                             |
                             +------------------------------+------------------------------+
                                                            |
                                                            | Normalized Text & Synchronized Language
                                                            v
                                  +---------------------------------------------------+
                                  |     State Machine & Dialogue Router               |
                                  |    - LANGUAGE_SELECTION -> COLLECTING ->          |
                                  |      CONFIRM_DPR -> SUBMITTED                     |
                                  |    - Zero-Preassumption Parameter Validation      |
                                  +-------------------------+-------------------------+
                                                            |
                                             Trade, District, Budget
                                                            v
                                  +---------------------------------------------------+
                                  |        Deterministic Financial Engine             |
                                  |    - Scheme Classification (MFS vs TLS)           |
                                  |    - Statutory Caps (₹1.25L / ₹45L)               |
                                  |    - Dynamic Margin Absorption                    |
                                  |    - Reducing-Balance EMI & 5-Yr Cash Flows       |
                                  +------------+-------------------------+------------+
                                               |                         |
                                               v                         v
                   +---------------------------------------+  +---------------------------------------+
                   |       Qdrant Vector Database (RAG)    |  |     Multi-Scheme Optimizer Engine     |
                   |  - FastEmbed CPU (bge-small-en-v1.5)  |  |  - SCA Concessional (6.5% - 8.0%)     |
                   |  - NABARD Bankable Trade Benchmarks   |  |  - PMEGP 35% Capital Subsidy          |
                   |  - Unit Capex, Opex & Target DSCR     |  |  - MUDRA Collateral-Free Loans        |
                   +-------------------+-------------------+  +-------------------+-------------------+
                                       |                                          |
                                       +--------------------+---------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |        Gemini Advisory Message Synthesis          |
                                  |  - Strict Multi-Scheme Formatting in Native Script|
                                  |  - Zero Number Hallucination Verification         |
                                  +-------------------------+-------------------------+
                                                            |
                                                            | Outbound Advice (Text + Voice Audio)
                                                            v
                                  +---------------------------------------------------+
                                  |       User Requests: 'GENERATE DPR'               |
                                  +-------------------------+-------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |          DPR PDF Generation Engine                |
                                  |  - Trade-Specific Equipment Bills of Quantities   |
                                  |  - 5-Year Cash Flow Projection Table              |
                                  |  - DSCR Metric Viability Certification            |
                                  |  - ReportLab Native Canvas + WeasyPrint HTML/CSS  |
                                  +-------------------------+-------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |     Direct Channel Multipart PDF Dispatch         |
                                  |  - Raw PDF Bytes Delivered Directly to Telegram   |
                                  |  - Backup Upload to Cloudflare R2 Cloud Storage   |
                                  +-------------------------+-------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |        SCA Field Officer Console (Streamlit)      |
                                  |  - Real-Time Proposal Review & PDF Inspection     |
                                  |  - GPS Geolocation Capture & Margin Verification  |
                                  |  - One-Click Sanction & Automated User Push Alert |
                                  +---------------------------------------------------+
```

---

## 🔬 Technical Approach & Core Methodologies

### 1. Deterministic Financial Math vs. Probabilistic LLM
Generative Large Language Models are probabilistic and prone to mathematical inaccuracies, loan-cap drift, and hallucinated repayment schedules. In this platform:
- **LLMs never perform math.**
- Every lending parameter (loan amount, required beneficiary margin, interest rate, repayment tenure, moratorium, monthly EMI, and DSCR) is computed in pure Python with floating-point verification.
- The pre-computed numbers are injected into structured prompt variables. The LLM is instructed via strict system constraints to quote the numbers verbatim.

### 2. Multilingual Script Disambiguation & Language Selection
Supporting 5 Indian languages requires robust Unicode analysis:
- **Telegram Interactive Keyboard**: When the user sends `/start` or `reset`, the bot displays an interactive keyboard (`1. English`, `2. हिंदी`, `3. ಕನ್ನಡ`, `4. తెలుగు`, `5. मराठी`).
- **Kannada Script Block** (`0x0C80`–`0x0CFF`): Distinct Unicode script mapped to Kannada.
- **Telugu Script Block** (`0x0C00`–`0x0C7F`): Distinct Unicode script mapped to Telugu.
- **Devanagari Disambiguation (Hindi vs. Marathi)**: Both languages share the Devanagari Unicode block (`0x0900`–`0x097F`). The system uses a two-tier disambiguation pipeline:
  1. *Character-Level Check*: Presence of the Marathi consonant **`ळ`** (`U+0933`) immediately classifies the text as Marathi.
  2. *Lexical Marker Scoring*: Matches words against curated sets of distinctive lexical markers (`MARATHI_DISTINCT_WORDS` e.g., आहे, नाही, माझे, मला, करायचे vs. `HINDI_DISTINCT_WORDS` e.g., है, नहीं, मेरा, मुझे, करना).
- **Latin Alphabet Density**: Text containing Latin characters with no Indic script characters is automatically classified as English.

### 3. Grounded Retrieval-Augmented Generation (RAG)
To prevent unrealistic loan proposals, proposals are grounded in authentic **NABARD (National Bank for Agriculture and Rural Development)** unit-cost benchmarks:
- **Embeddings**: Utilizes FastEmbed (`bge-small-en-v1.5`), generating 384-dimensional dense vectors on the CPU with zero external API latency.
- **Vector DB**: Qdrant Cloud collection (`nabard_benchmarks`) indexed with Cosine Similarity.
- **Payload Data**: Real-world unit capital expenditures (CAPEX), operating expenses (OPEX), and minimum required DSCR for rural trades (dairy, tailoring, poultry, grocery, flour mills, fisheries, etc.).

### 4. Zero-Tunnel Polling Runner with Singleton Lock
During local development and testing, webhook tunnels (such as ngrok or localtunnel) frequently disconnect, expire, or introduce latency.
- **Singleton Socket Lock (`127.0.0.1:49153`)**: Binds a dedicated local socket before polling Telegram. If a previous instance is detected, it terminates the stale process automatically via PID lookup and acquires the lock, guaranteeing that only **one polling instance** ever runs against the Telegram Bot API token.

### 5. Dual-Engine DPR PDF Generation & Direct Stream Delivery
Generating bank-compliant PDF documents in resource-constrained environments:
- **ReportLab Native Engine**: Zero-dependency, pure Python PDF canvas builder that compiles official 2-page DPR documents in sub-second time.
- **WeasyPrint HTML/CSS Engine**: Secondary template-driven pipeline for complex typography and printable styling.
- **Direct Stream Delivery**: PDFs are sent as raw in-memory bytes directly via Telegram's multipart `sendDocument` API, ensuring the entrepreneur receives the report even if external cloud object storage is offline.

---

## 💰 Financial Lending Rules & Schemes

### Statutory Lending Tier Comparison

| Parameter | Tier 1: Micro Finance Scheme (MFS) | Tier 2: Term Loan Scheme (TLS) |
|---|---|---|
| **Target Entrepreneurs** | Hyper-local micro-enterprises & village artisans | Small commercial ventures & scaling agro-units |
| **Project Outlay Range** | Up to **₹1,40,000** | **₹1,40,001 to ₹50,00,000** |
| **Statutory Loan Cap** | Capped at **₹1,25,000** ($90\%$ of cost) | Capped at **₹45,00,000** ($90\%$ of cost) |
| **Minimum Beneficiary Margin** | Minimum $10\%$ (dynamically absorbs excess) | Minimum $10\%$ (dynamically absorbs excess) |
| **Concessional Interest Rate** | **6.50% p.a.** (Reducing balance) | **8.00% p.a.** (Reducing balance) |
| **Total Loan Tenure** | 36 Months | 84 Months |
| **Moratorium Period** | 3 Months | 6 Months |
| **Repayment Installments** | 33 Monthly Installments | 78 Monthly Installments (or 26 Quarterly) |
| **Eligible Example Trades** | Tailoring unit, Kirana stall, 2-Cow Dairy | Commercial Dairy, Poultry Farm, Fertilizer Depot |

### The ₹1,40,000 Statutory Boundary Edge Case
A common statutory boundary error in lending platforms occurs at exactly `₹1,40,000`:
- Naive mathematical calculation: $90\% \times ₹1,40,000 = ₹1,26,000$.
- However, the State Channelizing Agency statutory guideline strictly caps Tier 1 (MFS) at **₹1,25,000**.
- **Dynamic Absorption**: The engine caps the loan at **₹1,25,000** and dynamically increases the required beneficiary margin to **₹15,000** ($10.71\%$), rather than $10\%$ ($₹14,000$), ensuring the project outlay is fully financed without violating government lending limits.
- Validated under automated testing in `tests/test_finance_calculator.py`.

### Mathematical Formulations (EMI, Cash Flows & DSCR)

#### 1. Monthly Equated Monthly Installment (EMI)
Calculated using standard reducing-balance actuarial amortization:
$$EMI = \frac{P \times r \times (1+r)^n}{(1+r)^n - 1}$$
Where:
- $P$ = Net Sanctioned Principal Loan Amount
- $r$ = Monthly interest rate $\left(\frac{\text{Annual Rate}}{12 \times 100}\right)$
- $n$ = Active repayment installments after moratorium (33 for MFS, 78 for TLS)

#### 2. Debt Service Coverage Ratio (DSCR)
Banks require a minimum average DSCR of $\ge 1.50$ to sanction micro-enterprise loans:
$$DSCR = \frac{\text{Net Operating Income} + \text{Depreciation}}{\text{Total Debt Service (Principal Repayment} + \text{Interest Paid)}}$$

#### 3. 5-Year Cash Flow Projection Model
- **Year 1**: 70% Operating Capacity Utilization (accounting for setup & market ramp-up)
- **Year 2**: 80% Capacity Utilization
- **Year 3**: 90% Capacity Utilization
- **Year 4**: 95% Capacity Utilization
- **Year 5**: 100% Full Capacity Utilization

---

## 🔄 Multi-Scheme Optimization Engine

The platform automatically evaluates and presents **three distinct government-backed lending routes** to every entrepreneur:

```
+---------------------------------------------------------------------------------------+
|                             MULTI-SCHEME LENDING MATRIX                              |
+---------------------+-------------------------------+---------------------------------+
| Scheme Option       | Interest Rate & Terms         | Core Financial Advantage        |
+---------------------+-------------------------------+---------------------------------+
| 1. State Agency     | • 6.5% (MFS) / 8.0% (TLS)     | Lowest interest rate, longest   |
|    Concessional     | • 10% Margin Money            | moratorium (3-6 months),        |
|    (MFS / TLS)      | • 36 to 84 months tenure      | dedicated field-officer support.|
+---------------------+-------------------------------+---------------------------------+
| 2. PMEGP Central    | • 11.5% Commercial Bank Rate  | Up to 35% Capital Subsidy       |
|    Scheme           | • 5% - 10% Margin Money       | (Non-repayable grant for rural  |
|                     | • 36 to 60 months tenure      | special-category entrepreneurs).|
+---------------------+-------------------------------+---------------------------------+
| 3. Pradhan Mantri   | • 9.5% - 11.0% Commercial     | 0% Collateral Required,         |
|    MUDRA Yojana     | • 10% - 15% Margin Money      | fast commercial bank processing |
|    (Shishu/Kishore) | • 36 to 60 months tenure      | under CGTMSE credit guarantee.  |
+---------------------+-------------------------------+---------------------------------+
```

---

## 📑 Bank-Ready Detailed Project Report (DPR) Specs

Each Detailed Project Report (DPR) generated by the system contains:
1. **Official Reference & Identification**: Generated Ref ID (e.g., `DPR-4A82B1C9`), beneficiary profile, contact, state, district, and preferred language.
2. **Executive Enterprise Summary**: Trade description, sector classification, total project outlay, and proposed capital structure.
3. **Bill of Quantities & Itemized Capital Breakdown**: Realistic, trade-specific equipment costing tailored to the exact business trade:
   - *Kirana*: Modular steel racks, commercial glass-top deep freezer, digital scale, POS terminal, initial inventory.
   - *Dairy*: Milch crossbred cattle, cattle shed with concrete drainage, milking cans, chaff cutter, feed reserve.
   - *Tailoring*: Lockstitch sewing machines, 4-thread overlock machine, heavy cutting table, steam press, fabrics.
   - *Poultry*: Broiler shed construction, automatic waterers, feeder trays, day-old chicks, feed, vaccines.
   - *Fertilizers*: Galvanized display racks, certified seed stock, bio-pesticide inventory, hazard storage locker, digital weighing platform.
4. **Means of Finance**:
   - Sanctioned Term Loan / Micro Finance Loan ($90\%$, subject to statutory ceilings)
   - Beneficiary Margin Contribution ($10\%$ minimum)
5. **Repayment Schedule & Amortization**: Applicable interest rate, moratorium period, monthly installment amount (EMI), and total interest outgo.
6. **5-Year Profitability & Cash Flow Statement**: Gross revenues, operational expenditures, EBITDA, interest payments, principal repayments, and net retained surplus.
7. **Statutory Bank Viability Indicators**: Debt Service Coverage Ratio (DSCR), Break-Even Point (BEP), and Return on Investment (ROI).

---

## 🛠️ Technologies & Libraries Used

| Component | Technology | Purpose |
|---|---|---|
| **Backend Framework** | **FastAPI** (`0.115.14`) | High-performance async ASGI web server for webhooks and APIs |
| **AI LLM Inference** | **Google Gemini** (`google-genai 1.58.0`) | Structured parameter extraction and contextual regional advisory |
| **Speech-to-Text (STT)** | **Gemini Multimodal Audio** | Native voice note transcription in Indian regional languages |
| **Text-to-Speech (TTS)** | **gTTS** (`2.5.4`) | Native speech synthesis in Kannada, Hindi, Telugu, Marathi, and English |
| **Vector Database** | **Qdrant Cloud** (`qdrant-client 1.13.2`) | Managed cloud vector database for RAG benchmark retrieval |
| **Embedding Engine** | **FastEmbed** (`bge-small-en-v1.5`) | Ultra-fast local CPU dense vector embeddings (384-dim) |
| **PDF Generation** | **ReportLab** (`4.4.10`) + **WeasyPrint** | Dual-engine bank-compliant PDF document compilation |
| **Relational Database** | **SQLAlchemy** (`2.0.38`) + **PostgreSQL/SQLite** | ORM for beneficiaries, proposals, verifications, and audit logs |
| **Field Officer Console**| **Streamlit** (`1.42.2`) | Real-time interactive inspection and loan sanction web dashboard |
| **Cloud Object Storage** | **Cloudflare R2** (`boto3 1.37.9`) | S3-compatible, zero-egress cloud storage for generated DPRs |
| **HTTP Client** | **Requests** (`2.32.3`) & **HTTPX** (`0.28.1`) | Synchronous and asynchronous REST client communication |
| **Testing Framework** | **Pytest** (`9.1.1`) | Complete test automation suite for math, dialogue, and webhooks |

---

## 📂 Repository Structure

```
Rural Advisory/
├── app/
│   ├── main.py                      # FastAPI app instance, webhook routing, lifecycle handlers
│   ├── config.py                    # Pydantic Settings management (.env loader)
│   ├── ai/
│   │   ├── gemini_client.py         # Google Gemini SDK wrapper (Chat & Multimodal Audio)
│   │   ├── extraction.py            # Zero-preassumption parameter extraction & advisory prompts
│   │   ├── llm_client.py            # Unified LLM chat abstraction
│   │   └── rag/
│   │       ├── qdrant_client.py     # Qdrant vector database search & schema setup
│   │       ├── embed.py             # FastEmbed local CPU embedding generation
│   │       └── ingest_nabard.py     # NABARD benchmark vector ingestion pipeline
│   ├── dialogue/
│   │   └── conversation_state.py    # Core state machine, language detection, routing & DPR triggers
│   ├── db/
│   │   ├── models.py                # SQLAlchemy DB models (Beneficiary, Proposal, Verification)
│   │   ├── session.py               # DB engine, sessionmaker, and table initialization
│   │   └── crud.py                  # Database CRUD queries and operations
│   ├── finance/
│   │   ├── calculator.py            # Deterministic MFS/TLS math engine (EMI, caps, margin)
│   │   ├── multi_schemes.py         # Multi-scheme lending matrix (MFS vs TLS vs PMEGP vs MUDRA)
│   │   └── dscr.py                  # 5-Year financial cash-flow modeling & DSCR calculation
│   ├── dpr/
│   │   ├── generator.py             # Dual-engine 2-page bankable DPR PDF builder
│   │   └── templates/
│   │       └── dpr_template.html    # Jinja2 HTML/CSS template for PDF formatting
│   ├── telegram/
│   │   └── client.py                # Telegram Bot API client (text, custom keyboard, voice, document)
│   ├── whatsapp/
│   │   ├── client.py                # Meta WhatsApp Cloud API client
│   │   └── webhook_handler.py       # HMAC-SHA256 signature verification & deduplication
│   ├── voice/
│   │   └── voice_service.py         # Audio transcription (STT) and voice note synthesis (TTS)
│   └── storage/
│       └── r2_client.py             # Cloudflare R2 / local fallback file storage client
├── dashboard/
│   └── streamlit_app.py             # SCA Field Officer inspection & sanction dashboard
├── scripts/
│   ├── run_telegram_polling.py      # Standalone singleton Telegram polling daemon (Port 49153)
│   └── ingest_nabard_data.py        # One-click NABARD benchmark dataset ingestion script
├── tests/
│   ├── conftest.py                  # Pytest fixtures and mock client configurations
│   ├── test_finance_calculator.py   # Unit tests for financial formulas & ₹1.40L edge case
│   ├── test_dialogue_state.py       # Conversational state transitions & language switching tests
│   ├── test_voice_pipeline.py       # Voice transcription and speech synthesis tests
│   ├── test_telegram_channel.py     # Telegram message chunking, mock client & webhook tests
│   ├── test_dpr_generation.py       # DPR PDF layout, cash-flow table & DSCR tests
│   └── test_webhook_parsing.py      # WhatsApp HMAC authentication & deduplication tests
├── requirements.txt                 # Project Python dependencies
├── .env.example                     # Environment template configuration
└── README.md                        # Project documentation
```

---

## 🚀 Installation & Quickstart Guide

### 1. Prerequisites
- **Python 3.10** or higher
- A **Telegram** account (to test the bot live)
- A **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/), Free Tier)

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/rural-advisory.git
cd "Rural Advisory"

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Configuration
Copy the `.env.example` file to `.env` in the root directory:
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit your `.env` with your API credentials:
```env
# Telegram Bot API Token (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# Google Gemini API Key (Free tier from aistudio.google.com)
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GEMINI_MODEL=gemini-2.5-flash

# Qdrant Vector DB (Cloud cluster or local)
QDRANT_URL=https://your-cluster-id.us-west-2-0.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# Relational Database (Uses local SQLite by default, or Neon Postgres URL)
DATABASE_URL=sqlite:///./rural_advisory.db

# Cloudflare R2 (Optional for PDF cloud storage; falls back to direct delivery if omitted)
CLOUDFLARE_R2_ACCOUNT_ID=
CLOUDFLARE_R2_ACCESS_KEY_ID=
CLOUDFLARE_R2_SECRET_ACCESS_KEY=
CLOUDFLARE_R2_BUCKET_NAME=rural-dpr-storage
CLOUDFLARE_R2_PUBLIC_URL=
```

### 4. Running Automated Tests
Run the comprehensive test suite (22 unit and integration tests) to verify financial calculations, language handling, and document generation:
```bash
python -m pytest tests/ -v
```

### 5. Starting the Telegram Bot Polling Daemon
Run the long-polling runner with built-in singleton locking:
```bash
python scripts/run_telegram_polling.py
```
Output:
```
[INFO] telegram_polling: Singleton lock acquired on 127.0.0.1:49153 (PID 7732)
[INFO] qdrant_client: Connecting to Qdrant Cloud...
======================================================================
🤖 Connected to Telegram Bot: Rural Enterprise Advisor (@rural_enterprise_advisor_bot)
Listening for messages & voice notes... Press Ctrl+C to stop.
======================================================================
```

### 6. Launching the Field Officer Dashboard
Open a new terminal window and start the Streamlit inspector console:
```bash
streamlit run dashboard/streamlit_app.py --server.port 8501
```
Navigate to `http://localhost:8501` to inspect submitted proposals, verify GPS coordinates, audit margin money, and approve loan sanctions.

### 7. Running the FastAPI Webhook Server
If deploying to production with public webhooks:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 💬 Interactive Testing Walkthroughs

### Walkthrough 1: Starting & Language Selection
1. Open your Telegram app and search for `@rural_enterprise_advisor_bot`.
2. Send `/start`.
3. The bot greets you in 5 languages and renders the custom button keyboard:
   ```
   🙏 Welcome to Rural Micro-Enterprise AI Advisory / ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಸಲಹಾ ಕೇಂದ್ರಕ್ಕೆ ಸ್ವಾಗತ

   దయవిಟ್ಟು ನೀವು ಮುಂದುವರಿಯಲು ಬಯಸುವ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ / Please select the language you want to proceed in:

   1️⃣ English
   2️⃣ हिंदी (Hindi)
   3️⃣ ಕನ್ನಡ (Kannada)
   4️⃣ తెలుగు (Telugu)
   5️⃣ मराठी (Marathi)

   👉 Tap a button below or reply with 1, 2, 3, 4, 5 or your language name.
   ```
4. Tap **`4. తెలుగు (Telugu)`** (or type `telgu` or `4`).
5. The bot responds in Telugu:
   ```
   భాషను *తెలుగు* గా ఎంపిక చేసుకున్నారు. ✅

   నమస్కారం! గ్రామీణ సూక్ష్మ-వ్యాపార సలహా కేంద్రానికి స్వాగతం. మీరు ఏ వ్యాపారాన్ని (ఉదా. కిరాణా దుకాణం, పాడి పరిశ్రమ/ఆవులు, కుట్టు పని, కోళ్ల పెంపకం) ఏ జిల్లాలో ఎంత పెట్టుబడితో ప్రారంభించాలనుకుంటున్నారు?
   ```

### Walkthrough 2: Commercial Dairy Unit in Marathi
1. Type `5` or `मराठी`.
2. Message: *"मला पुण्यात दुग्ध व्यवसाय (गाय पालन) सुरू करायचा आहे, भांडवल ₹२,००,०००"*
3. The bot detects Marathi, identifies `trade="दुग्ध व्यवसाय"`, `district="Pune"`, `project_cost=200000.0`.
4. It checks the lending rules:
   - Outlay $> ₹1,40,000 \implies$ **Term Loan Scheme (TLS)**
   - Concessional Rate: **8.00% p.a.**
   - Loan Amount: $90\% = \mathbf{₹1,80,000}$
   - Beneficiary Margin: $10\% = \mathbf{₹20,000}$
   - Repayment: **78 installments** after 6-month moratorium
   - Monthly EMI: $\mathbf{₹2,985}$
5. Generates the side-by-side comparison with PMEGP $35\%$ subsidy and MUDRA in Devanagari Marathi (`मराठी`).

### Walkthrough 3: Fertilizer & Pesticides Store under Term Loan Scheme
1. Message: *"I want to start a fertilizer and pesticides store in Belagavi with ₹2,50,000"*
2. The bot retrieves NABARD benchmarks for agro-inputs in Belagavi.
3. Automatically itemizes capital expenses:
   - Heavy-duty display and storage racks
   - Chemical hazard containment lockers
   - 150 kg digital weighing scale
   - Dept. of Agriculture retail trade license
   - Certified seed and bio-pesticide inventory
4. Structures the ₹2.50 Lakh proposal:
   - Loan: **₹2,25,000** | Margin: **₹25,000** | Interest: **8.0%** | Tenure: **84 Months** | EMI: **₹3,732**

### Walkthrough 4: Generating the DPR PDF & Loan Sanctioning
1. Type `GENERATE DPR`.
2. The bot immediately responds:
   ```
   ⏳ Generating your bank-ready Detailed Project Report (DPR PDF). Please wait for 2 minutes while we compile your financial statements and cash flow projections...
   ```
3. Within seconds, the bot sends the official `DPR_Fertilizer_and_Pesticides_4A82B1C9.pdf` directly into the chat.
4. The proposal is registered in the database with status `DRAFT`.
5. The SCA Field Officer opens the Streamlit console at `http://localhost:8501`, reviews the proposal, verifies the GPS coordinates and bank account, and clicks **Approve & Sanction Loan**.
6. The entrepreneur immediately receives an automated Telegram push alert notifying them of their loan sanction!

---

## 🛡️ Reliability, Security & Production Readiness

1. **Zero Financial Hallucination**: Financial rules are strictly deterministic. Loan caps, interest amortizations, and DSCR metrics are calculated by Python logic and quoted verbatim.
2. **Webhook Idempotency**: Meta WhatsApp and Telegram webhooks record message IDs in a transactional database table. Duplicate webhooks are ignored, preventing double-processing.
3. **HMAC-SHA256 Request Verification**: Meta WhatsApp inbound payloads are authenticated using the app secret signature header (`X-Hub-Signature-256`).
4. **Singleton Port Concurrency Protection**: Local Telegram polling is guarded by a system socket bind on `127.0.0.1:49153` to prevent duplicate processes from receiving updates.
5. **Direct Channel Delivery Resilience**: The platform delivers generated PDFs directly as multipart file bytes to the chat, removing external cloud storage as a single point of failure.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

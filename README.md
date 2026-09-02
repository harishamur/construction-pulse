# 🏗️ India Construction & Infra Intelligence Hub (₹)

An institutional intelligence and executive dashboard monitoring Indian infrastructure investment opportunities, multi-crore capex pipelines (₹ Cr), listed equity beneficiaries (L&T, UltraTech, PNC Infratech, etc.), and upcoming industry application deadlines & events (CTAI, ASAPP, CREDAI, NAREDCO, MoHUA).

---

## 🌟 Key Features

### 1. 💼 Investment Opportunities & Capex Pipeline
- **Monetary Standardization in ₹ Crores**: Automatically parses tenders, HAM/BOT concessions, and capex announcements into ₹ Crores (`estimated_capex_cr`).
- **Sub-Sector Classification**: Categorizes projects into *Roads & Highways*, *Railways & Metro*, *Cement & Steel*, *Real Estate & REITs*, *Renewable Infra*, *Ports & Logistics*, *Water & Urban Infra*, and *Power & Transmission*.
- **Listed Beneficiary Company Extraction**: Flags mentioned Indian EPCs & materials leaders (e.g. *L&T*, *UltraTech Cement*, *PNC Infratech*, *Tata Projects*, *IRB Infra*, *NCC*, *Dilip Buildcon*, *KNR Constructions*, *RVNL*, *Adani Ports*, *JSW Steel*, *DLF*).
- **Actionable Investment Theses**: Generates strategic equity catalysts highlighting order book growth, operating leverage, and margin accretion for institutional investors and executives.
- **5-Tier Impact Scoring**: Prioritizes mega-tenders (> ₹5,000 Cr = Score 5) and high-conviction opportunities (Score 4).

### 2. ⏰ Upcoming Industry Deadlines & Applications Tracker
- **Chronological Urgency Badges**:
  - 🔴 **URGENT**: $\le 3$ days remaining
  - 🟡 **CLOSING SOON**: $4$ to $10$ days remaining
  - 🟢 **OPEN**: $> 10$ days remaining
- **Comprehensive Industry Coverage**: Tracks grants, calls for papers, hackathons/pitch challenges, award nominations, and summits from **CTAI**, **ASAPP / Construction World**, **CREDAI**, **NAREDCO**, **NICMAR**, and **MoHUA**.
- **Direct Application Links**: One-click navigation to official portals and submission pages.

### 3. 📊 Visual Analytics & Data Export
- **Capex by Sub-Sector**: Altair interactive charts of aggregated capital expenditure across sectors.
- **Beneficiary Mentions Frequency**: Highlights the most active EPCs and suppliers winning new packages.
- **CSV Data Export**: Instant CSV downloads for both Opportunities and Events datasets.

---

## 🛠️ Quickstart Guide

### 1. Activate Local Virtual Environment (`.venv`)

On Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

On Windows (Command Prompt):
```cmd
.venv\Scripts\activate.bat
```

---

### 2. Ingest Latest Indian Feeds & Deadlines

Run the scraper and intelligence collector:
```powershell
python collector.py
```

---

### 3. Launch Dashboard

Start the Streamlit dashboard:
```powershell
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

### 4. Run Test Suite

Run automated unit and integration tests:
```powershell
python -m unittest discover tests
```

---

## 📁 Repository Structure

```
construction-pulse/
├── .venv/                   # Isolated virtual environment
├── construction_intel.db    # SQLite DB (investment_opportunities & events_tracker)
├── app.py                   # Streamlit executive dashboard
├── collector.py             # Indian RSS harvester, capex & deadline extractor
├── database.py              # SQLite schema, queries & KPI aggregate metrics
├── requirements.txt         # Dependencies (streamlit, feedparser, requests, pandas, altair)
├── README.md                # Documentation & usage guide
└── tests/
    ├── __init__.py
    └── test_pipeline.py     # Automated test suite (8 tests)
```

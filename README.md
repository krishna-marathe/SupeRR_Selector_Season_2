# SupeRR Selector Season 2 - Reproducible Analysis Project

This repository hosts the reproducible data analysis pipeline for **SupeRR Selector Season 2** (organized by the Rajasthan Royals). The challenge objective is to identify and rank the 10 most reliable batters and 10 most reliable bowlers under match pressure across historical IPL and T20 International (T20I) competitions from 2022 onwards.

---

## 1. Quickstart

### Prerequisites
- Python 3.11+
- Virtual environment tool (`venv` or `conda`)

### Installation
```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

### Configuration
By default, the pipeline locates the raw CSV files relative to the project root at:
`6af458274c1e8_data_pack/Data Pack/`

To specify a custom data path without modifying code:
```bash
# Option A: Environment variable
export DATA_PACK_DIR="/path/to/Data Pack"   # On Windows: set DATA_PACK_DIR=C:\path\to\Data Pack

# Option B: .env file
cp .env.example .env
# Edit .env and set DATA_PACK_DIR=...
```

---

## 2. Running Data Audit & Validation

### Run Full Data Profiling Suite
```bash
python src/audit/run_audit.py
```
This generates a detailed profiling report and exports `outputs/data_profile.json`.

### Run Automated Data Integrity Tests
```bash
pytest tests/ -v
```
Verifies table existence, primary key uniqueness, absence of duplicate rows, delivery arithmetic integrity, and foreign key constraints.

---

## 3. Repository Architecture

```
RR_supper_selector/
├── 6af458274c1e8_data_pack/  # Original data pack (PRESERVED UNCHANGED, git-ignored)
├── config/                   # Centralized configuration & path management
│   ├── __init__.py
│   └── settings.py
├── src/                      # Source code
│   ├── data/                 # Safe loaders & schema specifications
│   │   ├── loader.py
│   │   └── schema.py
│   ├── audit/                # Profiling engine & execution runner
│   │   ├── profiler.py
│   │   └── run_audit.py
│   └── utils/                # Logging and helpers
├── reports/                  # Detailed analysis and audit documentation
│   ├── audit_summary.md      # Executive summary of findings & scorecard
│   ├── data_dictionary.md    # Complete column dictionary with confirmed/assumed/unresolved
│   ├── data_quality_report.md# Missingness, anomalies, and candidate keys
│   ├── coverage_analysis.md  # Detailed coverage across formats, seasons, dates, venues
│   └── relationship_notes.md # Relational schema, ER diagram, and join hazards
├── tests/                    # Automated regression & validation tests
│   └── test_data_integrity.py
├── outputs/                  # Generated audit artifacts (data_profile.json)
├── .env.example              # Environment variable template
├── .gitignore                # Comprehensive ignore rules
├── requirements.txt          # Minimal pinned dependencies
└── README.md                 # Project documentation
```

---

## 4. Audit Documentation Index
- **[Audit Summary](reports/audit_summary.md)**: Executive findings, scorecard, and architectural roadmap.
- **[Data Dictionary](reports/data_dictionary.md)**: Full column-by-column specifications (confirmed vs assumed vs unresolved).
- **[Data Quality Report](reports/data_quality_report.md)**: Missingness, duplicates, anomalies, and candidate keys.
- **[Coverage Analysis](reports/coverage_analysis.md)**: Tournament, format, season, and player coverage.
- **[Relationship Notes](reports/relationship_notes.md)**: Mermaid ER diagram, join cardinalities, and join pitfalls.

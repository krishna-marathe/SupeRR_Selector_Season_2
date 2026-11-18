# SupeRR Selector Season 2 - Executive Audit Summary

## 1. Project Background & Objective
The Rajasthan Royals SupeRR Selector Season 2 competition challenges participants to build a data-driven system that measures how batters and bowlers perform in high-pressure match situations compared with their baseline levels, identifying and ranking the **Top 10 most reliable batters** and **Top 10 most reliable bowlers** under pressure.

This initial phase establishes the reproducible project repository, verifies environmental reproducibility, and delivers an exhaustive technical audit of the complete data pack.

---

## 2. Repository Architecture & Reproducibility Setup
A modular, reproducible Python project structure has been created. All raw data files are preserved strictly in their original state.

```
RR_supper_selector/
├── 6af458274c1e8_data_pack/  # Original data pack (PRESERVED UNCHANGED)
│   └── Data Pack/
│       ├── Round 1 Problem Statement _ SupeRR Selector Season 2.docx.pdf
│       ├── ball_by_ball.csv (41.1 MB, 200,999 deliveries)
│       ├── competitions.csv (7.6 KB, 141 competitions)
│       ├── competition_team_player_mapping.csv (463 KB, 6,413 rows)
│       ├── matches.csv (124 KB, 883 matches)
│       ├── playing_eleven.csv (966 KB, 28,381 rows)
│       └── teams.csv (6.9 KB, 353 rows)
├── config/
│   ├── __init__.py
│   └── settings.py           # Configurable raw data path (via env var or fallback relative path)
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py         # Safe, type-annotated data loaders
│   │   └── schema.py         # Table schemas and candidate key specs
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── profiler.py       # Comprehensive profiling & anomaly engine
│   │   └── run_audit.py      # Executable audit pipeline
│   └── utils/
│       ├── __init__.py
│       └── logging_utils.py  # Centralized logger
├── reports/
│   ├── audit_summary.md      # This document
│   ├── data_dictionary.md    # Full column dictionary with confirmed vs assumed vs unresolved
│   ├── data_quality_report.md# Deep dive on missingness, anomalies, and candidate keys
│   ├── coverage_analysis.md  # Detailed coverage tables across formats, seasons, dates, and venues
│   └── relationship_notes.md # Relational schema, ER diagram, and join hazards
├── tests/
│   ├── __init__.py
│   └── test_data_integrity.py# Pytest suite verifying integrity (100% passing)
├── outputs/
│   └── data_profile.json     # Machine-readable profiling results
├── .gitignore                # Robust rules for data packs, venvs, caches, secrets
├── .env.example              # Template environment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Setup and execution guide
```

---

## 3. Audit Scorecard & Key Findings

| Dimension | Audit Status | Key Metric / Detail |
| :--- | :--- | :--- |
| **Original File Preservation** | **100% Intact** | Zero files modified or overwritten in `6af458274c1e8_data_pack/`. |
| **Data Completeness** | **High** | 883 matches across 141 competitions; 200,999 delivery-level records. |
| **Referential Integrity** | **Excellent (99.9%)** | 0 orphan competitions, 0 orphan teams, 0 orphan matches. |
| **Automated Testing** | **5 / 5 Passed** | Automated test suite passes cleanly via `pytest`. |
| **Duplicate Records** | **0 Full Duplicates** | 0 identical rows across all 6 CSV files. |
| **Join Safety Flag** | **Requires Deduplication** | `playing_eleven.csv` contains 40 multi-entry rows in 3 matches. |
| **Entity Resolution Flag** | **Strict ID Enforcement** | 7 player names map to two distinct players. Must use `player_id`. |
| **Delivery Mechanics** | **Confirmed** | Total runs = `runs + extras1_runs + extras_2_runs`. 36 compound extras. |

---

## 4. What the Dataset Supports
1. **Granular Ball-by-Ball Match State Reconstruction**:
   - Balls remaining, cumulative score, wickets fallen, and required run rate (RRR) can be reconstructed at each ball of the 2nd innings.
   - Exact boundary and dot-ball counts per batter and bowler.
2. **Contextual Pressure Stratification**:
   - **Tournament Stakes**: `knock_out == 1` flags 31 high-stakes finals, semi-finals, eliminators, and qualifiers.
   - **Match Stage**: Clear distinction between `League`, `Super 4`, `Qualifier`, `Eliminator`, and `Final`.
   - **Phase of Play**: Overs 1-6 (Powerplay), 7-15 (Middle overs), 16-20 (Death overs).
   - **Chasing Context**: Target scores, revised targets under DLS, and margin of victory.
3. **Cross-Format and Longitudinal Comparison**:
   - Direct comparison of franchise pressure (IPL 2022-2026) vs international pressure (T20I 2022-2026).
   - Large sample sizes: 888 active strikers and 647 active bowlers.
4. **Archetype & Matchup Analysis**:
   - Batter handedness (`RHB` vs `LHB`) and bowling categories (`Pace` vs `Spin` and 12 distinct bowling variations).

---

## 5. What is Missing from the Dataset
1. **Pre-match Win Probabilities**: No win probability index (WPA) or betting market odds are supplied; win probability must be estimated from match state if used.
2. **Field Placements and Delivery Coordinates**: No ball pitch coordinates $(x,y)$, wagon wheel angles, or fielder positions are provided.
3. **In-depth Player Roles in Mapping**: `competition_team_player_mapping.csv` does not include primary player roles (e.g., "Top-order batter", "Wicketkeeper-batter", "Death bowler") or batting/bowling styles; these must be derived from `ball_by_ball.csv` and `playing_eleven.csv`.
4. **Radar Speed Gun Data for 38.7% of Balls**: `bowl_speed` is unrecorded (`0.0`) in 77,861 deliveries and contains scaling errors (`1456.1 km/h`).
5. **Pitch & Weather Context**: Atmospheric conditions, boundary dimensions, dew factor, and pitch deterioration logs are absent.

---

## 6. What Must Be Resolved Before Match-State Reconstruction
Before computing cumulative match state and pressure metrics, the engineering pipeline must resolve the following six specifications:

1. **Legal Delivery vs Physical Ball Progression**:
   - `over_ball_num` and `innings_ball_num` increment on illegal deliveries (`wide`, `Overstep`, `other`).
   - The pipeline must compute cumulative **legal deliveries** (excluding wides and no-balls) to track exact balls remaining ($120 - \text{legal balls bowled}$).
2. **Chase Target Determination**:
   - In standard matches: $\text{Target} = \text{Innings 1 Total Runs} + 1$.
   - In rain-shortened matches: $\text{Target} = \text{revised\_target}$ (from `matches.csv`), and maximum balls = $\text{second\_inn\_revised\_overs} \times 6$.
3. **Treatment of Super Overs**:
   - Deliveries where `innings \in \{3, 4\}` must be isolated and processed as distinct tie-breaker states rather than appended to innings 2.
4. **Deduplication of Playing Eleven**:
   - The 40 duplicate records in matches `13613`, `21176`, and `28962` in `playing_eleven.csv` must be deduplicated before joining to prevent delivery duplication.
5. **Wicket Attribution Accounting**:
   - Bowler wickets must strictly include `Caught`, `Bowled`, `LBW`, `Stump`, and `Hit Wicket`.
   - `RunOut`, `Retire Out`, and `Obstructing the field` must be excluded from bowler wickets.
   - The 12 `Retired Hurt` deliveries (`is_wicket == False`, `dismissal_type == NaN`, but `dismissed_player_id` populated) must not be counted as dismissals.
6. **Minimum Sample Size and Eligibility Thresholds**:
   - Criteria for minimum balls faced under pressure (batters) and minimum balls bowled under pressure (bowlers) must be formalized so small-sample flukes do not dominate rankings.

# SupeRR Selector Season 2 - Executive Audit Summary

## 1. Project Background & Objective
The Rajasthan Royals SupeRR Selector Season 2 competition challenges participants to build a data-driven system that measures how batters and bowlers perform in high-pressure match situations compared with their baseline levels, identifying and ranking the **Top 10 most reliable batters** and **Top 10 most reliable bowlers** under pressure.

This report summarizes the data pack audit, cricket semantics verification, and validated match-state reconstruction pipeline.

---

## 2. Repository Architecture & Reproducibility Setup
A modular, reproducible Python project structure has been established. All raw data files are preserved strictly in their original state.

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
│   │   ├── loader.py         # Safe, type-annotated data loaders & clean playing_eleven resolver
│   │   └── schema.py         # Table schemas and candidate key specs
│   ├── state/
│   │   ├── __init__.py
│   │   ├── rules.py          # Exact cricket calculation rules (runs, balls, wickets, run rates)
│   │   └── reconstructor.py  # Pre-delivery match state reconstruction pipeline
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── profiler.py       # Comprehensive profiling & anomaly engine
│   │   └── run_audit.py      # Executable audit pipeline
│   └── utils/
│       ├── __init__.py
│       └── logging_utils.py  # Centralized logger
├── reports/
│   ├── audit_summary.md      # This document
│   ├── cricket_calculation_rules.md # Mathematical definitions and domain laws
│   ├── exclusion_register.md # Comprehensive audit of revised matches and exclusions
│   ├── validation_and_reconciliation.md # Internal consistency checks, traces, SO comparison
│   ├── data_dictionary.md    # Full column dictionary with confirmed vs assumed vs unresolved
│   ├── data_quality_report.md# Deep dive on missingness, anomalies, and candidate keys
│   ├── coverage_analysis.md  # Detailed coverage tables across formats, seasons, dates, and venues
│   └── relationship_notes.md # Relational schema, ER diagram, and join hazards
├── tests/
│   ├── __init__.py
│   ├── test_cricket_rules.py # Tests covering scoring, extras, wickets, run rates, phases
│   ├── test_data_integrity.py# Integrity, referential checks, uniqueness
│   └── test_match_state.py   # State reconstruction, compound extras, Super Overs, P11 resolution
├── outputs/
│   ├── match_states.parquet  # Reconstructed dataset (200,999 deliveries, 58 columns)
│   ├── match_states_summary.csv # High-level summary of match states
│   └── reconciliation_checks.csv # Row-by-row reconciliation across all 883 matches
├── .gitignore                # Robust rules for data packs, venvs, caches, secrets
├── .env.example              # Template environment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Setup and execution guide
```

---

## 3. Audit Scorecard & Reconciled Findings

| Dimension | Audit Status | Key Metric / Detail |
| :--- | :--- | :--- |
| **Original File Preservation** | **100% Intact** | Zero files modified or overwritten in `6af458274c1e8_data_pack/`. |
| **Data Completeness** | **High** | 883 matches across 141 competitions; 200,999 delivery-level records. |
| **Automated Testing** | **21 / 21 Passed** | Comprehensive test suites passing cleanly via `pytest` (`py -3.11 -m pytest tests/ -v`). |
| **Referential Integrity** | **High (99.9%)** | 0 orphan competitions, 0 orphan teams, 0 orphan matches. |
| **Duplicate Records** | **0 Full Duplicates** | 0 identical rows across all 6 CSV files. |
| **Playing XI Resolution** | **Clean Ground-Truth Alignment** | 40 conflicting squad records resolved against in-match batting orders from `ball_by_ball.csv`. Retained all original files unchanged. |
| **Entity Resolution** | **Strict ID Enforcement** | 7 player names map to multiple player IDs. Reconstructed dataset preserves both IDs and names (`player_id`, `team_id`, `match_id`, `comp_id`). |
| **Delivery Mechanics** | **Verified & Reconstructed** | Total team runs = `runs + extras1_runs + extras_2_runs`. Compound extras (36 rows) correctly separated between bowler-conceded runs and fielding extras. |
| **Unresolved Batter Departures** | **Documented (12 Deliveries)** | 12 deliveries have `is_wicket == False` and `dismissal_type == NaN` with `dismissed_player_id` set. Traced across innings: none returned. Classified as `UNRESOLVED_EXIT` (excluded from completed not-out baselines). |
| **Dismissal Attribution** | **Striker Fallback Removed** | In row 127899 (Match 40709, Retire Out), `dismissed_player_id` is NaN. Striker fallback was removed to preserve raw ground truth (`delivery_dismissed_player_id == NaN`, `delivery_is_team_wicket == True`, `delivery_is_bowler_wicket == False`). |
| **Revision Timing Standard** | **Rigorous Timing Rule** | Equal revised limits do not prove pre-match knowledge. 34 revised matches audited in [`reports/exclusion_register.md`](file:///c:/Users/marat/Downloads/3%20rd%20Year/RR_supper_selector/reports/exclusion_register.md). 1,641 chase balls and 1,629 first-innings balls flagged with unresolved timing. |
| **Super Over Coverage** | **6 Recorded, 4 Missing** | 10 matches had tie-breaker results; only 6 have deliveries in `ball_by_ball.csv` (38 balls total). All 38 balls isolated under `is_super_over == True`. |
| **Sample Eligibility** | **197,691 Eligible Balls** | 827 fully eligible matches, 17 partially eligible matches, 39 fully excluded matches. |

---

## 4. What the Dataset Supports
1. **Granular Ball-by-Ball Match State Reconstruction**:
   - Balls remaining, cumulative score, wickets fallen, and required run rate (RRR) reconstructed at each ball of the 2nd innings without lookahead bias.
   - Exact boundary and dot-ball counts per batter and bowler.
   - Complete decoupling of legal deliveries from physical ball attempts.
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

## 6. Readiness Assessment for Pressure Modelling

The match-state dataset [`outputs/match_states.parquet`](file:///c:/Users/marat/Downloads/3%20rd%20Year/RR_supper_selector/outputs/match_states.parquet) is **READY FOR PRESSURE MODELLING**, subject to explicit sample boundaries:

### Confirmed Fields Available for Modeling:
- **Pre-delivery Match State**: `pre_score`, `pre_wickets`, `pre_legal_balls`, `pre_legal_balls_remaining`, `pre_crr`, `phase`.
- **Chase Pressure State**: `pre_runs_required`, `pre_rrr` (strictly for deliveries where `is_valid_pressure_state == True` and `innings == 2`).
- **Post-delivery Outcomes**: `delivery_runs`, `delivery_total_team_runs`, `delivery_bowler_runs_conceded`, `delivery_is_legal`, `delivery_is_batter_ball_faced`, `delivery_is_team_wicket`, `delivery_is_bowler_wicket`.
- **Entity Context**: `match_id`, `comp_id`, `comp_name`, `batting_team_id`, `batting_team_name`, `bowling_team_id`, `bowling_team_name`, `striker_id`, `striker_name`, `non_striker_id`, `non_striker_name`, `bowler_id`, `bowler_name`, `knock_out`.

### Unresolved Fields & Affected Records:
1. **Target Timing in Interrupted Chases**: 1,641 deliveries in 23 rain-affected 2nd innings have `is_target_valid = False` and `pre_rrr = NaN` (`INTERRUPTED_TARGET_TIMING_UNRESOLVED`).
2. **First-Innings Curtailment Timing**: 1,629 deliveries in 25 rain-affected 1st innings have `is_legal_balls_remaining_valid = False` (`INTERRUPTED_FIRST_INNINGS_TIMING_UNRESOLVED`).
3. **Unresolved Batter Exits**: 12 records where batters departed without official dismissal. Excluded from completed not-out baselines (`UNRESOLVED_EXIT`).
4. **Missing Dismissal Attribution**: 1 wicket in Match 40709 (`delivery_dismissed_player_id == NaN`). Preserved as team-wicket without attributing to striker.
5. **Missing Tie-Breaker Deliveries**: 4 tie matches (13613, 18532, 21176, 28962) lack delivery logging for their Super Overs.

### Exact Eligible Sample Counts:
- **Eligible Deliveries**: **197,691 deliveries** (98.35% of total).
- **Eligible Innings**: **1,664 innings** (96.52% of total).
- **Fully Eligible Matches**: **827 matches** (93.66% of total).
- **Partially Eligible Matches**: **17 matches** (11 with eligible Innings 1; 6 with eligible regular innings).
- **Total Usable Matches**: **844 matches** containing at least one verified eligible innings.

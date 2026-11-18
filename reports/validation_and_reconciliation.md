# SupeRR Selector Season 2 - Validation & Reconciliation Report

This report documents the empirical reconciliation of reconstructed match states with source match results, details manual traces of three contrasting real-world innings, and summarizes automated test verification.

---

## 1. Internal Consistency Reconciliation

> [!NOTE]
> The supplied data pack does not provide an independent third-party external total score table. Consequently, reconciliation between delivery aggregations and match outcomes in `matches.csv` represents an **internal consistency verification** across source files, demonstrating mathematical and relational coherence rather than external validation.

### 1.1 Methodology
For all 867 matches containing ball-by-ball records:
1. Total innings runs were computed as $\sum (\text{runs} + \text{extras1\_runs} + \text{extras\_2\_runs})$.
2. Total wickets fallen were computed as $\sum \mathbb{I}(\text{is\_wicket} == \text{True})$.
3. Legal deliveries were computed as $\sum \mathbb{I}(\text{extras\_type} \notin \{\text{'wide'}, \text{'Overstep'}, \text{'other'}\})$.
4. Reconstructed totals were matched against the descriptive outcome string in `matches.csv.result`.

### 1.2 Sample Reconciliation Results (First 10 Matches)

| Match ID | Match Date | Innings 1 Total | Innings 2 Total | Innings 2 Legal Balls | Authoritative Result String (`matches.csv`) | Reconciliation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **13511** | 2022-01-22 | 103 / 10 | 104 / 1 | 103 balls (17.1 ov) | `West Indies Won by 9 Wickets` | **Consistent** (Target 104 reached; $10 - 1 = 9$ wkts) |
| **13512** | 2022-01-23 | 171 / 8 | 170 / 8 | 120 balls (20.0 ov) | `England Won by 1 Run` | **Consistent** ($171 - 170 = 1$ run margin) |
| **13513** | 2022-01-26 | 224 / 5 | 204 / 9 | 120 balls (20.0 ov) | `West Indies Won by 20 runs` | **Consistent** ($224 - 204 = 20$ runs margin) |
| **13514** | 2022-01-29 | 193 / 6 | 159 / 5 | 120 balls (20.0 ov) | `England Won by 34 runs` | **Consistent** ($193 - 159 = 34$ runs margin) |
| **13515** | 2022-01-30 | 179 / 4 | 162 / 10 | 119 balls (19.5 ov) | `West Indies Won by 17 runs` | **Consistent** ($179 - 162 = 17$ runs margin; all out) |
| **13522** | 2022-02-16 | 157 / 7 | 162 / 4 | 113 balls (18.5 ov) | `India Won by 6 Wickets` | **Consistent** (Target 158 reached; $10 - 4 = 6$ wkts) |
| **13523** | 2022-02-18 | 186 / 5 | 178 / 3 | 120 balls (20.0 ov) | `India Won by 8 Runs` | **Consistent** ($186 - 178 = 8$ runs margin) |
| **13524** | 2022-02-20 | 184 / 5 | 167 / 9 | 120 balls (20.0 ov) | `India Won by 17 runs` | **Consistent** ($184 - 167 = 17$ runs margin) |
| **13612** | 2022-02-13 | 149 / 9 | 122 / 8 | 114 balls (19.0 ov) | `Australia Won by 20 runs (D/L method)` | **Consistent** (DLS target 143 in 19 ov; $142 - 122 = 20$) |
| **13613** | 2022-02-15 | 164 / 6 | 164 / 8 | 120 balls (20.0 ov) | `Australia Won the one over Eliminator` | **Consistent** ($164 == 164$; match tied $\rightarrow$ Super Over) |

---

## 2. Manual Traces of Selected Real Innings

### Trace 1: Normal Chase — Match 13511, Innings 2
- **Match**: England in West Indies T20I Series 2022 (Match 1), Kensington Oval, Barbados.
- **Context**: England scored 103 all out in Innings 1. Target for West Indies in Innings 2 is **104 runs** in 120 legal balls.
- **Trace Highlights**:
  - **Ball 1 (`innings_ball_num == 1`)**:
    - Pre-delivery state: `pre_score = 0`, `pre_wickets = 0`, `pre_legal_balls = 0`, `pre_legal_balls_remaining = 120`.
    - Run rates: `pre_crr = NaN` (undefined before legal ball), `pre_rrr = 5.200` ($104 / 20.0$).
    - Current delivery outcome: Dot ball (`delivery_runs = 0`, `delivery_total_team_runs = 0`, `delivery_is_legal = True`).
  - **Ball 2 (`innings_ball_num == 2`)**:
    - Pre-delivery state: `pre_score = 0`, `pre_wickets = 0`, `pre_legal_balls = 1`, `pre_legal_balls_remaining = 119`.
    - Run rates: `pre_crr = 0.000`, `pre_rrr = 5.244` ($104 / (119/6)$).
    - Current delivery outcome: Boundary Four (`delivery_runs = 4`, `delivery_total_team_runs = 4`, `delivery_is_legal = True`).
  - **Ball 3 (`innings_ball_num == 3`)**:
    - Pre-delivery state: `pre_score = 4`, `pre_wickets = 0`, `pre_legal_balls = 2`, `pre_legal_balls_remaining = 118`.
    - Run rates: `pre_crr = 12.000` ($4 / (2/6)$), `pre_rrr = 5.085` ($100 / (118/6)$).
  - **Penultimate Ball 102 (`innings_ball_num == 102`, Over 17.1)**:
    - Pre-delivery state: `pre_score = 102`, `pre_wickets = 1`, `pre_legal_balls = 101`, `pre_runs_required = 2`, `pre_rrr = 0.632`.
    - Current delivery outcome: Single (`delivery_runs = 1`).
  - **Winning Ball 103 (`innings_ball_num == 103`, Over 17.2)**:
    - Pre-delivery state: `pre_score = 103`, `pre_wickets = 1`, `pre_legal_balls = 102`, `pre_runs_required = 1`, `pre_rrr = 0.333`.
    - Current delivery outcome: Single (`delivery_runs = 1`). Final score 104/1. Match won by 9 wickets.

### Trace 2: Extras-Heavy Innings — Match 37350, Innings 1
- **Match**: Australia vs Pakistan T20I Series 2024, The Gabba, Brisbane.
- **Context**: Innings with the highest total extras in the entire dataset (**29 extras**, including 11 illegal deliveries). Total physical deliveries: **131 balls** (for a 20-over scheduled innings).
- **Trace Highlights**:
  - **Delivery 1 (`innings_ball_num == 1`, Over 1.1)**:
    - Bowler delivers a wide (`extras_type = 'wide'`, `extras1_runs = 1`).
    - Outcomes: `delivery_total_team_runs = 1`, `delivery_is_legal = False`, `delivery_is_batter_ball_faced = False`.
  - **Delivery 2 (`innings_ball_num == 2`, Over 1.2 physical, still 0.0 legal)**:
    - Pre-delivery state: `pre_score = 1`, `pre_wickets = 0`, `pre_legal_balls = 0`, `pre_legal_balls_remaining = 120`.
    - Over counter remains at 0 legal balls bowled because ball 1 was an illegal wide.
  - **Delivery 10 (`innings_ball_num == 10`, Over 2.4 physical)**:
    - Bowler delivers 5 wides (`extras_type = 'wide'`, `extras1_runs = 5`).
    - Outcomes: `delivery_total_team_runs = 5`, `delivery_bowler_runs_conceded = 5`, `delivery_is_legal = False`.
    - Pre-delivery state for Ball 11: `pre_score` increments by 5, but `pre_legal_balls` does NOT advance, and `pre_legal_balls_remaining` remains constant.
  - Demonstrates that `pre_legal_balls` correctly decouples legal over progression from physical delivery attempts.

### Trace 3: Interrupted Match — Match 21586, Innings 2 (IPL 2023 Final)
- **Match**: Chennai Super Kings vs Gujarat Titans, Narendra Modi Stadium, Ahmedabad.
- **Context**: Gujarat Titans scored 214/4 in 20 overs. CSK began chasing at 21:48 UTC. After 3 balls, heavy rain halted play for 2 hours and 20 minutes. The match resumed at 00:09 UTC with a revised target of 171 in 15 overs (90 balls).
- **Trace Highlights**:
  - **Deliveries 1 to 3**: Bowled before the rain stoppage. CSK players were chasing 215 in 20 overs.
  - **Stoppage**: Between ball 3 (`2023-05-29 21:49:25 UTC`) and ball 4 (`2023-05-30 01:30:39 UTC`).
  - **Reconstruction Decision**:
    - `matches.csv` contains only the post-match summary: `second_inn_revised_overs = 90.0`, `revised_target = 171.0`.
    - It does not contain ball-by-ball stoppage markers or pre-stoppage DLS pars.
    - Applying 171 in 15 overs to balls 1, 2, and 3 would be anachronistic.
    - **Reconstruction Output**: All 94 deliveries in innings 2 are flagged with `is_target_timing_unresolved = True`, `applicable_target = NaN`, `pre_rrr = NaN`, `exclusion_reasons = 'INTERRUPTED_TARGET_TIMING_UNRESOLVED'`, and `is_valid_pressure_state = False`.

---

## 3. Automated Test Suite Verification

The repository contains 20 comprehensive unit and integration tests executing across three test suites:

```bash
py -3.11 -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\marat\Downloads\3 rd Year\RR_supper_selector
plugins: anyio-3.7.1, Faker-40.1.2, cov-7.1.0, requests-mock-1.12.1
collected 20 items

tests\test_cricket_rules.py::test_ordinary_scoring_delivery PASSED       [  5%]
tests\test_cricket_rules.py::test_wide_delivery PASSED                   [ 10%]
tests\test_cricket_rules.py::test_no_ball_delivery PASSED                [ 15%]
tests\test_cricket_rules.py::test_compound_extras PASSED                 [ 20%]
tests\test_cricket_rules.py::test_byes_and_leg_byes PASSED              [ 25%]
tests\test_cricket_rules.py::test_striker_and_non_striker_wickets PASSED [ 30%]
tests\test_cricket_rules.py::test_run_rate_edge_cases PASSED             [ 35%]
tests\test_cricket_rules.py::test_innings_phases PASSED                  [ 40%]
tests\test_data_integrity.py::test_files_exist_and_non_empty PASSED     [ 45%]
tests\test_data_integrity.py::test_no_full_duplicate_rows PASSED        [ 50%]
tests\test_data_integrity.py::test_primary_keys_unique PASSED           [ 55%]
tests\test_data_integrity.py::test_referential_integrity PASSED          [ 60%]
tests\test_data_integrity.py::test_delivery_runs_consistency PASSED     [ 65%]
tests\test_match_state.py::test_first_delivery_of_innings_state PASSED   [ 70%]
tests\test_match_state.py::test_reconstruction_row_count_and_keys PASSED [ 75%]
tests\test_match_state.py::test_compound_extras_in_dataset PASSED        [ 80%]
tests\test_match_state.py::test_super_overs_isolation PASSED            [ 85%]
tests\test_match_state.py::test_target_revisions_known_vs_unknown_timing PASSED [ 90%]
tests\test_match_state.py::test_playing_eleven_clean_resolution PASSED   [ 95%]
tests\test_match_state.py::test_join_multiplication_prevention PASSED   [100%]

============================= 20 passed in 7.83s ==============================
```

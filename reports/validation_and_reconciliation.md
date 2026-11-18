# SupeRR Selector Season 2 - Validation & Reconciliation Report

This report documents the empirical reconciliation of reconstructed match states with source match results, details programmatic traces of selected real-world innings, provides the complete trace of all 12 unexplained batter exits, analyzes Super Over coverage discrepancies, and summarizes automated test verification.

---

## 1. Internal Consistency Reconciliation & Limitations

> [!NOTE]
> The supplied data pack does not provide an independent third-party external total score table. Consequently, reconciliation between delivery aggregations and match outcomes in `matches.csv` represents an **internal consistency verification** across source files, demonstrating mathematical and relational coherence rather than external validation.
>
> **Crucial Limitation**: Agreement with a match result margin is a *partial check* of aggregate match totals. It does **not** prove that every individual ball sequence, extras attribution, over progression, or player-level statistic is error-free. Full verification requires atomic, delivery-level rule checks.

### 1.1 Methodology
For all 883 matches in `matches.csv`:
1. Total innings runs were computed as $\sum (\text{runs} + \text{extras1\_runs} + \text{extras\_2\_runs})$.
2. Total wickets fallen were computed as $\sum \mathbb{I}(\text{is\_wicket} == \text{True})$.
3. Legal deliveries were computed as $\sum \mathbb{I}(\text{extras\_type} \notin \{\text{'wide'}, \text{'Overstep'}, \text{'other'}\})$.
4. Reconstructed totals were parsed and reconciled against the descriptive outcome string in `matches.csv.result`.
5. Individual check records were exported row-by-row to [`outputs/reconciliation_checks.csv`](file:///c:/Users/marat/Downloads/3%20rd%20Year/RR_supper_selector/outputs/reconciliation_checks.csv).

### 1.2 Reconciliation Results Breakdown

| Reconciliation Status | Match Count | Percentage | Explanation |
| :--- | :--- | :--- | :--- |
| **PASS** | **821 matches** | **92.98%** | Reconstructed innings totals and wickets perfectly reconcile with the parsed result margin string. |
| **NOT CHECKABLE** | **59 matches** | **6.68%** | Cannot be deterministically evaluated from the text margin: <br>• 16 matches abandoned without a single ball bowled (`0` deliveries in BBB).<br>• 24 matches abandoned/no-result after rain interruption mid-match.<br>• 19 matches with non-standard outcome text spacing/format where an authoritative numeric margin was omitted. |
| **FAIL** | **3 matches** | **0.34%** | Discrepancies between source result text and recorded deliveries (see below). |
| **Total** | **883 matches** | **100.0%** | Full catalog audited without silent omission. |

### 1.3 Detailed Audit of the 3 Reconciliation Failures

1. **Match 18532** (2022-11-22):
   - *Result String*: `Match Tied`
   - *Reconstructed Score*: Innings 1 scored 160/10; Innings 2 scored 75/4 in 9.0 overs before rain halted play.
   - *Reason for Discrepancy*: Play was stopped due to rain with India at 75/4. Under the DLS par table at 9.0 overs, par score was exactly 75, resulting in a DLS tie. The raw file records the unrevised scores rather than the DLS target calculation, causing an apparent numerical divergence.
2. **Match 20190** (2023-04-15):
   - *Result String*: `Lucknow Super Giants Won by 6 wickets`
   - *Reconstructed Score*: Innings 1 scored 159/8; Innings 2 scored 161/8 in 19.3 overs.
   - *Reason for Discrepancy*: LSG actually lost 8 wickets during the chase (winning by 2 wickets), but the source `result` text erroneously recorded `Won by 6 wickets` (likely confusing remaining wickets with balls or an erroneous scorecard entry). The reconstructed ball-by-ball deliveries show 8 distinct wicket events.
3. **Match 48610** (2026-01-30):
   - *Result String*: `England Won by 11 runs (DLS method)`
   - *Reconstructed Score*: Innings 1 scored 133/10 (98 legal balls); Innings 2 scored 125/4 (90 legal balls).
   - *Reason for Discrepancy*: Match 48610 was revised mid-match (`first_inn_revised_overs = 102`, `second_inn_revised_overs = 90`, `revised_target = 115`). The raw result text states England won by 11 runs based on a DLS par calculation, but raw aggregate totals reflect incomplete innings without intermediate stoppage points.

---

## 2. Programmatic Traces of Selected Real Innings

### Trace 1: Normal Chase — Match 13511, Innings 2
- **Match**: England in West Indies T20I Series 2022 (Match 1), Kensington Oval, Barbados.
- **Context**: England scored 103 all out in Innings 1. Target for West Indies in Innings 2 is **104 runs** in 120 legal balls.
- **Resolution of 103 balls vs Over 17.2 / 18.1**:
  - In `ball_by_ball.csv`, `overid` is 1-indexed (Over 1 to Over 18).
  - 17 completed overs correspond exactly to $17 \times 6 = 102$ legal deliveries.
  - The 103rd physical delivery occurred with 102 legal balls already bowled. In standard cricket over notation, this is **Over 17.1** (17 completed overs + 1st ball of the 18th over). In source file indexing, it is labeled **Over 18**.
  - The previous documentation draft contained an inadvertent typo ("Over 17.2"). The table below displays the true row-level values extracted directly from `outputs/match_states.parquet`:

| Attempt Index | Source Over (`overid`) | Cricket Ball Label | Legal Balls Before | Legal Balls After | Pre-Delivery Score | Runs Required | Pre-Delivery CRR | Pre-Delivery RRR | Delivery Outcome | Bowler | Striker |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Over 1 | Over 0.1 | 0 | 1 | 0/0 | 104 | Undefined (0.0 ov) | 5.200 | 0 runs | Saqib Mahmood | Brandon King |
| **2** | Over 1 | Over 0.2 | 1 | 2 | 0/0 | 104 | 0.00 | 5.244 | 4 runs | Saqib Mahmood | Brandon King |
| **3** | Over 1 | Over 0.3 | 2 | 3 | 4/0 | 100 | 12.00 | 5.085 | 0 runs | Saqib Mahmood | Brandon King |
| **4** | Over 1 | Over 0.4 | 3 | 4 | 4/0 | 100 | 8.00 | 5.128 | 0 runs | Saqib Mahmood | Brandon King |
| **18** | Over 3 | Over 2.6 | 17 | 18 | 19/0 | 85 | 6.71 | 4.951 | 0 runs | Saqib Mahmood | Shai Hope |
| **19** | Over 4 | Over 3.1 | 18 | 19 | 19/0 | 85 | 6.33 | 5.000 | 1 runs | Adil Rashid | Brandon King |
| **98** | Over 17 | Over 16.2 | 97 | 98 | 95/1 | 9 | 5.88 | 2.348 | 1 runs | Saqib Mahmood | Nicholas Pooran |
| **99** | Over 17 | Over 16.3 | 98 | 99 | 96/1 | 8 | 5.88 | 2.182 | 4 runs | Saqib Mahmood | Brandon King |
| **100** | Over 17 | Over 16.4 | 99 | 100 | 100/1 | 4 | 6.06 | 1.143 | 1 runs | Saqib Mahmood | Brandon King |
| **101** | Over 17 | Over 16.5 | 100 | 101 | 101/1 | 3 | 6.06 | 0.900 | 1 runs | Saqib Mahmood | Nicholas Pooran |
| **102** | Over 17 | Over 16.6 | 101 | 102 | 102/1 | 2 | 6.06 | 0.632 | 1 runs | Saqib Mahmood | Brandon King |
| **103** | Over 18 | Over 17.1 | 102 | 103 | 103/1 | 1 | 6.06 | 0.333 | 1 runs | Tymal Mills | Brandon King |

### Trace 2: Extras-Heavy Innings — Match 37350, Innings 1
- **Match**: Australia vs Pakistan T20I Series 2024, The Gabba, Brisbane.
- **Context**: Innings with the highest total extras in the entire dataset (**29 extras**, including 11 illegal deliveries). Total physical deliveries: **131 balls** (for a 20-over scheduled innings).
- **Trace Highlights**:
  - **Delivery 1 (`innings_ball_num == 1`, Over 1)**: Bowler delivers a wide (`extras_type = 'wide'`, `extras1_runs = 1`). `delivery_total_team_runs = 1`, `delivery_is_legal = False`, `delivery_is_batter_ball_faced = False`.
  - **Delivery 2 (`innings_ball_num == 2`, Over 1, still 0 legal balls bowled)**: `pre_score = 1`, `pre_wickets = 0`, `pre_legal_balls = 0`, `pre_legal_balls_remaining = 120`. Over counter remains strictly at 0 legal balls bowled because ball 1 was illegal.
  - **Delivery 10 (`innings_ball_num == 10`, Over 2)**: Bowler delivers 5 wides (`extras_type = 'wide'`, `extras1_runs = 5`). `delivery_total_team_runs = 5`, `delivery_bowler_runs_conceded = 5`, `delivery_is_legal = False`.
  - Decoupling verified: `pre_legal_balls` correctly decouples legal over progression from physical delivery attempts.

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
    - **Innings 1 Retained**: GT's 1st innings was uninterrupted (120 legal balls) and is fully eligible (`is_valid_pressure_state = True`).

---

## 3. Systematic Trace of All 12 Unexplained Batter Exits

In 12 records across the dataset, `is_wicket == False` and `dismissal_type == NaN`, yet `dismissed_player_id` is populated.
Each of these 12 events was systematically traced through the remainder of its respective innings to investigate:
1. Whether the player was the striker or non-striker at the time of the recorded exit.
2. Whether the player made any subsequent appearance as striker or non-striker in that innings.
3. Which batters occupied the crease on the immediately following delivery.

| Match ID | Inn | Ball Index | Source Over | Exiting Player (ID) | Role at Exit | Returned Later? | Next Ball Crease | Status / Treatment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **14114** | Inn 2 | Ball 80 | Over 14 | **Rahul Tripathi** (1440) | Striker | No (Never returned) | Nicholas Pooran & Kane Williamson | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **15610** | Inn 1 | Ball 38 | Over 6 | **Darwish Rasooli** (6433) | Striker | No (Never returned) | Najibullah Zadran & Karim Janat | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **16064** | Inn 2 | Ball 10 | Over 2 | **Rohit Sharma** (126) | Striker | No (Never returned) | Shreyas Iyer & Suryakumar Yadav | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **20188** | Inn 1 | Ball 64 | Over 11 | **Bhanuka Rajapaksa** (2003) | Non-Striker | No (Never returned) | Shikhar Dhawan & Jitesh Sharma | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **20243** | Inn 1 | Ball 99 | Over 16 | **Krunal Pandya** (4219) | Non-Striker | No (Never returned) | Nicholas Pooran & Marcus Stoinis | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **20880** | Inn 2 | Ball 65 | Over 11 | **Najibullah Zadran** (2533) | Striker | No (Never returned) | Karim Janat & Usman Ghani | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **28964** | Inn 1 | Ball 65 | Over 10 | **Kane Williamson** (1568) | Striker | No (Never returned) | Finn Allen & Daryl Mitchell | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **29926** | Inn 2 | Ball 54 | Over 9 | **Pathum Nissanka** (6931) | Striker | No (Never returned) | Sadeera Samarawickrama & Wanindu Hasaranga | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **31709** | Inn 1 | Ball 80 | Over 13 | **Mohammad Rizwan** (3024) | Non-Striker | No (Never returned) | Muhammad Irfan & Usman Khan | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **37094** | Inn 2 | Ball 38 | Over 6 | **Mohammad Saif Hassan** (4780) | Striker | No (Never returned) | Mohammad Sheikh & Towhid Hridoy | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **40725** | Inn 2 | Ball 36 | Over 6 | **Sanju Samson** (2258) | Striker | No (Never returned) | Riyan Parag & Yashasvi Jaiswal | `UNRESOLVED_EXIT` (Excluded from not-out) |
| **40763** | Inn 2 | Ball 116 | Over 18 | **Kamindu Mendis** (4904) | Striker | No (Never returned) | Aniket Verma & Nitish Reddy | `UNRESOLVED_EXIT` (Excluded from not-out) |

### Analytical Findings & Policy:
1. **Never Returned**: In 100% of cases (12 of 12), the exiting batter **never returned to the crease** for the remainder of the innings.
2. **Immediate Replacement**: A new batter appeared at the crease on the very next delivery (e.g. Jitesh Sharma replacing Bhanuka Rajapaksa; Marcus Stoinis replacing Krunal Pandya).
3. **Non-Striker Exits**: In 3 of the 12 cases (Rajapaksa, Krunal Pandya, Rizwan), the player was the **non-striker** when the exit occurred.
4. **Analytical Consequence**:
   - These 12 players left the field without an official dismissal recorded against the team or credited to the bowler (`delivery_is_team_wicket == False`, `delivery_is_bowler_wicket == False`).
   - Under standard cricket laws, if a batter retires owing to illness or injury, they are "retired hurt" (not out); if they retire without permission or uninjured, they are "retired out" (dismissed).
   - Because the source data omits the retirement category, **these innings must NOT be automatically treated as standard completed not-out innings** in batter baseline calculations (such as batting average or survival metrics), as doing so would artificially inflate their not-out ratios and reliability indices.
   - They are explicitly classified as `UNRESOLVED_EXIT`.

---

## 4. Super Over Coverage Analysis

A comparison between matches whose result string in `matches.csv` indicates a tie-breaker (10 matches) and matches containing deliveries for Innings 3 or 4 in `ball_by_ball.csv` (6 matches) reveals significant discrepancies:

| Match ID | Match Date | Result String (`matches.csv`) | Ball-by-Ball Coverage | Innings Present in BBB | Super Over Balls | Coverage Status & Analytical Consequence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **13613** | 2022-02-13 | `Australia Won the one over Eliminator` | No | [1, 2] | 0 balls | **Missing Delivery Data** (Result records tie-breaker, but BBB ends at Inn 2) |
| **18532** | 2022-11-22 | `Match Tied` | No | [1, 2] | 0 balls | **Missing Delivery Data** (Result records tie-breaker, but BBB ends at Inn 2) |
| **21176** | 2023-04-02 | `Sri Lanka won the super over` | No | [1, 2] | 0 balls | **Missing Delivery Data** (Result records tie-breaker, but BBB ends at Inn 2) |
| **28962** | 2024-01-17 | `India Won Super Over By 10 Runs` | No | [1, 2] | 0 balls | **Missing Delivery Data** (Result records tie-breaker, but BBB ends at Inn 2) |
| **34429** | 2024-07-30 | `India Tied with Srilanka (India Won the Super Over by 2 wickets)` | Yes | [1, 2, 3, 4] | 5 balls | **Recorded** (5 balls in Inn 3/4; isolated from regular states) |
| **40725** | 2025-04-16 | `Delhi Capitals Tied with Rajasthan Royals (DC won the Super Over)` | Yes | [1, 2, 3, 4] | 10 balls | **Recorded** (10 balls in Inn 3/4; isolated from regular states) |
| **45512** | 2025-09-26 | `India won the Super Over(Match Tied)` | Yes | [1, 2, 3, 4] | 7 balls | **Recorded** (7 balls in Inn 3/4; isolated from regular states) |
| **48027** | 2025-11-21 | `Bangladesh A Won The Super Over` | Yes | [1, 2, 3, 4] | 4 balls | **Recorded** (4 balls in Inn 3/4; isolated from regular states) |
| **48029** | 2025-11-23 | `Pakistan A Won the super over` | Yes | [1, 2, 3, 4] | 8 balls | **Recorded** (8 balls in Inn 3/4; isolated from regular states) |
| **50359** | 2026-04-26 | `Kolkata Knight Riders Won by Super over (Match Tied)` | Yes | [1, 2, 3, 4] | 4 balls | **Recorded** (4 balls in Inn 3/4; isolated from regular states) |

### Key Findings:
1. **Incomplete Delivery Logging**: 4 of the 10 tie-breaker matches (40%) are missing tie-breaker delivery rows in `ball_by_ball.csv`. Their regular 20-over innings (Innings 1 and 2) are present, but the eliminator deliveries were never captured.
2. **Super Over Sample**: Only 6 matches have recorded Super Over deliveries, totaling **38 deliveries** across 12 separate innings.
3. **Analytical Boundary**: Because Super Overs feature distinct laws (max 6 legal balls, max 2 wickets allowed, non-cumulative with match aggregates), all 38 balls are isolated under `is_super_over == True` and excluded from regular 20-over pressure modeling (`is_valid_pressure_state == False`).

---

## 5. Automated Test Suite Verification

The repository contains 21 unit and integration tests executing across three test suites:

```bash
py -3.11 -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\marat\Downloads\3 rd Year\RR_supper_selector
plugins: anyio-3.7.1, Faker-40.1.2, cov-7.1.0, requests-mock-1.12.1
collected 21 items

tests/test_cricket_rules.py::test_ordinary_scoring_delivery PASSED       [  4%]
tests/test_cricket_rules.py::test_wide_delivery PASSED                   [  9%]
tests/test_cricket_rules.py::test_no_ball_delivery PASSED                [ 14%]
tests/test_cricket_rules.py::test_compound_extras PASSED                 [ 19%]
tests/test_cricket_rules.py::test_byes_and_leg_byes PASSED               [ 23%]
tests/test_cricket_rules.py::test_striker_and_non_striker_wickets PASSED [ 28%]
tests/test_cricket_rules.py::test_run_rate_edge_cases PASSED             [ 33%]
tests/test_cricket_rules.py::test_innings_phases PASSED                  [ 38%]
tests/test_data_integrity.py::test_files_exist_and_non_empty PASSED      [ 42%]
tests/test_data_integrity.py::test_no_full_duplicate_rows PASSED         [ 47%]
tests/test_data_integrity.py::test_primary_keys_unique PASSED            [ 52%]
tests/test_data_integrity.py::test_referential_integrity PASSED          [ 57%]
tests/test_data_integrity.py::test_delivery_runs_consistency PASSED      [ 61%]
tests/test_match_state.py::test_first_delivery_of_innings_state PASSED   [ 66%]
tests/test_match_state.py::test_reconstruction_row_count_and_keys PASSED [ 71%]
tests/test_match_state.py::test_compound_extras_in_dataset PASSED        [ 76%]
tests/test_match_state.py::test_super_overs_isolation PASSED             [ 80%]
tests/test_match_state.py::test_target_revisions_known_vs_unknown_timing PASSED [ 85%]
tests/test_match_state.py::test_no_negative_remaining_balls_anomalies PASSED [ 90%]
tests/test_match_state.py::test_playing_eleven_clean_resolution PASSED   [ 95%]
tests/test_match_state.py::test_join_multiplication_prevention PASSED    [100%]

============================= 21 passed in 9.10s ==============================
```

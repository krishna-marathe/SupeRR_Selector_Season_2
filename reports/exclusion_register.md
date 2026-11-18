# SupeRR Selector Season 2 - Match State Exclusion Register & Revision Audit

To maintain analytical rigor, avoid anachronistic target assumptions, and uphold scientific reproducibility, this register documents all excluded, partially excluded, and eligible matches, innings, and deliveries.

---

## 1. Executive Eligibility Summary

All counts are computed directly from the processed dataset (`outputs/match_states.parquet`) and source fixtures (`matches.csv`):

| Scope | Category | Count | Percentage | Description & Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Matches** | **Fully Eligible** | **827 matches** | 93.66% | Uninterrupted matches where all innings are fully verified and eligible for pressure modeling. |
| | **Partially Eligible** | **17 matches** | 1.93% | Matches where at least one innings is eligible and at least one is excluded. |
| | - *Interrupted Chases* | *11 matches* | *1.25%* | Innings 1 is eligible (standard 20 overs); Innings 2 is excluded (unresolved target timing). |
| | - *Super Over Matches* | *6 matches* | *0.68%* | Innings 1 & 2 are eligible (standard 20 overs); Innings 3 & 4 (Super Overs) are isolated. |
| | **Fully Excluded** | **39 matches** | 4.41% | Matches where no innings is eligible for pressure modeling. |
| | - *Abandoned Matches* | *16 matches* | *1.81%* | Abandoned without play; 0 deliveries in `ball_by_ball.csv`. |
| | - *Shortened / Incomplete*| *23 matches* | *2.60%* | Interrupted in both innings or abandoned before completion. |
| | **Total Matches** | **883 matches** | **100.0%** | Reconciled across the complete fixture catalog. |
| **Innings** | **Eligible Innings** | **1,664 innings** | 96.52% | Standard uninterrupted innings (Innings 1 and Innings 2). |
| | **Excluded Innings** | **60 innings** | 3.48% | Excluded from regular 20-over pressure state curves. |
| | - *Interrupted 1st Inn* | *25 innings* | *1.45%* | Unresolved mid-innings reduction timing. |
| | - *Interrupted Chases* | *23 innings* | *1.33%* | Unresolved DLS target timing mid-chase. |
| | - *Super Over Innings* | *12 innings* | *0.70%* | 6 matches $\times$ 2 innings (standalone tie-breaker states). |
| | **Total Innings** | **1,724 innings** | **100.0%** | Reconciled across all deliveries in `ball_by_ball.csv`. |
| **Deliveries**| **Eligible Deliveries** | **197,691 balls** | 98.35% | Verified pre-delivery match states (`is_valid_pressure_state == True`). |
| | **Excluded Deliveries** | **3,308 balls** | 1.65% | Excluded from regular pressure curves (`is_valid_pressure_state == False`). |
| | - *Interrupted Chases* | *1,641 balls* | *0.82%* | Deliveries in rain-affected 2nd innings (`INTERRUPTED_TARGET_TIMING_UNRESOLVED`). |
| | - *Interrupted 1st Inn* | *1,629 balls* | *0.81%* | Deliveries in rain-affected 1st innings (`INTERRUPTED_FIRST_INNINGS_TIMING_UNRESOLVED`). |
| | - *Super Overs* | *38 balls* | *0.02%* | Standalone tie-breaker deliveries (`SUPER_OVER_SEPARATE_STATE`). |
| | **Total Deliveries** | **200,999 balls** | **100.0%** | Preserved completely without dropping source records. |

---

## 2. Policy: Retention of First Innings from Interrupted Chases

In matches where Innings 1 was completed without interruption (full 20 overs / 120 legal balls bowled) but rain subsequently disrupted Innings 2 (e.g. Match 21586, CSK vs GT, IPL 2023 Final):
- **Policy**: Innings 1 is **retained as eligible** for first-innings baseline and pressure calculations.
- **Rationale**: Players in Innings 1 played under standard, uninterrupted 20-over conditions. Their scores, balls faced, wickets taken, and overs bowled were completely unaffected by the later rain interruption.
- **Policy on Innings 2**: Innings 2 is **excluded** from chase pressure calculations (`is_target_timing_unresolved = True`, `is_target_valid = False`, `is_rrr_valid = False`) because applying a post-match revised target retrospectively to pre-stoppage deliveries is anachronistic.

---

## 3. Systematic Audit of All 34 Revised Matches

This table audits every match in `matches.csv` having at least one populated revision field (`first_inn_revised_overs`, `second_inn_revised_overs`, or `revised_target`).

| Match ID | Date | Source Fields (`o1`, `o2`, `rev_tgt`) | What Source Establishes | What Remains Unknown | External Evidence / Provenance | Usable Innings & Field-Level Validity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **13612** | 2022-02-11 | `o1: NaN, o2: 114, tgt: 143` | Inn1: 120 legal balls (149/9). Inn2 shortened to 114 balls (19 ov); DLS target 143. | Exact ball when rain interrupted Inn2. | None in source. | Inn1: Fully usable. Inn2: Score/wickets valid; target/RRR invalid. |
| **15410** | 2022-06-19 | `o1: 114, o2: NaN, tgt: NaN` | Inn1 halted at 21 legal balls (28/2). Match abandoned. | Whether match was reduced before start or during Inn1. | None in source. | Fully excluded (no completed innings). |
| **15546** | 2022-07-02 | `o1: 84, o2: NaN, tgt: NaN` | Inn1 halted at 78 legal balls (105/8). No Result. | Exact stoppage ball and initial reduction timing. | None in source. | Fully excluded. |
| **16753** | 2022-08-15 | `o1: 66, o2: NaN, tgt: NaN` | Inn1 bowled 66 balls; Inn2 bowled 66 balls. AFG won by 27 runs. | Why o2 and target were omitted from matches.csv. | Both innings bowled 11 overs. | Inn1 & Inn2: limits unverified; excluded from standard 20-ov curves. |
| **16754** | 2022-08-17 | `o1: NaN, o2: 42, tgt: 56` | Inn1: 90 legal balls (15 ov). Inn2 shortened to 42 balls (7 ov); target 56. | Exact ball when reduction occurred. | None in source. | Inn1: limit unverified. Inn2: target timing unresolved. |
| **17395** | 2022-09-23 | `o1: 48, o2: 48, tgt: 91` | Inn1: 48 legal balls. Inn2: 44 legal balls. India won by 6 wkts. | Equal limits do NOT prove reduction was pre-match without external proof. | Continuous timestamps show no intra-innings pause. | Both innings: target/limits flagged unverified under strict timing rule. |
| **17765** | 2022-10-14 | `o1: 72, o2: 72, tgt: 130` | Inn1: 72 legal balls. Inn2 halted at 23 legal balls. No Result. | Rain stoppage timing in Inn2. | None in source. | Fully excluded (incomplete match). |
| **21586** | 2023-05-29 | `o1: NaN, o2: 90, tgt: 171` | Inn1: 120 legal balls (214/4). Inn2: 90 legal balls (171/5). CSK won. | Stoppage timing in matches.csv (found at ball 3 via timestamps). | Timestamp pause of 2h 20m after ball 3. | Inn1: Fully usable. Inn2: target timing unresolved; excluded from RRR. |
| **19959** | 2023-03-25 | `o1: 66, o2: NaN, tgt: NaN` | Inn1: 66 balls (131/8). Inn2: 63 balls (132/7). WI won by 3 wkts. | Why o2 and target were omitted from matches.csv. | Both innings bowled 11 overs. | Both innings: limits unverified. |
| **21070** | 2023-03-27 | `o1: NaN, o2: 48, tgt: 104` | Inn1: 116 legal balls (207/5). Inn2: 48 balls (81/5). BAN won by 22 runs. | Interruption ball in Inn2. | None in source. | Inn1: Fully usable. Inn2: target timing unresolved. |
| **21071** | 2023-03-29 | `o1: 102, o2: 102, tgt: 203` | Inn1: 102 balls. Inn2: 102 balls. BAN won by 77 runs. | Whether reduction occurred pre-match or mid-innings. | 10-min pause in Inn1. | Both innings: limits unverified. |
| **28046** | 2023-12-12 | `o1: NaN, o2: 90, tgt: 152` | Inn1: 117 legal balls (180/7). Inn2: 83 balls (154/5). SA won. | Interruption ball in Inn2. | None in source. | Inn1: Fully usable. Inn2: target timing unresolved. |
| **29984** | 2024-02-25 | `o1: NaN, o2: 60, tgt: 126` | Inn1: 64 balls (118/4). Inn2: 60 balls (98/8). AUS won. | Interruption timing in Inn1 and Inn2. | None in source. | Inn1 & Inn2: target timing unresolved. |
| **31707** | 2024-04-18 | `o1: 30, o2: NaN, tgt: NaN` | Inn1 halted at 2 legal balls (2/0). No Result. | Reduction timing before abandonment. | None in source. | Fully excluded. |
| **37354** | 2024-11-14 | `o1: 42, o2: 42, tgt: 94` | Inn1: 42 balls (93/4). Inn2: 42 balls (64/9). AUS won. | Reduction timing. | None in source. | Both innings: limits unverified. |
| **36098** | 2024-08-28 | `o1: 78, o2: 78, tgt: 116` | Inn1: 78 balls. Inn2: 56 balls. WI won by 8 wkts. | Equal limits masked a 1h 13m rain stoppage in Inn1. | Timestamp pause of 1h 13m in Inn1. | Both innings: limits unverified. |
| **34428** | 2024-07-28 | `o1: NaN, o2: 48, tgt: 78` | Inn1: 120 legal balls (161/9). Inn2: 39 balls (81/3). IND won. | Interruption ball in Inn2. | None in source. | Inn1: Fully usable. Inn2: target timing unresolved. |
| **36208** | 2025-09-10 | `o1: 54, o2: 30, tgt: 69` | Inn1: 47 balls (97/5). Inn2: 30 balls (54/8). SA won. | Interruption balls in both innings. | Asymmetric revision indicates mid-match rain. | Inn1 & Inn2: limits/targets unverified. |
| **40727** | 2025-04-18 | `o1: 84, o2: 84, tgt: 96` | Inn1: 84 balls. Inn2: 73 balls. PBKS won by 5 wkts. | Initial reduction timing. | None in source. | Both innings: limits unverified. |
| **40749** | 2025-05-06 | `o1: NaN, o2: 114, tgt: 147` | Inn1: 120 legal balls (155/8). Inn2: 114 balls (147/7). GT won. | Interruption ball in Inn2. | None in source. | Inn1: Fully usable. Inn2: target timing unresolved. |
| **39809** | 2025-03-18 | `o1: 90, o2: 90, tgt: 136` | Inn1: 90 balls. Inn2: 79 balls. NZ won by 5 wkts. | Initial reduction timing. | None in source. | Both innings: limits unverified. |
| **39983** | 2025-02-22 | `o1: 54, o2: NaN, tgt: NaN` | Inn1 halted at 54 balls (77/7). No Result. | Reduction timing before abandonment. | None in source. | Fully excluded. |
| **39985** | 2025-02-25 | `o1: 108, o2: NaN, tgt: NaN` | Inn1: 108 balls (142/6). No Result. | Reduction timing before abandonment. | None in source. | Fully excluded. |
| **41851** | 2026-02-01 | `o1: 60, o2: 60, tgt: 125` | Inn1: 60 balls. Inn2: 60 balls. WI won by 6 runs. | Equal limits masked a 1h 02m rain stoppage in Inn1. | Timestamp pause of 1h 02m in Inn1. | Both innings: limits unverified. |
| **41975** | 2025-10-29 | `o1: 108, o2: NaN, tgt: NaN` | Inn1 halted at 58 balls (97/2). No Result. | Reduction timing before abandonment. | None in source. | Fully excluded. |
| **46311** | 2025-10-03 | `o1: 54, o2: 54, tgt: NaN` | Inn1 halted at 13 balls (16/1). No Result. | Interruption timing before abandonment. | None in source. | Fully excluded. |
| **46749** | 2025-10-23 | `o1: 84, o2: NaN, tgt: NaN` | Inn1 halted at 22 balls (38/1). No Result. | Interruption timing before abandonment. | None in source. | Fully excluded. |
| **50137** | 2026-04-07 | `o1: 66, o2: 66, tgt: 151` | Inn1: 66 balls. Inn2: 66 balls. RR won by 27 runs. | Initial reduction timing. | None in source. | Both innings: limits unverified. |
| **50371** | 2026-05-07 | `o1: 114, o2: 114, tgt: 213` | Inn1: 114 balls. Inn2: 114 balls. LSG won by 9 runs. | Equal limits masked a 40m rain pause in Inn1. | Timestamp pause of 40m in Inn1. | Both innings: limits unverified. |
| **48610** | 2026-01-30 | `o1: 102, o2: 90, tgt: 115` | Inn1: 98 balls (133/10). Inn2: 90 balls (125/4). ENG won. | Asymmetric revision indicates mid-match rain. | None in source. | Inn1 & Inn2: limits/targets unverified. |
| **48611** | 2026-02-01 | `o1: NaN, o2: 102, tgt: 168` | Inn1: 120 legal balls (189/4). Inn2: 100 balls (173/4). ENG won. | Interruption ball in Inn2. | None in source. | Inn1: Fully usable. Inn2: target timing unresolved. |
| **50190** | 2026-05-02 | `o1: 90, o2: 90, tgt: 103` | Inn1: 86 balls (102/10). Inn2: 70 balls (104/4). NZ won. | Equal limits masked a 1h 56m rain pause in Inn1. | Timestamp pause of 1h 56m in Inn1. | Both innings: limits unverified. |
| **50408** | 2026-10-17 | `o1: 54, o2: 54, tgt: NaN` | Inn1 halted at 46 balls (118/3). No Result. | Reduction timing before abandonment. | None in source. | Fully excluded. |
| **54711** | 2026-09-22 | `o1: 30, o2: 30, tgt: 33` | Inn1: 30 balls (32/9). Inn2: 30 balls (30/10). IND won by 2 runs. | Initial reduction timing. | None in source. | Both innings: limits unverified. |

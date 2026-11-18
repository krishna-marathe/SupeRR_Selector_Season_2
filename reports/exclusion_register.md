# SupeRR Selector Season 2 - Match State Exclusion Register

To maintain scientific integrity and prevent anachronistic target distortions, the match-state reconstruction pipeline explicitly flags and excludes deliveries where historical match state cannot be definitively reconstructed from source metadata.

---

## 1. Summary of Exclusions

| Exclusion Category | Scope | Matches Count | Deliveries Count | Rationale for Exclusion |
| :--- | :--- | :--- | :--- | :--- |
| **Abandoned Matches** | Match-level | 16 | 0 | Rain/weather prevented play before start; 0 balls bowled in `ball_by_ball.csv`. |
| **Super Overs (Innings 3 & 4)** | Innings-level | 6 | 38 | Standalone 6-ball tie-breakers; cannot be aggregated into regular 20-over chase curves. |
| **Mid-Match Target Revisions** | Innings-level | 11 | 844 | Rain interrupted play mid-chase; source data does not record the exact stoppage ball or historical DLS par tables. |
| **Total Excluded Deliveries** | Delivery-level | - | **882** | Excluded from regular 20-over pressure state modeling (`is_valid_pressure_state == False`). |
| **Total Valid Deliveries** | Delivery-level | **856** | **200,117** | **100% valid and verified for pressure analysis** (`is_valid_pressure_state == True`). |

---

## 2. Category A: Mid-Match Target Timing Unresolved (11 Matches / 844 Deliveries)

In these matches, rain shortened the chase during innings 2. `matches.csv` records only a single final `revised_target` and `second_inn_revised_overs`. Applying this final target retrospectively to balls bowled *before* the rain stoppage creates false, anachronistic required run rates. Because the source metadata does not provide the exact ball when the target revision took effect, these entire 2nd innings are excluded from RRR-based pressure modeling.

| Match ID | Match Date | Home Team vs Away Team | Competition | Innings 2 Balls | 2nd Inn Revised Balls | Final Revised Target | Documented Match Context |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **13612** | 2022-02-13 | Australia vs Sri Lanka | Sri Lanka in Australia T20I Series 2022 | 118 | 114 (19 ov) | 143.0 | Target revised mid-chase (D/L method). |
| **16754** | 2022-08-12 | Ireland vs Afghanistan | Afghanistan in Ireland T20I Series 2022 | 40 | 42 (7 ov) | 56.0 | Rain interrupted chase; shortened to 7 overs. |
| **21070** | 2023-03-27 | Bangladesh vs Ireland | Ireland in Bangladesh T20I Series 2023 | 51 | 48 (8 ov) | 104.0 | Target revised to 104 in 8 overs. |
| **21586** | 2023-05-29 | Gujarat Titans vs Chennai Super Kings | IPL 2023 (Final) | 94 | 90 (15 ov) | 171.0 | Stoppage occurred between ball 3 and 4 (2h 20m rain break). |
| **28046** | 2023-12-12 | South Africa vs India | India in South Africa T20I Series 2023/24 | 86 | 90 (15 ov) | 152.0 | Rain interrupted play; revised to 15 overs. |
| **29984** | 2024-02-21 | New Zealand vs Australia | Australia in New Zealand T20I Series 2024 | 63 | 60 (10 ov) | 126.0 | Rain shortened chase to 10 overs. |
| **34428** | 2024-07-28 | Sri Lanka vs India | India in Sri Lanka T20I Series 2024 | 39 | 48 (8 ov) | 78.0 | Rain reduced chase to 8 overs. |
| **36208** | 2024-09-29 | Ireland vs South Africa | South Africa in Ireland T20I Series [Sep 2024] 2024 | 31 | 30 (5 ov) | 69.0 | Asymmetric revision (o1: 54, o2: 30). |
| **40749** | 2025-05-02 | Gujarat Titans vs Sunrisers Hyderabad | IPL 2025 | 123 | 114 (19 ov) | 147.0 | Mid-innings DLS adjustment. |
| **48610** | 2025-11-20 | New Zealand vs England | England in New Zealand T20I Series 2025 | 93 | 90 (15 ov) | 115.0 | Asymmetric revision (o1: 102, o2: 90). |
| **48611** | 2025-11-23 | New Zealand vs England | England in New Zealand T20I Series 2025 | 106 | 102 (17 ov) | 168.0 | Mid-match rain revision. |

> **Total Deliveries in Category A**: **844 deliveries**. Flagged with `is_target_timing_unresolved = True`, `applicable_target = NaN`, `pre_rrr = NaN`, `is_valid_pressure_state = False`.

---

## 3. Category B: Super Overs (6 Matches / 38 Deliveries)

Super Overs are standalone one-over eliminators contested after a tie. They feature unique playing rules (maximum 6 legal balls, maximum 2 wickets). They cannot be appended to or treated as regular 20-over innings.

| Match ID | Match Date | Teams | Innings 3 Balls | Innings 3 Score/Wickets | Innings 4 Balls | Innings 4 Score/Wickets | Super Over Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **34429** | 2024-07-30 | Sri Lanka vs India | 4 | 2 / 2 (All out) | 1 | 4 / 0 | India won by 2 wickets |
| **40725** | 2025-04-16 | Delhi Capitals vs Rajasthan Royals | 6 | 11 / 2 | 4 | 13 / 0 | Delhi Capitals won |
| **45512** | 2025-09-26 | India vs Sri Lanka | 6 | 2 / 2 (All out) | 1 | 3 / 0 | India won |
| **48027** | 2025-11-21 | Bangladesh A vs India A | 2 | 0 / 2 (All out) | 2 | 1 / 1 | Bangladesh A won |
| **48029** | 2025-11-23 | Bangladesh A vs Pakistan A | 4 | 6 / 2 | 4 | 7 / 0 | Pakistan A won |
| **50359** | 2026-04-26 | LSG vs KKR | 3 | 1 / 2 | 1 | 4 / 0 | KKR won |

> **Total Deliveries in Category B**: **38 deliveries** (25 in innings 3, 13 in innings 4). Flagged with `is_super_over = True`, `innings_phase = 'Super Over'`, `is_valid_pressure_state = False`.

---

## 4. Category C: Non-Excluded Pre-Match Shortened Matches (12 Matches / 1,452 Deliveries)

In 12 matches, both `first_inn_revised_overs` and `second_inn_revised_overs` were set to identical values before play commenced (e.g. Match 17395: India vs SA, 8 overs / 48 balls per side).
- **Rule**: Because the scheduled length and DLS target were established before ball 1 of innings 1, **no retrospective target distortion exists**.
- **Status**: **NOT EXCLUDED**. Fully reconstructed with scheduled legal limits ($48, 60, 66, 72, 78, 84, 90, 102, 114$ balls) and flagged `is_valid_pressure_state = True`.

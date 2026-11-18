# SupeRR Selector Season 2 — Analytical Limitations & Assumptions Register

This document provides a transparent, exhaustive disclosure of data limitations, analytical assumptions, and modeling boundaries governing the SupeRR Selector Season 2 outputs.

---

## 1. Cricket Data & Relational Limitations

### 1.1 Incomplete Ball-Tracking & Spatial Metrics
- **Limitation**: The dataset contains zero ball tracking coordinates (release point $(x,y,z)$, pitch bounce coordinates, deviation off the seam/pitch) and zero batting wagon wheel data (stroke angles, fielder positions).
- **Analytical Impact**: Contextual expected performance models cannot distinguish between a delivery pitched on a perfect yorker length outside off-stump versus a full toss that was mistimed. Expectations reflect average macro-context (phase, wickets, score, competition) rather than micro delivery execution.

### 1.2 Speed Gun Missingness & Scaling Anomalies
- **Limitation**: `bowl_speed` is recorded as `0.0` across 77,861 deliveries (38.7% of all balls) and contains obvious decimal scaling corruption (e.g. `1456.1 km/h`).
- **Analytical Impact**: Delivery speed could not be used as a predictor in expected-performance modeling without introducing massive imputation bias. Bowling analysis relies strictly on bowler handedness, style (`Pace` vs `Spin`), and delivery category.

### 1.3 Fielding Metrics & Dropped Catch Absence
- **Limitation**: The source data logs official dismissal outcomes (`Caught`), but records zero dropped catches, missed run-out opportunities, or misfield runs.
- **Analytical Impact**: A bowler's wicket-taking residual reflects *realized dismissals* rather than *expected wickets including dropped chances*. A bowler who creates three dropped catches in a death over is charged with conceded runs without receiving wicket credit.

### 1.4 Environmental & Weather Absence (Dew Factor)
- **Limitation**: No atmospheric humidity, temperature, wind velocity, or ground dew logs are supplied.
- **Analytical Impact**: In Indian and UAE evening fixtures, heavy dew frequently hampers second-innings grip and favors chasing batters. The model controls for innings ($I=1$ vs $I=2$) and macro venue baselines, but cannot adjust for specific high-dew nights.

---

## 2. Competition & Opposition Strength Adjustment Limits

### 2.1 Sparse Head-to-Head Overlap in T20 Internationals
- **Limitation**: In international T20 cricket, teams schedule tours asynchronously under the ICC Future Tours Programme. Top-tier Full Member nations rarely play Associate members outside of global qualifiers.
- **Opposition Adjustment Standard**:
  - The model adjusts for macro tournament category: `IPL (Franchise)`, `Bilateral Series (T20I)`, `Multi-Nation Tournament (T20I)`, and `International Tri-Series (T20I)`.
  - It does **not** attempt fine-grained opponent Elo scaling because the bipartite player matchup graph is highly fragmented.
  - As disclosed in candidate profiles, players who accumulated stats primarily in bilateral tours against lower-ranked nations are flagged (`International-only sample`) to assist scouts in contextualizing performance.

### 2.2 Exclusion of Youth / 'A' Team Competitions
- **Policy**: Tournaments featuring developmental sides (`Mens T20 Emerging Teams Asia Cup` and `Asia Cup Rising Stars`) were isolated from the primary analysis. Including junior prospects against senior international stars would distort baseline expected runs and wicket probabilities.

---

## 3. Match State Reconstruction & Timing Boundaries

### 3.1 Interrupted Chases & Rain Curtailment Timing
- **Standard**: In 34 matches with populated revised limits, `matches.csv` records only final post-match summaries (`second_inn_revised_overs`, `revised_target`). It does not record the exact delivery at which rain halted play.
- **Analytical Consequence**: Applying revised targets retrospectively to pre-stoppage balls constitutes lookahead bias. Consequently, **1,641 chase deliveries** across 23 innings were flagged `INTERRUPTED_TARGET_TIMING_UNRESOLVED` and excluded from RRR-dependent pressure modeling.

### 3.2 Unexplained Batter Exits (`UNRESOLVED_EXIT`)
- **Standard**: In 12 records, `is_wicket == False` and `dismissal_type == NaN` while `dismissed_player_id` is populated. Systematic traces proved that none of these 12 batters returned to the crease, but source files omit whether they retired hurt (injury) or retired out (tactical).
- **Analytical Policy**: These innings are **not treated as completed not-out innings** in batter baselines, preventing artificial inflation of survival metrics. They are flagged as `UNRESOLVED_EXIT`.

### 3.3 Missing Super Over Delivery Logging
- **Standard**: 10 matches recorded tie-breaker results in `matches.csv`, but only 6 have ball-by-ball delivery rows in `ball_by_ball.csv`. Matches `13613`, `18532`, `21176`, and `28962` lack delivery records for their Super Overs.
- **Analytical Consequence**: Super Overs cannot be analyzed for these 4 matches. For the 6 recorded matches, all 38 balls are isolated under `is_super_over == True` and excluded from regular 20-over pressure curves due to distinct 6-ball / 2-wicket laws.

---

## 4. Modeling & Ranking Trade-offs

### 4.1 Conservative Lower-Bound Ranking ($q_{0.05}$)
- **Trade-off**: Ranking players by the 5th percentile lower bound of their 90% bootstrap score interval deliberately penalizes variance and rewards large sample size.
- **Consequence**: An emerging player with an eye-catching central score of $0.70$ over 105 balls and wide interval $[0.10, 1.30]$ will rank below a seasoned veteran with central score $0.62$ over 500 balls and tight interval $[0.35, 0.89]$. This is an intentional risk-mitigation policy for franchise squad construction.

### 4.2 Component Weight Sensitivity
- **Declared Weights**: 60% Scoring/Prevention + 40% Survival/Wickets; 75% Effectiveness + 25% Lift.
- **Robustness Finding**: Testing 50/50 and 70/30 component weights, and 60/40 and 90/10 effectiveness/lift weights, demonstrated 8 to 10 out of 10 player overlap among the top shortlist, confirming that top rankers excel across both volume scoring and wicket suppression.

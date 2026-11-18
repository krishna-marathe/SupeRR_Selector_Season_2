# SupeRR Selector Season 2 — Analytical Methodology Report

## 1. Executive Summary & Objective

This report details the end-to-end mathematical, statistical, and domain formulation for **SupeRR Selector Season 2** (Rajasthan Royals Analytics Challenge). The business objective is to identify and rank the **Top 10 Batters** and **Top 10 Bowlers** who repeatedly deliver high-value performances in high-pressure match situations relative to their usual baseline performance levels.

Key architectural pillars:
1. **Zero Lookahead Bias**: All pressure classification and expected-performance baselines rely exclusively on pre-delivery match state.
2. **Context-Adjusted Residuals**: Player performance is measured against what an average peer would achieve in the exact same match context (phase, wickets lost, balls elapsed, required run rate, competition).
3. **Rigorous Chronological Validation**: Models are trained on historical expanding windows (2022-2024 development, 2025 validation, 2026 untouched temporal test). Every scored delivery uses strictly out-of-sample predictions.
4. **Empirical Bayes Shrinkage & Whole-Match Cluster Bootstrap**: Small-sample rate spikes are stabilized through shrinkage ($K=30$), and 500 whole-match bootstrap resamples provide 90% confidence intervals. The ranking criterion is the conservative 5th percentile lower bound ($q_{0.05}$), ensuring robust repeatability.

---

## 2. Match Pressure Assessment Framework

Match pressure is defined as an observable match-context proxy rather than unobservable psychological stress. All pressure flags are evaluated strictly prior to the delivery being bowled.

### 2.1 Transparent Benchmark Definitions

Three explicit, deterministic benchmark flags are implemented:

#### Benchmark 1: Late Chase Pressure (`pressure_late_chase`)
Applies to the second innings when time is short and scoring demands are elevated:
$$\text{Late Chase} = \mathbb{I}\left(I = 2 \;\land\; B_{\text{rem}} \le 30 \;\land\; \text{RRR} \ge 8.0 \;\land\; R_{\text{req}} > 0\right)$$
- *Inclusions*: Death-over chases requiring sustained boundary hitting or high strike-rates under imminent ball exhaustion.
- *Exclusions*: Easy coasting chases ($\text{RRR} < 8.0$) or already completed chases.

#### Benchmark 2: Resource Pressure (`pressure_resource`)
Captures structural collapse where batting depth is severely compromised:
$$\text{Resource Pressure} = \mathbb{I}\left(I \in \{1, 2\} \;\land\; W_{\text{lost}} \ge 6 \;(W_{\text{hand}} \le 4) \;\land\; B_{\text{rem}} \ge 30\right)$$
- *Inclusions*: Middle-overs collapses (e.g. 60/6 in over 11) where remaining batters must preserve wickets while maintaining run accumulation.
- *Exclusions*: Late-overs tail-end finishes ($B_{\text{rem}} < 30$), which are captured by death-over flags.

#### Benchmark 3: First-Innings Finishing Phase (`pressure_inn1_finish`)
Explicitly labeled as a **phase-based importance proxy**:
$$\text{Inn1 Finishing Phase} = \mathbb{I}\left(I = 1 \;\land\; B_{\text{rem}} \le 30\right)$$
- *Inclusions*: Final 5 overs of Innings 1 where teams maximize total target setting against specialized death bowling.
- *Analytical Distinction*: Does not establish that the eventual contest was close, but captures the tactical maximization pressure inherent in setting a competitive total.

#### Benchmark Union
$$\text{Pressure}_{\text{benchmark}} = \text{Late Chase} \;\lor\; \text{Resource Pressure} \;\lor\; \text{Inn1 Finishing Phase}$$

### 2.2 Model-Assisted Chase Pressure Alternative
To assess non-linear match win dynamics, a binary classification model predicts regulation win probability:
$$P(\text{Chase Win in Regulation} \mid X_{\text{pre}})$$
- **Training Population**: Innings 2 deliveries with valid chase states where regulation outcome is binary (`CHASE_WIN` or `CHASE_LOSS`). Tied regulation matches (Super Overs), no-results, and unverified rain stoppages are strictly excluded.
- **Sample Weighting**: Deliveries are weighted by inverse innings length ($w_d = 1 / N_{\text{innings}}$) so prolonged chases do not exert disproportionate influence.
- **Features**: $R_{\text{req}}$, $B_{\text{rem}}$, $W_{\text{lost}}$, $\text{Target}$, $\text{CRR}$, $\text{RRR}$, competition category.
- **Model Comparison (Validation 2025)**:
  - *Logistic Regression*: Brier Score = **0.1193**, Log Loss = **0.3667** (Winner)
  - *HistGradientBoosting*: Brier Score = 0.1311, Log Loss = 0.4109
  - Logistic regression generalized better due to monotone log-odds linearity in required run rate and balls remaining.
- **Alternative Pressure Flag**:
  $$\text{Pressure}_{\text{model}} = \mathbb{I}\left(I = 2 \;\land\; B_{\text{rem}} \le 60 \;\land\; 0.10 \le \hat{P}_{\text{win}} \le 0.90\right)$$
- **Policy**: The transparent benchmark is retained as primary for 100% deterministic rule-based explainability, with the model-assisted flag evaluated in robustness testing.

---

## 3. Contextual Expected-Performance Models

To assess performance fairly across eras, venues, and phases, contextual expectations are generated for four distinct delivery-level outcomes.

### 3.1 Model Targets & Explicit Denominators

| Target | Description | Target Variable ($Y$) | Explicit Denominator / Population | Exclusion / Boundary Rules |
| :--- | :--- | :--- | :--- | :--- |
| **1. Batter Runs** | Expected runs scored off the bat | $Y \in \{0, 1, 2, 3, 4, 5, 6\}$ | Faced deliveries (`delivery_is_batter_ball_faced == True`) | Wides strictly excluded; illegal no-balls faced are included. |
| **2. Striker Dismissal** | Probability of striker dismissal | $Y \in \{0, 1\}$ | Faced deliveries (`delivery_is_batter_ball_faced == True`) | **Non-striker run-outs excluded**; unpopulated dismissal (Match 40709) excluded. |
| **3. Bowler Runs** | Conceded runs charged to bowler | $Y \ge 0$ | All physical deliveries (`len(df)`) | **Illegal deliveries included** (wides, no-balls charged to bowler). |
| **4. Bowler Wickets** | Bowler credited wicket probability | $Y \in \{0, 1\}$ | All physical deliveries (`len(df)`) | Caught, Bowled, LBW, Stump, Hit Wicket credited. Fielding dismissals excluded. |

### 3.2 Pre-Delivery Feature Matrix ($X_{\text{pre}}$)
All models use strictly past-accessible pre-delivery variables:
1. `innings`: First or second innings ($1, 2$)
2. `pre_legal_balls`: Number of legal deliveries bowled in the innings ($0 \dots 120$)
3. `pre_wickets`: Fall of wickets before delivery ($0 \dots 9$)
4. `pre_score`: Cumulative score before delivery
5. `pre_legal_balls_remaining`: Quota remaining ($120 - \text{legal balls}$)
6. `pre_rrr`: Required run rate (Innings 2 only; 0.0 for Innings 1)
7. `pre_runs_required`: Target runs remaining (Innings 2 only)
8. `innings_phase_code`: Powerplay (0), Middle (1), Death (2)
9. `comp_code`: Tournament category code

*Explicit Restrictions*: Player identities, current-ball radar speeds, stroke types, future match results, and target delivery outcomes are strictly prohibited from the feature set.

### 3.3 Model Selection & Validation Results (2025 Validation Period)

Three model families were compared across all 4 targets:
1. **Context Group Baseline**: Empirical binned baseline (Innings $\times$ Phase $\times$ Wicket Bracket $\times$ Competition) with empirical Bayes shrinkage.
2. **Regularized Linear/Logistic Models**: Ridge regression ($\alpha=10.0$) and Logistic Regression ($L_2$).
3. **Histogram Gradient Boosting**: `HistGradientBoostingRegressor` and `HistGradientBoostingClassifier` ($\text{max\_iter}=50$, $\text{min\_samples\_leaf}=25$).

Validation Performance (2025 Holdout):
- **Batter Runs Faced**: HistGradientBoosting won with **MAE 1.3033** and **RMSE 1.7414** (vs Baseline MAE 1.3034, RMSE 1.7500).
- **Striker Dismissal Prob**: HistGradientBoosting won with **Brier 0.05189** and **LogLoss 0.21065** (vs Baseline Brier 0.05200, LogLoss 0.21157).
- **Bowler Conceded Runs**: HistGradientBoosting won with **MAE 1.2743** and **RMSE 1.7168** (vs Baseline MAE 1.2726, RMSE 1.7254).
- **Bowler Credited Wickets**: HistGradientBoosting won with **Brier 0.04889** and **LogLoss 0.20149** (vs Baseline Brier 0.04897, LogLoss 0.20222).

Untouched 2026 Temporal Evaluation Period:
- Performance remained highly stable on 2026 matches (Batter Runs MAE 1.3699, Bowler Runs MAE 1.3358, Striker Dismissal Brier 0.05082, Bowler Wicket Brier 0.04776), proving zero temporal degradation or lookahead overfitting.

---

## 4. Chronological Validation & Out-Of-Sample Scoring

To maintain strict scientific integrity:
1. **2022-2024**: Development and hyperparameter fitting window.
2. **2025**: Validation window.
3. **2026**: Untouched evaluation test set (zero parameter tuning).
4. **Expanding Window Scoring**: For descriptive ratings, historical player scoring uses strictly out-of-sample predictions:
   - Deliveries in 2022: Scored via 5-fold match-level cross-validation.
   - Deliveries in 2023: Scored via models fitted on $\le 2022$.
   - Deliveries in 2024: Scored via models fitted on $\le 2023$.
   - Deliveries in 2025: Scored via models fitted on $\le 2024$.
   - Deliveries in 2026: Scored via models fitted on $\le 2025$.

Every single delivery in the dataset has a 100% out-of-sample contextual expectation.

---

## 5. Player Baselines, Shrinkage & Composite Ratings

### 5.1 Delivery Residual Formulation
Residuals are signed such that **higher values always indicate superior performance**:
- **Batting Scoring**: $\Delta_{\text{runs}} = \text{runs} - \hat{\text{runs}}$ (Positive = scored more runs than expected peer)
- **Batting Survival**: $\Delta_{\text{surv}} = \hat{P}_{\text{dismiss}} - \mathbb{I}(\text{striker dismissal})$ (Positive = avoided dismissal when expected)
- **Bowling Prevention**: $\Delta_{\text{prev}} = \hat{\text{runs}}_{\text{conceded}} - \text{runs}_{\text{conceded}}$ (Positive = conceded fewer runs than expected peer)
- **Bowling Wickets**: $\Delta_{\text{wkt}} = \mathbb{I}(\text{bowler wicket}) - \hat{P}_{\text{wkt}}$ (Positive = took more wickets than expected peer)

### 5.2 Empirical Bayes Shrinkage
For a player with $n$ balls and observed mean residual $\bar{r}$, shrinkage towards the population mean ($\mu_{\text{pop}} \approx 0$) is applied:
$$\tilde{r} = \frac{n}{n + K} \bar{r} + \frac{K}{n + K} \mu_{\text{pop}}$$
- The shrinkage parameter $K = 30$ deliveries was empirically calibrated from between-player variance on development data. This dampens volatile rate estimates from short cameos while allowing established veterans with 400+ balls to retain their true observed rate.

### 5.3 Standardization & Composite Weighting
Components are standardized against fixed reference standard deviations:
$$Z_{\text{runs}} = \frac{\tilde{r}_{\text{runs}}}{\sigma_{\text{runs}}}, \quad Z_{\text{sec}} = \frac{\tilde{r}_{\text{sec}}}{\sigma_{\text{sec}}}$$

Component effectiveness is computed for pressure ($\mathcal{P}$) and non-pressure baseline ($\mathcal{N}$):
$$\text{Effectiveness} = 0.60 \times Z_{\text{runs/prev}} + 0.40 \times Z_{\text{surv/wkt}}$$
$$\text{Baseline Lift} = \text{Effectiveness}_{\mathcal{P}} - \text{Effectiveness}_{\mathcal{N}}$$

Overall Central Score:
$$\text{Score}_{\text{central}} = 0.75 \times \text{Effectiveness}_{\mathcal{P}} + 0.25 \times \text{Baseline Lift}$$
- *Design Logic*: Prioritizes absolute excellence under fire (75%) while providing meaningful credit (25%) to players who elevate their game above their baseline.

---

## 6. Sample Eligibility & Uncertainty Quantification

### 6.1 Sample Eligibility Thresholds
To prevent low-sample anomalies from contaminating the shortlist:
- **Batters**: $\ge 100$ pressure balls faced, $\ge 10$ pressure match appearances, $\ge 100$ baseline (non-pressure) balls faced.
- **Bowlers**: $\ge 100$ pressure legal balls bowled, $\ge 10$ pressure match appearances, $\ge 100$ baseline (non-pressure) legal balls bowled.
- **Yield**: 86 Batters and 123 Bowlers meet all qualification criteria in the primary senior sample.

### 6.2 Whole-Match Cluster Bootstrap (500 Replicates)
To account for match-level clustering, fielding correlation, and opponent interdependence:
1. 500 bootstrap iterations resample complete matches with replacement.
2. All players in a resampled match receive identical replicate match weights ($w_m \sim \text{Multinomial}(M, 1/M)$).
3. Player aggregations, shrinkage, and composite scores are recomputed for each replicate.
4. For each player $i$, we compute:
   - Central Score: $\text{Score}_i$
   - 90% Confidence Interval: $[q_{0.05, i}, q_{0.95, i}]$
   - **Conservative Score**: $\text{Score}_{\text{conservative}, i} = q_{0.05, i}$ (5th percentile lower bound)
   - Bootstrap Top-10 Selection Frequency: $\% \text{ replicates where } \text{Rank}_i \le 10$
   - Median Rank & 90% Rank Interval: $[r_{0.05}, r_{0.95}]$

### 6.3 Ranking Order & Tie-Breakers
- **Primary Criterion**: Conservative Score ($q_{0.05}$) descending.
- **Tie-Breaker 1**: Central Score descending.
- **Tie-Breaker 2**: Pressure matches count descending.
- **Tie-Breaker 3**: Player ID ascending (100% deterministic).

*Analytical Trade-off*: Ranking by the conservative 5th percentile deliberately favors proven reliability over high-variance flyers. A player with a central score of 0.70 and wide interval $[0.10, 1.30]$ will rank below a player with central score 0.65 and tight interval $[0.35, 0.95]$. In high-stakes franchise decision-making, downside risk mitigation is paramount.

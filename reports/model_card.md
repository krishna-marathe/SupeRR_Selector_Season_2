# SupeRR Selector Season 2 — Model Card: Contextual Expected-Performance & Win Probability Models

## 1. Model Overview

| Attribute | Details |
| :--- | :--- |
| **Model Names** | Contextual Expectation Suite (`HGB-Runs`, `HGB-Wickets`, `LogReg-WinProb`) |
| **Model Types** | Histogram Gradient Boosting Regressors/Classifiers & Regularized Logistic Regression |
| **Task Category** | Conditional Expected-Performance Modeling & In-Match Win Probability Estimation |
| **Version** | 2.0 (Post-Audit Chronological Expanding Window) |
| **Maintainer** | Rajasthan Royals Analytics Team / SupeRR Selector Pipeline |
| **Framework** | Python 3.11, `scikit-learn 1.7.2`, `pandas 2.3.3`, `numpy 2.3.4` |

---

## 2. Intended Use & Analytical Scope

- **Primary Purpose**: Estimate situational peer-performance baselines (expected runs and wicket probabilities) given only pre-delivery match context, enabling the calculation of unbiased player performance residuals.
- **Intended Users**: Rajasthan Royals cricket operations, performance analysts, and talent scouts evaluating situational reliability for the upcoming auction and tactical planning.
- **Out-of-Scope Uses**:
  - *Auction Price Predictions*: This model evaluates on-field performance residuals, not financial market values.
  - *Squad Budget Optimization*: Portfolio selection and salary caps belong to a distinct operational module.
  - *Direct In-Game Match Strategy*: Descriptive evaluations are calculated post-match using historical expanding windows.

---

## 3. Training & Validation Datasets

### 3.1 Primary Sample Population
The models are trained exclusively on verified senior professional fixtures:
- **Competitions Included**: Indian Premier League (IPL), Senior Men's Bilateral T20 Internationals, ICC/ACC Multi-Nation Tournaments (Asia Cup), and Senior Tri-Series.
- **Competitions Separated**: Youth and 'A' team development tournaments (Men's T20 Emerging Teams Asia Cup, Asia Cup Rising Stars) are segregated into a supplementary analysis.
- **Quarantined Matches**: 3 matches (`18532`, `20190`, `48610`) were quarantined due to scorecard/result-string divergences.

### 3.2 Chronological Partitioning (Zero Temporal Leakage)
To strictly mirror real-world operational forecasting, the dataset is partitioned chronologically by match date:
- **Development Period (2022–2024)**: 115,027 deliveries across 478 matches. Used for model architecture selection, hyperparameter tuning, and shrinkage estimation.
- **Validation Period (2025)**: 44,629 deliveries across 190 matches. Used for comparative model evaluation and calibration assessment.
- **Untouched Temporal Evaluation (2026)**: 30,660 deliveries across 144 matches. Held completely untouched until final verification.
- **Out-of-Sample Scoring**: Every scored delivery across the historical record receives an expectation generated from models trained strictly on preceding years (e.g. 2024 matches scored with models trained on $\le 2023$).

---

## 4. Input Features & Denominator Definitions

### 4.1 Feature Set ($X_{\text{pre}}$)
All input features represent verified match state available *before* the delivery is bowled:
1. `innings`: First (1) or Second (2) innings.
2. `pre_legal_balls`: Count of legal balls bowled in the innings ($0 \dots 120$).
3. `pre_wickets`: Count of wickets fallen prior to delivery ($0 \dots 9$).
4. `pre_score`: Cumulative team score prior to delivery.
5. `pre_legal_balls_remaining`: Legal deliveries remaining ($120 - \text{legal balls}$).
6. `pre_rrr`: Required run rate (Innings 2 only; 0.0 for Innings 1).
7. `pre_runs_required`: Absolute target runs remaining (Innings 2 only).
8. `innings_phase_code`: Powerplay (0), Middle (1), Death (2).
9. `comp_code`: Category code for franchise vs international context.

> [!CAUTION]
> **Prohibited Variables**: Player identities, historical player averages, current delivery speeds, stroke types, dismissal outcomes, and match results are strictly excluded to prevent reputation bias and target leakage.

### 4.2 Explicit Denominators

| Model Target | Population / Denominator | Handling of Extras & Edge Cases |
| :--- | :--- | :--- |
| **Batter Runs Faced** | Faced deliveries (`delivery_is_batter_ball_faced == True`) | Wides excluded; legal balls and no-balls faced included. |
| **Striker Dismissal** | Faced deliveries (`delivery_is_batter_ball_faced == True`) | **Non-striker run-outs excluded**; unpopulated dismissal (Match 40709) excluded. |
| **Bowler Conceded Runs** | All physical deliveries (`len(df)`) | **Illegal deliveries included** (wides, no-balls charged to bowler). Bat-pad anomalies uncharged. |
| **Bowler Wickets** | All physical deliveries (`len(df)`) | Bowler dismissals credited (Caught, Bowled, LBW, Stump, Hit Wicket). Run-outs excluded. |
| **Chase Win Probability** | Valid regulation Innings 2 deliveries | Tied regulation innings (Super Overs) and rain abandonments excluded. |

---

## 5. Quantitative Model Comparison & Performance

### 5.1 Validation Performance (2025 Holdout Period)

| Target Task | Candidate Model | Primary Metric | Secondary Metric | Selection Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Batter Runs Faced** | Context Baseline | MAE: 1.3034 | RMSE: 1.7500 | Benchmark |
| | Ridge Regression | MAE: 1.3075 | RMSE: 1.7442 | Rejected |
| | **HistGradientBoosting** | **MAE: 1.3033** | **RMSE: 1.7414** | **Selected Model** |
| **Striker Dismissal Prob** | Context Baseline | Brier: 0.05200 | LogLoss: 0.21157 | Benchmark |
| | Logistic Regression | Brier: 0.05198 | LogLoss: 0.21140 | Rejected |
| | **HistGradientBoosting** | **Brier: 0.05189** | **LogLoss: 0.21065** | **Selected Model** |
| **Bowler Conceded Runs** | Context Baseline | MAE: 1.2726 | RMSE: 1.7254 | Benchmark |
| | Ridge Regression | MAE: 1.2772 | RMSE: 1.7201 | Rejected |
| | **HistGradientBoosting** | **MAE: 1.2743** | **RMSE: 1.7168** | **Selected Model** |
| **Bowler Wickets Prob** | Context Baseline | Brier: 0.04897 | LogLoss: 0.20222 | Benchmark |
| | Logistic Regression | Brier: 0.04895 | LogLoss: 0.20200 | Rejected |
| | **HistGradientBoosting** | **Brier: 0.04889** | **LogLoss: 0.20149** | **Selected Model** |
| **Chase Win Probability** | **Logistic Regression** | **Brier: 0.11929** | **LogLoss: 0.36670** | **Selected Model** |
| | HistGradientBoosting | Brier: 0.13113 | LogLoss: 0.41091 | Overfitted |

### 5.2 Untouched Temporal Test Performance (2026 Season)
- **Batter Runs**: MAE = 1.3699, RMSE = 1.8050 ($N=30,660$ balls)
- **Striker Dismissal**: Brier = 0.05082, LogLoss = 0.20732 ($N=30,660$ balls)
- **Bowler Conceded Runs**: MAE = 1.3358, RMSE = 1.7771 ($N=31,996$ balls)
- **Bowler Wickets**: Brier = 0.04776, LogLoss = 0.19794 ($N=31,996$ balls)

---

## 6. Known Limitations & Fair Use Guidelines

1. **Opposition Adjustment Boundaries**:
   - In international T20 cricket, teams face heterogeneous opponents scheduled via the ICC FTP.
   - Adjusting for exact head-to-head opposition rating is hindered by sparse match overlap between specific bowling attacks and batting lineups.
   - The model adjusts for macro tournament category (IPL vs Senior T20I) and venue conditions, but cannot perfectly control for playing against weaker Associate attacks vs Full Member attacks.
2. **Fielding & Dropped Catches**:
   - The dataset records whether a catch was completed (`Caught`), but lacks dropped-catch tracking. A bowler's wicket-taking residual reflects realized dismissals rather than expected wickets including dropped chances.
3. **Pitch Deterioration & Dew**:
   - While pre-score and elapsed balls capture average run deceleration or acceleration, intra-day dew (which often aids second-innings batting in subcontinental evening matches) is unrecorded in the source files.

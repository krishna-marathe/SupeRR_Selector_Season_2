# SupeRR Selector Season 2 — Comprehensive Report Outline

This outline structures the final executive presentation and technical dossier for the Rajasthan Royals leadership team, following the required analytical narrative:
**Recommendations $\rightarrow$ Pressure Definition $\rightarrow$ Fair Performance Measurement $\rightarrow$ Batting Evidence $\rightarrow$ Bowling Evidence $\rightarrow$ Reliability $\rightarrow$ Limitations.**

---

## Section 1: Executive Recommendations
- **1.1 Business Objective**: Identify and acquire T20 players with proven repeatability under high-stakes match pressure.
- **1.2 Top 10 Batters Under Pressure**: Ordered ranking by 90% bootstrap conservative lower-bound score ($q_{0.05}$), highlighting central score, baseline lift, consistency, and sample volume.
- **1.3 Top 10 Bowlers Under Pressure**: Ordered ranking by 90% bootstrap conservative lower-bound score ($q_{0.05}$), highlighting boundary suppression, wicket-taking in death overs, and consistency.
- **1.4 All-Rounder Analysis**: Independent qualification assessment (e.g. Romario Shepherd, Sikandar Raza).
- **1.5 Strategic Squad Implications**: High-leverage acquisitions for death-over execution and resource-collapse mitigation.

---

## Section 2: Match Pressure Definition & Observable Proxies
- **2.1 Observable Context vs Psychological Stress**: Pre-delivery match state as an objective operational proxy.
- **2.2 Transparent Benchmark Rules**:
  - *Late Chase*: Innings 2, $\le 30$ legal balls remaining, $\text{RRR} \ge 8.0$, target unreached.
  - *Resource Pressure*: $\le 4$ wickets in hand, $\ge 30$ legal balls remaining (middle-over collapses).
  - *First-Innings Finish*: Innings 1, $\le 30$ legal balls remaining (phase-based maximization proxy).
- **2.3 Model-Assisted Chase Pressure Alternative**:
  - In-match regulation win probability estimation ($P(\text{Win} \mid X_{\text{pre}})$).
  - Comparative evaluation: Logistic Regression (Brier 0.119) vs HistGradientBoosting (Brier 0.131).
  - Rationale for retaining the transparent benchmark for primary ratings.
- **2.4 Pressure Distribution**: Coverage by phase (89.5% death overs, 6.4% middle overs, 0.02% powerplay), format (IPL vs T20I), and season.

---

## Section 3: Fair Performance Measurement (Contextual Expectations)
- **3.1 Zero Lookahead Architecture**: Pre-delivery features only ($X_{\text{pre}}$).
- **3.2 Four Target Models & Explicit Denominators**:
  - *Batter Runs Faced*: Excludes wides; includes legal balls and no-balls faced.
  - *Striker Dismissal*: Excludes non-striker run-outs and unpopulated dismissal anomalies.
  - *Bowler Conceded Runs*: All physical deliveries (includes wides and no-balls).
  - *Bowler Credited Wickets*: Caught, Bowled, LBW, Stump, Hit Wicket. Excludes fielding dismissals.
- **3.3 Chronological Expanding Window Validation**:
  - 2022-2024 Development $\rightarrow$ 2025 Validation $\rightarrow$ 2026 Untouched Temporal Evaluation.
  - Out-of-sample delivery scoring across all historical periods.
- **3.4 Residual Formulation**: Signed so positive values always indicate superior performance above peer expectations.
- **3.5 Empirical Bayes Shrinkage**: Stabilization of small-sample cameos ($K = 30$ balls).

---

## Section 4: Batting Pressure Evidence & Deep-Dives
- **4.1 Top-10 Batter Ranking Table**: Detailed breakdown of ranks, IDs, scores, and intervals.
- **4.2 Archetype Stratification**:
  - *Elite Death Accelerators*: Romario Shepherd (#1), Rovman Powell (#3), Tim David (#5).
  - *High-Consistency Chasers*: Rinku Singh (#2, 53.7% consistency), Tilak Varma (#4, 58.8% consistency).
  - *Emerging Dynamic Finishers*: Naman Dhir (#7, 75.0% consistency), Tristan Stubbs (#9, 62.2% consistency).
- **4.3 Supporting Match-Level Evidence**: Single-match contributions and peak pressure performances.
- **4.4 Franchise vs International Split**: IPL-only comparison and competition exposure.

---

## Section 5: Bowling Pressure Evidence & Deep-Dives
- **5.1 Top-10 Bowler Ranking Table**: Detailed breakdown of ranks, IDs, scores, and intervals.
- **5.2 Tactical Archetype Breakdown**:
  - *Economic Strangulation*: Sunil Narine (#1, 74.4% consistency, conservative score 0.590).
  - *Precision Death Yorker Mastery*: Jasprit Bumrah (#3, 76.7% consistency, 537 pressure balls).
  - *Attacking Wrist-Spin*: Kuldeep Yadav (#5), Rashid Khan (#7), Wanindu Hasaranga (#10).
  - *Early/Late Pace Enforcers*: Shaheen Afridi (#6), Matheesha Pathirana (#8).
- **5.3 Wicket-Taking vs Run-Prevention Dynamics**: Trade-off between bowling economy and boundary wickets.

---

## Section 6: Reliability & Robustness Analysis
- **6.1 Whole-Match Cluster Bootstrap**: 500 replicates resampling complete matches.
- **6.2 Conservative Ranking Standard ($q_{0.05}$)**: Rewarding downside protection over volatile peaks.
- **6.3 Sensitivity Checks**:
  - Late-phase ball limits (24 vs 30 vs 36 balls).
  - Required run-rate hurdles (7.0 vs 8.0 vs 9.0).
  - Inclusion vs exclusion of first-innings finishing phase.
  - Component weights (50/50 vs 60/40 vs 70/30).
  - Effectiveness vs lift weights (60/40 vs 75/25 vs 90/10).
  - Sample qualification thresholds (75 vs 100 vs 150 balls).
  - IPL-only vs Combined Senior fixtures.
- **6.4 Temporal Predictive Validity**: Out-of-sample correlation showing 2022-2024 ratings predict 2025-2026 performance ($r = 0.112$ for batting, $r = 0.069$ for bowling).

---

## Section 7: Data Boundaries, Limitations & Operational Caveats
- **7.1 Spatial & Tracking Limitations**: Absence of pitch trajectory $(x,y,z)$ and wagon wheels.
- **7.2 Speed Gun Missingness**: Unrecorded speeds on 38.7% of balls.
- **7.3 Unrecorded Fielding & Dropped Catches**: Realized dismissals vs expected wickets.
- **7.4 Environmental Variables**: Absence of evening dew logs.
- **7.5 Opposition Strength Adjustment Boundaries**: Bipartite match sparsity in T20Is.
- **7.6 Administrative Disclosures**: Player availability, retention rules, and dropdown eligibility pending administrative verification.

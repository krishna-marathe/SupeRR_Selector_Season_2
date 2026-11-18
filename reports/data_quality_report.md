# SupeRR Selector Season 2 - Data Quality & Integrity Report

This report presents an empirical, code-verified audit of the SupeRR Selector Season 2 data pack. All original files were examined strictly in read-only mode and preserved without modification.

---

## 1. Dataset Dimensions & Duplicate Summary

| Table Name | File Name | Row Count | Column Count | Full Duplicate Rows | Memory (MB) | Primary Candidate Key |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **competitions** | `competitions.csv` | 141 | 4 | 0 (0.00%) | 0.01 MB | `comp_id` |
| **teams** | `teams.csv` | 353 | 3 | 0 (0.00%) | 0.01 MB | `(comp_id, team_id)` |
| **matches** | `matches.csv` | 883 | 22 | 0 (0.00%) | 0.15 MB | `match_id` |
| **playing_eleven** | `playing_eleven.csv` | 28,381 | 9 | 0 (0.00%) | 1.84 MB | `(match_id, player_id)`* |
| **mappings** | `competition_team_player_mapping.csv`| 6,413 | 6 | 0 (0.00%) | 0.45 MB | `(comp_id, player_id)` |
| **ball_by_ball** | `ball_by_ball.csv` | 200,999 | 33 | 0 (0.00%) | 50.60 MB | `(match_id, innings, innings_ball_num)` |

> **Key Takeaway**: There are **zero completely identical duplicate rows** in any of the 6 supplied CSV files. Every row contains at least one distinct data attribute.

---

## 2. Missingness Analysis

### 2.1 Clean Tables (0% Missingness)
- `competitions.csv`: 0 missing values across all 4 columns.
- `teams.csv`: 0 missing values across all 3 columns.
- `competition_team_player_mapping.csv`: 0 missing values across all 6 columns.

### 2.2 Tables with Missingness

#### A. `matches.csv` (883 rows)
| Column | Null Count | Null % | Domain Explanation |
| :--- | :--- | :--- | :--- |
| `revised_target` | 860 | 97.40% | Target score set via DLS in 23 rain-affected 2nd innings. In all 860 other matches, target is regular `1st innings total + 1`. |
| `first_inn_revised_overs` | 858 | 97.17% | Populated only when match overs were shortened (25 matches). Standard uninterrupted matches default to 20.0 overs. |
| `second_inn_revised_overs` | 858 | 97.17% | Populated only when 2nd innings overs were shortened (25 matches). |
| `away_team_captain_id` | 45 | 5.10% | Unrecorded in abandoned / rained-out matches without official team sheet announcement. |
| `home_team_captain_id` | 44 | 4.98% | Unrecorded in abandoned / rained-out matches without official team sheet announcement. |
| `win_team_id` | 41 | 4.64% | Matches with no winner: 21 `No Result`, 19 `Match Abandoned`, 1 `Match Tied`. |
| `toss_win_team_id` | 15 | 1.70% | Toss never occurred due to pre-match abandonment / rain. |
| `toss_opted` | 15 | 1.70% | Toss never occurred due to pre-match abandonment / rain. |

#### B. `playing_eleven.csv` (28,381 rows)
| Column | Null Count | Null % | Domain Explanation |
| :--- | :--- | :--- | :--- |
| `batting_order` | 8,678 | 30.58% | **8,667 rows** are non-playing squad members (`is_played == False`). The remaining **11 rows** belong to Pakistan in match 48512 where lineup order was omitted in the team sheet. |
| `is_captain` | 8,667 | 30.54% | Null strictly for all non-playing bench squad members (`is_played == False`). |
| `is_wk` | 8,667 | 30.54% | Null strictly for all non-playing bench squad members (`is_played == False`). |

#### C. `ball_by_ball.csv` (200,999 rows)
| Column | Null Count | Null % | Domain Explanation |
| :--- | :--- | :--- | :--- |
| `dismissal_type_id` | 190,118 | 94.59% | Null on all non-wicket deliveries (190,118 non-wicket deliveries). |
| `dismissal_type` | 190,118 | 94.59% | Null on all non-wicket deliveries. Matches `is_wicket == False` exactly. |
| `dismissed_player_id` | 190,107 | 94.58% | Null on non-dismissal balls, with 13 edge cases (12 unexplained departures traced as UNRESOLVED_EXIT, 1 unpopulated ID on Retire Out wicket). |
| `extras_type` | 189,167 | 94.11% | Null on all regular legal deliveries without extras (189,167 balls). |
| `stroke` | 6,158 | 3.06% | Unclassified batting shot (balls left, padded away, or tracking missing). |
| `over_or_around` | 407 | 0.20% | Bowler delivery side (Over/Around the wicket) missing in 407 deliveries. |
| `delivery_style` | 391 | 0.19% | Pitch-tracking trajectory classification missing in 391 deliveries. |

---

## 3. Data Anomalies & Edge Cases

### Anomaly 1: Squad Duplication in `playing_eleven.csv` (Join Multiplication Risk)
- **Observation**: 40 duplicate player records exist across 3 matches (`13613`, `21176`, `28962`), resulting in 75 affected rows.
- **Root Cause**: The data pack contains duplicate squad entries for these matches where players have two differing `batting_order` values (e.g. player 223 listed at both order 5.0 and order 6.0).
- **Risk**: A direct join `ball_by_ball.merge(playing_eleven, on=['match_id', 'player_id'])` will **duplicate delivery rows** for those matches.
- **Remediation**: Downstream pipelines must deduplicate `playing_eleven` or aggregate by `(match_id, player_id)` before joining.

### Anomaly 2: Unresolved Batter Departures / Non-Wicket Exits (12 Deliveries)
- **Observation**: In 12 deliveries across 12 distinct matches, `is_wicket` is `False`, `dismissal_type` is `NaN`, but `dismissed_player_id` is populated with a valid player ID.
- **Empirical Findings**:
  - In all 12 cases, the departed batter never faced another ball in that innings.
  - In 3 of the 12 cases (e.g. Bhanuka Rajapaksa, Krunal Pandya, Mohammad Rizwan), the player listed in `dismissed_player_id` was the **non-striker**, not the striker!
  - `is_wicket` is strictly `False` in all 12 deliveries.
- **Correction of Provisional Assumption**:
  - Automatically labeling all 12 records as medically confirmed 'Retired Hurt' is an unsupported assumption. The source records indicate an exit without official dismissal (which can occur due to tactical retirement, injury, illness, or data collection protocol).
  - **Analytical Consequence**: Because `is_wicket == False`, these deliveries are strictly **NOT team wickets** (the batting team's cumulative wickets fallen does NOT increment). No bowler is credited with a wicket. The departed batter's individual innings ends, and downstream batter metrics must treat this as a non-dismissed innings unless explicit evidence dictates otherwise.
- **Additional Finding**: In row 127899 (match 40709, Hardik Pandya), `dismissal_type` is recorded as `'Retire Out'`, but `dismissed_player_id` is `NaN`. Here `is_wicket == True`, correctly registering as a team wicket lost, but the dismissed player ID must be resolved from `striker_id`.

### Anomaly 3: Extreme & Unrecorded Bowling Speeds (`bowl_speed`)
- **Observation**:
  - `bowl_speed == 0.0`: 77,861 rows (38.74% of all deliveries).
  - `bowl_speed < 0`: 1 row (value `-1.0`).
  - `bowl_speed > 165 km/h`: 3 rows (e.g., `1456.1 km/h`).
- **Root Cause**: Speed guns were not available or unrecorded at certain venues/competitions (especially associate/tri-series matches and spin bowlers). Extreme values represent misplaced decimal points in manual logging (e.g., 145.61 km/h logged as 1456.1).
- **Remediation**: Do not use raw `bowl_speed` as a mandatory feature in pressure modeling without filtering, winsorizing, or imputing.

### Anomaly 4: Abandoned Matches Without Deliveries
- **Observation**: 16 matches in `matches.csv` have **zero deliveries** in `ball_by_ball.csv`.
- **Root Cause**: All 16 matches have `result == 'Match Abandoned'` (e.g. continuous rain before toss or play).
- **Remediation**: This is normal cricket domain behavior. These matches contain no performance data and must be filtered out of player performance aggregations.

### Anomaly 5: Active Players Missing from `playing_eleven.csv`
- **Observation**: Two players (`36153` Syed Haider and `39444` Basil Hameed) appear as active batters/bowlers in `ball_by_ball.csv` for match 37087 (`Mens T20 Emerging Teams Asia Cup 2024`), but are omitted from `playing_eleven.csv` for that match.
- **Root Cause**: Match 37087 has an incomplete lineup log in `playing_eleven.csv`. Both players exist in `competition_team_player_mapping.csv`.
- **Remediation**: Player identity must be sourced directly from `ball_by_ball.csv` and resolved via `competition_team_player_mapping.csv`.

### Anomaly 6: Compound Extras (`extras_2_runs`)
- **Observation**: 36 deliveries have non-zero `extras_2_runs` (20 instances of 1 run, 16 instances of 4 runs).
- **Root Cause**: When a bowler bowls a No Ball (`extras_type == 'Overstep'` or `'other'`) and the ball also beats the keeper for byes/leg-byes or goes to the boundary, `extras1_runs` records the 1-run penalty and `extras_2_runs` records the byes/leg-byes/boundary.
- **Rule**: Total runs scored on any delivery = `runs + extras1_runs + extras_2_runs`.

### Anomaly 7: Distinct Players Sharing Identical Names
- **Observation**: Exactly 7 player names map to two different `player_id`s:
  1. `Abdul Samad` (2 IDs)
  2. `Bashir Ahmad` (2 IDs)
  3. `Basil Hameed` (2 IDs)
  4. `Haider Ali` (2 IDs)
  5. `Mohammad Ali` (2 IDs)
  6. `Muhammad Farooq` (2 IDs)
  7. `Rashid Khan` (2 IDs)
- **Remediation**: **Never aggregate or join on player names**. All downstream grouping, rating, and tracking must use `player_id`.

---

## 4. Candidate Key Validation Matrix

| Table | Candidate Key | Tested | Uniqueness Result | Violations | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **competitions** | `comp_id` | 141 rows | **Strictly Unique (True)** | 0 | **Confirmed Primary Key** |
| **competitions** | `comp_name` | 141 rows | **Strictly Unique (True)** | 0 | Alternate Key |
| **teams** | `team_id` | 353 rows | False | 315 dupes | Surrogate key (shared across comps) |
| **teams** | `(comp_id, team_id)` | 353 rows | **Strictly Unique (True)** | 0 | **Confirmed Primary Key** |
| **matches** | `match_id` | 883 rows | **Strictly Unique (True)** | 0 | **Confirmed Primary Key** |
| **playing_eleven** | `(match_id, player_id)` | 28,381 rows | False | 40 dupes | Duplicate entries in 3 matches |
| **mappings** | `(comp_id, player_id)` | 6,413 rows | **Strictly Unique (True)** | 0 | **Confirmed Primary Key** |
| **mappings** | `(comp_id, team_id, player_id)`| 6,413 rows | **Strictly Unique (True)** | 0 | Alternate Composite Key |
| **ball_by_ball** | `(match_id, innings, innings_ball_num)` | 200,999 rows | **Strictly Unique (True)** | 0 | **Confirmed Primary Key** |
| **ball_by_ball** | `(match_id, innings, overid, over_ball_num)` | 200,999 rows | **Strictly Unique (True)** | 0 | Alternate Composite Key |

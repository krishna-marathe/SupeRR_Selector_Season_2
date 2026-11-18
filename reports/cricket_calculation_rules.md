# SupeRR Selector Season 2 - Cricket Calculation Rules & Domain Logic

This document specifies the exact mathematical, statistical, and domain calculation rules implemented in the match-state reconstruction pipeline. All rules strictly adhere to MCC Laws of Cricket, ICC T20 International Playing Conditions, and IPL Playing Regulations.

---

## 1. Scoring & Runs Attribution

Each row in `ball_by_ball.csv` represents a single physical delivery attempt and contains three primary numerical scoring fields: `runs` (batter runs), `extras1_runs` (primary extra runs), and `extras_2_runs` (secondary / compound extra runs).

### 1.1 Team Runs
The total runs added to the batting team's innings score on any delivery is the sum of off-the-bat runs and all extras:
$$\text{delivery\_total\_team\_runs} = \text{runs} + \text{extras1\_runs} + \text{extras\_2\_runs}$$

### 1.2 Batter Runs Scored
Runs credited to the individual striker's batting scorecard:
$$\text{batter\_runs} = \text{runs}$$
- **Wides**: Batter runs are strictly $0$.
- **Byes & Leg Byes**: Batter runs are strictly $0$.
- **No-Balls**: If the striker hits the ball, `runs` records the runs scored off the bat ($1, 2, 3, 4, 6$).
- **Dot Balls**: When `runs == 0` and `extras1_runs == 0` and `extras_2_runs == 0`.

### 1.3 Bowler Runs Conceded
Runs debited against the bowler's individual bowling analysis:
$$\text{bowler\_runs\_conceded} = \begin{cases} 
\text{runs} + \text{extras1\_runs} & \text{if } \text{extras\_type} \in \{\text{'wide'}, \text{'Overstep'}, \text{'other'}\} \\
\text{runs} & \text{if } \text{extras\_type} \in \{\text{'byes'}, \text{'legbyes'}, \text{'Penalty'}\} \\
\text{runs} + \text{extras1\_runs} & \text{if } \text{extras\_type is NaN}
\end{cases}$$

> **Compound Extras Rule**: Under MCC Law 21, when a bowler delivers a No Ball and the ball also beats the wicketkeeper for byes or leg-byes (recorded in `extras_2_runs`), the bowler is charged **strictly with the 1-run No Ball penalty** (`extras1_runs == 1`) plus any bat runs. Byes and leg-byes occurring on a No Ball are credited to team extras, not debited to the bowler.

---

## 2. Delivery Progression: Legal Balls vs Balls Faced

### 2.1 Legal Deliveries (Over Progression)
A delivery is defined as **legal** if it advances the 6-ball over count:
$$\text{delivery\_is\_legal} = \begin{cases}
\text{False} & \text{if } \text{extras\_type} \in \{\text{'wide'}, \text{'Overstep'}, \text{'other'}\} \\
\text{True} & \text{otherwise (regular delivery, byes, leg-byes, penalty)}
\end{cases}$$
- Illegal deliveries (`wide`, `Overstep`, `other`) must be re-bowled.
- `over_ball_num` (1 to 13) and `innings_ball_num` (1 to 136) track physical delivery attempts, NOT legal deliveries.
- Cumulative legal deliveries bowled before a ball is:
  $$\text{pre\_legal\_balls} = \sum_{i=1}^{n-1} \mathbb{I}(\text{delivery\_is\_legal}_i)$$
- Legal balls remaining in an innings:
  $$\text{pre\_legal\_balls\_remaining} = \max(0, \text{innings\_legal\_ball\_limit} - \text{pre\_legal\_balls})$$

### 2.2 Batter Balls Faced (Batting Statistics)
A delivery is counted on the striker's batting card as a **ball faced** if the batter had the opportunity to play the ball:
$$\text{delivery\_is\_batter\_ball\_faced} = \begin{cases}
\text{False} & \text{if } \text{extras\_type} == \text{'wide'} \\
\text{True} & \text{otherwise (regular delivery, no-balls, byes, leg-byes)}
\end{cases}$$

> **Crucial Distinction**:
> - **Wides**: Neither a legal delivery nor a ball faced by the batter.
> - **No-Balls**: NOT a legal delivery (re-bowled), but IS a ball faced by the batter (credited to striker's balls faced, stroke played, and boundaries).

---

## 3. Wicket & Dismissal Classification

The dataset records `is_wicket` (boolean), `dismissal_type` (string), and `dismissed_player_id` (float). These must be classified into team wickets vs bowler dismissals.

### 3.1 Wickets Lost by Batting Team
A wicket is lost by the batting team if:
$$\text{delivery\_is\_team\_wicket} = (\text{is\_wicket} == \text{True})$$
Total team wickets in dataset: **10,881**.

### 3.2 Dismissals Credited to Bowler
A dismissal is credited to the bowler if and only if it belongs to the official bowler-credited dismissal set:
$$\text{BOWLER\_DISMISSAL\_TYPES} = \{\text{'Caught'}, \text{'Bowled'}, \text{'LBW'}, \text{'Stump'}, \text{'Hit Wicket'}\}$$
$$\text{delivery\_is\_bowler\_wicket} = \text{delivery\_is\_team_wicket} \land (\text{dismissal\_type} \in \text{BOWLER\_DISMISSAL\_TYPES})$$
- Bowler-credited wickets in dataset: **10,272**.
- Fielding / non-bowler wickets: **609** (`RunOut`: 600, `Retire Out`: 6, `Obstructing`: 3). Bowlers are never credited with run-outs or retire-outs.

### 3.3 Unresolved Departures / Non-Wicket Exits (12 Deliveries)
In 12 deliveries, `is_wicket` is `False`, `dismissal_type` is `NaN`, but `dismissed_player_id` is populated with a player ID.
- **Rule**: Because `is_wicket == False`, these deliveries are **NOT wickets**. Team wicket count does NOT increment, and no bowler is credited.
- **Analytical Treatment**: These represent players leaving the field without official dismissal (e.g. retired hurt/ill under Law 25.4). They are flagged in audit logs but preserved as `delivery_is_team_wicket = False` and `delivery_is_bowler_wicket = False`.

---

## 4. Run Rates & Boundary Value Handling

### 4.1 Current Run Rate (CRR)
$$\text{pre\_crr} = \begin{cases}
\text{NaN} & \text{if } \text{pre\_legal\_balls} == 0 \\
\text{round}\left(\frac{\text{pre\_score}}{\text{pre\_legal\_balls}} \times 6.0, 3\right) & \text{if } \text{pre\_legal\_balls} > 0
\end{cases}$$
- **Ball 1 Rule**: Before the first legal ball is bowled, CRR is mathematically undefined ($0/0$). It is safely represented as `NaN`.

### 4.2 Required Run Rate (RRR)
Applicable strictly during chasing innings (`innings \in \{2, 4\}`):
$$\text{pre\_rrr} = \begin{cases}
0.0 & \text{if } \text{pre\_runs\_required} \le 0 \\
\text{NaN} & \text{if } \text{pre\_legal\_balls\_remaining} == 0 \land \text{pre\_runs\_required} > 0 \\
\text{NaN} & \text{if target is unverified / timing unresolved} \\
\text{round}\left(\frac{\text{pre\_runs\_required}}{\text{pre\_legal\_balls\_remaining}} \times 6.0, 3\right) & \text{otherwise}
\end{cases}$$

---

## 5. Match Phase Classification

Match phase provides tactical context for measuring performance against phase-specific baseline expectations:
- **Standard Uninterrupted 20-Over Matches** (`innings_legal_ball_limit == 120`):
  - `Powerplay`: Overs 1 to 6 (`overid \in [1, 6]`, legal balls $0$ to $35$)
  - `Middle`: Overs 7 to 15 (`overid \in [7, 15]`, legal balls $36$ to $89$)
  - `Death`: Overs 16 to 20 (`overid \in [16, 20]`, legal balls $90$ to $119$)
- **Super Overs** (`innings \in [3, 4]`):
  - Classified strictly as `'Super Over'`.
- **Shortened Matches** (`innings_legal_ball_limit < 120`):
  - Classified as `'Shortened'` to avoid applying 20-over phase boundaries to reduced-overs matches.

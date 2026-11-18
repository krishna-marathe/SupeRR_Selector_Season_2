# SupeRR Selector Season 2 - Comprehensive Data Dictionary

This data dictionary documents every table and column provided in the official data pack.
For every field, definitions are explicitly categorized into **Confirmed Meaning**, **Assumptions**, and **Unresolved Questions / Caveats** to maintain analytical rigor and avoid unfounded assumptions.

---

## 1. Table: `competitions.csv`
- **File Purpose**: Catalog of tournament and series identifiers.
- **Row Count**: 141 rows
- **Candidate Key**: `comp_id` (141 unique, 0 nulls), `comp_name` (141 unique, 0 nulls).

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.00%) | 141 | **Confirmed Meaning**: Unique surrogate primary identifier for each tournament or bilateral series.<br>**Assumptions**: Assigned sequentially/arbitrarily by the data provider.<br>**Unresolved Questions**: None. |
| `comp_name` | `string` | 0 (0.00%) | 141 | **Confirmed Meaning**: Official title of the competition (e.g., `IPL 2024`, `ICC Men's T20 World Cup 2024`, bilateral series).<br>**Assumptions**: Human-readable name matches official tournament records.<br>**Unresolved Questions**: Minor naming variations across years (e.g., `Netherlands Tri-Nation T20I Series [Aug 2024] 2024`). |
| `match_format` | `string` | 0 (0.00%) | 2 | **Confirmed Meaning**: Format classification of the competition. Exactly two values: `T20` (franchise/domestic/emerging) and `T20I` (international).<br>**Assumptions**: All matches under a `T20` or `T20I` competition conform to standard Twenty20 rules (20 overs per side).<br>**Unresolved Questions**: Emerging Asia Cup matches are tagged `T20`, whereas regular Asia Cup matches are `T20I`. |
| `season` | `string` | 0 (0.00%) | 8 | **Confirmed Meaning**: Year or cross-year season of the tournament (e.g., `2022`, `2022/23`, `2023`, `2023/24`, `2024`, `2024/25`, `2025`, `2026`).<br>**Assumptions**: Reflects the competition cycle.<br>**Unresolved Questions**: None. The dataset spans 2022 to 2026 (all historical relative to the current date 2026-11-18). |

---

## 2. Table: `teams.csv`
- **File Purpose**: Association between competitions and participating teams.
- **Row Count**: 353 rows
- **Candidate Key**: `(comp_id, team_id)` (353 unique, 0 nulls).

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.00%) | 141 | **Confirmed Meaning**: Foreign key referencing `competitions.comp_id`.<br>**Assumptions**: Team roster and naming scoped to this competition.<br>**Unresolved Questions**: None. |
| `team_id` | `int64` | 0 (0.00%) | 38 | **Confirmed Meaning**: Unique identifier for a cricket team/franchise/national side across all competitions.<br>**Assumptions**: Exactly 38 unique teams exist across the entire dataset.<br>**Unresolved Questions**: None. |
| `team_name` | `string` | 0 (0.00%) | 38 | **Confirmed Meaning**: Official name of the team (e.g., `Rajasthan Royals`, `India`, `Australia`).<br>**Assumptions**: 1:1 bidirectional mapping with `team_id` is verified across all rows.<br>**Unresolved Questions**: None. |

---

## 3. Table: `matches.csv`
- **File Purpose**: Match metadata, scheduling, venue, toss, captains, target adjustments, and match outcomes.
- **Row Count**: 883 rows
- **Candidate Key**: `match_id` (883 unique, 0 nulls).

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.00%) | 883 | **Confirmed Meaning**: Primary key identifying each cricket match.<br>**Assumptions**: Unique match identifier across all competitions.<br>**Unresolved Questions**: None. |
| `comp_id` | `int64` | 0 (0.00%) | 138 | **Confirmed Meaning**: Foreign key referencing `competitions.comp_id`.<br>**Assumptions**: 3 competitions in `competitions.csv` have 0 matches in `matches.csv`.<br>**Unresolved Questions**: Why are comp_ids 3395, 3405, 3406 empty in matches? (Scheduled/unplayed series). |
| `match_number` | `int64` | 0 (0.00%) | 75 | **Confirmed Meaning**: Sequence number of the match within the competition.<br>**Assumptions**: In bilateral series, indicates 1st, 2nd, 3rd match. In leagues, indicates match 1 to 74.<br>**Unresolved Questions**: None. |
| `match_date` | `string` (Date) | 0 (0.00%) | 686 | **Confirmed Meaning**: Calendar date when the match was played (`YYYY-MM-DD`). Ranges from `2022-01-22` to `2026-11-01`.<br>**Assumptions**: Stored in local match date or UTC date.<br>**Unresolved Questions**: None. |
| `stage` | `string` | 0 (0.00%) | 7 | **Confirmed Meaning**: Tournament phase: `League` (620), `Others` (226), `Final` (12), `Qualifier` (10), `Super 4` (6), `Eliminator` (5), `Semi Final` (4).<br>**Assumptions**: `Others` represents bilateral series games; playoff games carry high tournament pressure.<br>**Unresolved Questions**: None. |
| `venue_id` | `int64` | 0 (0.00%) | 98 | **Confirmed Meaning**: Surrogate key identifying the cricket ground.<br>**Assumptions**: Matches venue location uniquely.<br>**Unresolved Questions**: Venue names are not provided in a separate lookup table. |
| `venue_country` | `string` | 0 (0.00%) | 17 | **Confirmed Meaning**: Host nation of the match (e.g., India: 425, UAE: 69, NZ: 52, UK: 49, etc.).<br>**Assumptions**: Useful for home vs away context and pitch characteristics.<br>**Unresolved Questions**: None. |
| `home_team_id` | `int64` | 0 (0.00%) | 36 | **Confirmed Meaning**: Team ID designated as the home team.<br>**Assumptions**: For tournament matches at neutral venues, one team is designated home administratively.<br>**Unresolved Questions**: Neutral venue designation versus genuine home advantage. |
| `home_team` | `string` | 0 (0.00%) | 36 | **Confirmed Meaning**: String name matching `home_team_id`.<br>**Assumptions**: Consistent with `teams.team_name`.<br>**Unresolved Questions**: None. |
| `away_team_id` | `int64` | 0 (0.00%) | 36 | **Confirmed Meaning**: Team ID designated as the away/visiting team.<br>**Assumptions**: Second team listed on the match fixture.<br>**Unresolved Questions**: None. |
| `away_team` | `string` | 0 (0.00%) | 36 | **Confirmed Meaning**: String name matching `away_team_id`.<br>**Assumptions**: Consistent with `teams.team_name`.<br>**Unresolved Questions**: None. |
| `home_team_captain_id` | `Float64` | 44 (4.98%) | 90 | **Confirmed Meaning**: `player_id` of the home team captain.<br>**Assumptions**: Missing in matches abandoned without toss/squad announcement.<br>**Unresolved Questions**: None. |
| `away_team_captain_id` | `Float64` | 45 (5.10%) | 99 | **Confirmed Meaning**: `player_id` of the away team captain.<br>**Assumptions**: Missing in matches abandoned without toss/squad announcement.<br>**Unresolved Questions**: None. |
| `toss_win_team_id` | `Float64` | 15 (1.70%) | 38 | **Confirmed Meaning**: `team_id` of the team that won the coin toss.<br>**Assumptions**: Null only when toss never occurred (abandoned matches).<br>**Unresolved Questions**: None. |
| `toss_opted` | `string` | 15 (1.70%) | 3 | **Confirmed Meaning**: Decision taken by toss winner: `Fielding` (639), `Batting` (229), or `NaN` (15).<br>**Assumptions**: Crucial for knowing who batted first before inspecting ball-by-ball.<br>**Unresolved Questions**: None. |
| `man_of_the_match` | `int64` | 0 (0.00%) | 293 | **Confirmed Meaning**: `player_id` of the Player of the Match award recipient.<br>**Assumptions**: Value `0` indicates no award was given (119 matches: abandoned, no-result, or unawarded).<br>**Unresolved Questions**: None. |
| `first_inn_revised_overs` | `Float64` | 858 (97.17%) | 14 | **Confirmed Meaning**: Scheduled maximum overs for 1st innings when rain/interruptions shortened the game before or during innings 1.<br>**Assumptions**: Standard uninterrupted match is 20.0 overs.<br>**Unresolved Questions**: Must be used during state reconstruction to know inning length when non-null. |
| `second_inn_revised_overs` | `Float64` | 858 (97.17%) | 13 | **Confirmed Meaning**: Scheduled maximum overs for 2nd innings when rain shortened the chase.<br>**Assumptions**: Standard uninterrupted match is 20.0 overs.<br>**Unresolved Questions**: Essential for balls remaining calculations in DLS chases. |
| `revised_target` | `Float64` | 860 (97.40%) | 24 | **Confirmed Meaning**: Official target score set for team batting second under DLS method (23 matches).<br>**Assumptions**: When non-null, this overrides `innings_1_runs + 1`.<br>**Unresolved Questions**: When null, chase target is strictly `1st innings total + 1`. |
| `knock_out` | `int64` | 0 (0.00%) | 2 | **Confirmed Meaning**: Binary flag (1 = Knockout / playoff match, 0 = Group / league / bilateral match). 31 matches have value 1.<br>**Assumptions**: Primary contextual indicator of match pressure.<br>**Unresolved Questions**: None. |
| `win_team_id` | `Float64` | 41 (4.64%) | 37 | **Confirmed Meaning**: `team_id` of the winning team.<br>**Assumptions**: Missing (NaN) in 41 matches (21 `No Result`, 19 `Match Abandoned`, 1 `Match Tied`).<br>**Unresolved Questions**: Match tied (match 45512) was tied without super over resolution or shared trophy. |
| `result` | `string` | 0 (0.00%) | 670 | **Confirmed Meaning**: Descriptive summary of the match outcome (e.g., `West Indies Won by 9 Wickets`, `England Won by 1 Run`, `Match Abandoned`).<br>**Assumptions**: Contains margin of victory and DLS notation.<br>**Unresolved Questions**: None. |

---

## 4. Table: `playing_eleven.csv`
- **File Purpose**: Matchday squad lists, starting XI, designated roles (captain, wicketkeeper), and Impact Player substitutions.
- **Row Count**: 28,381 rows
- **Candidate Key**: Conceptually `(match_id, player_id)`; however, 40 duplicate records exist across 3 matches due to squad duplication.

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.00%) | 880 | **Confirmed Meaning**: Foreign key referencing `matches.match_id`. 3 matches have no p11 records (matches 48513, 36210, 41503 - abandoned without squads).<br>**Assumptions**: Links players to specific matches.<br>**Unresolved Questions**: None. |
| `team_id` | `int64` | 0 (0.00%) | 38 | **Confirmed Meaning**: Team ID to which the player belonged for this match.<br>**Assumptions**: Foreign key referencing `teams.team_id`.<br>**Unresolved Questions**: None. |
| `player_id` | `int64` | 0 (0.00%) | 1082 | **Confirmed Meaning**: Unique player identifier referencing `competition_team_player_mapping.player_id`.<br>**Assumptions**: Identifies the individual cricketer.<br>**Unresolved Questions**: None. |
| `batting_order` | `Float64` | 8,678 (30.58%) | 14 | **Confirmed Meaning**: Nominal pre-match batting lineup order (1.0 to 11.0).<br>**Assumptions**: Null for 8,667 bench/non-playing players (`is_played == False`) and 11 players in match 48512 where lineup order was omitted.<br>**Unresolved Questions**: Differs from actual in-match batting position in `ball_by_ball.batting_order` (e.g. tactical changes). |
| `is_played` | `boolean` | 0 (0.00%) | 2 | **Confirmed Meaning**: Boolean flag indicating whether the player took part in the match (`True`: 19,714, `False`: 8,667).<br>**Assumptions**: Crucial filter: `is_played == False` represents squad reserves/bench warmers.<br>**Unresolved Questions**: None. |
| `is_captain` | `boolean` | 8,667 (30.54%) | 3 | **Confirmed Meaning**: Boolean flag indicating if player was team captain (`True`: 1,683, `False`: 18,031).<br>**Assumptions**: Null for all bench players (`is_played == False`).<br>**Unresolved Questions**: None. |
| `is_wk` | `boolean` | 8,667 (30.54%) | 3 | **Confirmed Meaning**: Boolean flag indicating if player was designated wicketkeeper (`True`: 1,675, `False`: 18,039).<br>**Assumptions**: Null for all bench players (`is_played == False`).<br>**Unresolved Questions**: None. |
| `is_impact` | `int64` | 0 (0.00%) | 2 | **Confirmed Meaning**: Binary flag (1 = Player entered the match as an Impact Player substitution in IPL). 558 occurrences.<br>**Assumptions**: Specific to IPL from 2023 onwards.<br>**Unresolved Questions**: None. |
| `is_impact_off` | `int64` | 0 (0.00%) | 2 | **Confirmed Meaning**: Binary flag (1 = Player was substituted off the field under IPL Impact Player rule). 558 occurrences.<br>**Assumptions**: Substituted off player could still have batted or bowled before substitution.<br>**Unresolved Questions**: None. |

---

## 5. Table: `competition_team_player_mapping.csv`
- **File Purpose**: Master roster mapping players to competitions and teams.
- **Row Count**: 6,413 rows
- **Candidate Key**: `(comp_id, player_id)` (6,413 unique, 0 nulls), `(comp_id, team_id, player_id)` (6,413 unique, 0 nulls).

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.00%) | 140 | **Confirmed Meaning**: Foreign key referencing `competitions.comp_id`.<br>**Assumptions**: Connects player roster to tournament.<br>**Unresolved Questions**: None. |
| `comp_name` | `string` | 0 (0.00%) | 140 | **Confirmed Meaning**: Redundant tournament name matching `competitions.comp_name`.<br>**Assumptions**: Included for denormalized human readability.<br>**Unresolved Questions**: None. |
| `team_id` | `int64` | 0 (0.00%) | 38 | **Confirmed Meaning**: Foreign key referencing `teams.team_id`.<br>**Assumptions**: Team player represented in that competition.<br>**Unresolved Questions**: None. |
| `team_name` | `string` | 0 (0.00%) | 38 | **Confirmed Meaning**: Redundant team name matching `teams.team_name`.<br>**Assumptions**: Included for denormalized human readability.<br>**Unresolved Questions**: None. |
| `player_id` | `int64` | 0 (0.00%) | 1,217 | **Confirmed Meaning**: Master primary identifier for each cricket player across all competitions.<br>**Assumptions**: Persistent across tournaments and years.<br>**Unresolved Questions**: Exactly 1,217 unique players in master registry. |
| `player_name` | `string` | 0 (0.00%) | 1,210 | **Confirmed Meaning**: Full name of the player.<br>**Assumptions**: 1,210 unique names for 1,217 IDs.<br>**Unresolved Questions**: 7 player names belong to 2 distinct players each (e.g., Abdul Samad, Rashid Khan, Haider Ali, Basil Hameed). Never group by player_name alone! |

---

## 6. Table: `ball_by_ball.csv`
- **File Purpose**: Granular delivery-level records (200,999 balls) across 867 matches.
- **Row Count**: 200,999 rows
- **Candidate Key**: `(match_id, innings, innings_ball_num)` (200,999 unique, 0 nulls) AND `(match_id, innings, overid, over_ball_num)` (200,999 unique, 0 nulls).

| Column Name | Inferred Type | Null Count (%) | Unique Values | Description & Technical Details |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.00%) | 867 | **Confirmed Meaning**: Foreign key referencing `matches.match_id`.<br>**Assumptions**: Links delivery to match.<br>**Unresolved Questions**: 16 matches in `matches.csv` have no deliveries (abandoned without play). |
| `innings` | `int64` | 0 (0.00%) | 4 | **Confirmed Meaning**: Innings number: `1` (1st Innings: 105,727), `2` (2nd Innings: 95,234), `3` (Super Over 1: 25), `4` (Super Over 2: 13).<br>**Assumptions**: Super overs must be treated separately from regular innings.<br>**Unresolved Questions**: None. |
| `overid` | `int64` | 0 (0.00%) | 20 | **Confirmed Meaning**: Over sequence number (1 to 20). 1-indexed (Over 1 is overs 0.1-0.6 in standard cricket notation).<br>**Assumptions**: Super overs also use `overid = 1`.<br>**Unresolved Questions**: None. |
| `over_ball_num` | `int64` | 0 (0.00%) | 13 | **Confirmed Meaning**: Sequential ball attempt within the over (1 up to 13).<br>**Assumptions**: Increments on illegal balls (wides/no-balls). NOT identical to legal ball count (0.1 to 0.6).<br>**Unresolved Questions**: Re-bowled balls cause this counter to exceed 6. |
| `innings_ball_num` | `int64` | 0 (0.00%) | 136 | **Confirmed Meaning**: Sequential ball attempt within the innings (1 up to 136).<br>**Assumptions**: Delivery attempt counter, not legal ball counter.<br>**Unresolved Questions**: Legal ball count must be derived by excluding wides and no-balls. |
| `batting_team_id` | `int64` | 0 (0.00%) | 38 | **Confirmed Meaning**: Foreign key referencing `teams.team_id` for batting side.<br>**Assumptions**: Corresponds to team currently at the crease.<br>**Unresolved Questions**: None. |
| `bowling_team_id` | `int64` | 0 (0.00%) | 38 | **Confirmed Meaning**: Foreign key referencing `teams.team_id` for fielding side.<br>**Assumptions**: Corresponds to team currently in the field.<br>**Unresolved Questions**: None. |
| `striker_id` | `int64` | 0 (0.00%) | 888 | **Confirmed Meaning**: `player_id` of the batter facing the delivery.<br>**Assumptions**: Credited with `runs`, boundaries, and facing balls.<br>**Unresolved Questions**: None. |
| `striker_name` | `string` | 0 (0.00%) | 885 | **Confirmed Meaning**: Name of the facing batter.<br>**Assumptions**: Redundant descriptor of `striker_id`.<br>**Unresolved Questions**: Duplicate names exist for different IDs. |
| `non_striker_id` | `int64` | 0 (0.00%) | 867 | **Confirmed Meaning**: `player_id` of the partner at the bowler's end.<br>**Assumptions**: Involved in running and run outs.<br>**Unresolved Questions**: None. |
| `non_striker_name` | `string` | 0 (0.00%) | 864 | **Confirmed Meaning**: Name of non-striking batter.<br>**Assumptions**: Redundant descriptor.<br>**Unresolved Questions**: None. |
| `bowler_id` | `int64` | 0 (0.00%) | 647 | **Confirmed Meaning**: `player_id` of the bowler delivering the ball.<br>**Assumptions**: Debited with runs conceded and credited with bowler wickets.<br>**Unresolved Questions**: None. |
| `bowler_name` | `string` | 0 (0.00%) | 646 | **Confirmed Meaning**: Name of the bowler delivering the ball.<br>**Assumptions**: Redundant descriptor.<br>**Unresolved Questions**: None. |
| `batting_type` | `string` | 0 (0.00%) | 2 | **Confirmed Meaning**: Batter handedness: `RHB` (Right-Handed: 131,006), `LHB` (Left-Handed: 69,993).<br>**Assumptions**: Tactical matchup indicator for split analysis.<br>**Unresolved Questions**: None. |
| `bowling_type` | `string` | 0 (0.00%) | 12 | **Confirmed Meaning**: Detailed bowling style (e.g., `Right-arm Fast`, `Slow left-arm orthodox`, `Left-arm Chinaman`, etc.).<br>**Assumptions**: Useful for bowler archetype clustering.<br>**Unresolved Questions**: None. |
| `batting_order` | `int64` | 0 (0.00%) | 13 | **Confirmed Meaning**: Actual batting position (1 to 13) at which the striker walked out to bat in this innings.<br>**Assumptions**: 1-2 = Openers, 3-4 = Top order, 5-7 = Middle/lower-middle, 8-11 = Tail, 12-13 = Impact sub / injury replacement.<br>**Unresolved Questions**: Differs from `playing_eleven.batting_order` when lineups are shuffled in-match. |
| `runs` | `int64` | 0 (0.00%) | 7 | **Confirmed Meaning**: Runs scored strictly off the bat by the striker (values: 0, 1, 2, 3, 4, 5, 6).<br>**Assumptions**: On wides and byes/leg-byes, `runs == 0`.<br>**Unresolved Questions**: On no-balls where batter hits, `runs` holds the bat runs while `extras1_runs` holds 1. |
| `is_four` | `boolean` | 0 (0.00%) | 2 | **Confirmed Meaning**: Boolean flag indicating if the delivery resulted in a boundary four (23,283 True).<br>**Assumptions**: 20 instances where `runs == 4` but `is_four == False` correspond to run-fours or overthrows.<br>**Unresolved Questions**: None. |
| `is_six` | `boolean` | 0 (0.00%) | 2 | **Confirmed Meaning**: Boolean flag indicating if the delivery resulted in a boundary six (12,811 True).<br>**Assumptions**: 3 instances where `runs == 6` but `is_six == False` correspond to running overthrows.<br>**Unresolved Questions**: None. |
| `is_wicket` | `boolean` | 0 (0.00%) | 2 | **Confirmed Meaning**: Boolean flag indicating an official fall of wicket (10,881 True).<br>**Assumptions**: Exactly matches `dismissal_type.notna()`.<br>**Unresolved Questions**: Does NOT flag 12 unexplained batter exit deliveries (`is_wicket == False`, `dismissal_type == NaN`, but `dismissed_player_id` populated). Traced in `validation_and_reconciliation.md` as non-returning batter departures (`UNRESOLVED_EXIT`). |
| `dismissal_type_id` | `Float64` | 190,118 (94.59%) | 9 | **Confirmed Meaning**: Numeric code identifying dismissal category.<br>**Assumptions**: Null on non-wicket balls and 1 Retired Out ball.<br>**Unresolved Questions**: None. |
| `dismissal_type` | `string` | 190,118 (94.59%) | 10 | **Confirmed Meaning**: Classification of dismissal: `Caught` (7557), `Bowled` (1775), `LBW` (709), `RunOut` (600), `Stump` (214), `Hit Wicket` (17), `Retire Out` (6), `Obstracting the field` (2), `Obstructing the field` (1).<br>**Assumptions**: Bowler credited wickets = Caught, Bowled, LBW, Stump, Hit Wicket (total: 10,272). Fielding dismissals = RunOut, Retire Out, Obstructing.<br>**Unresolved Questions**: Spelling typo in `Obstracting the field`. Excludes the 12 unexplained departure incidents. |
| `dismissed_player_id` | `Float64` | 190,107 (94.58%) | 815 | **Confirmed Meaning**: `player_id` of the batter dismissed or leaving the field.<br>**Assumptions**: Can be striker OR non-striker (e.g. run out at non-striker end).<br>**Unresolved Questions**: Set in 12 non-wicket deliveries (unexplained batter departures; classified as `UNRESOLVED_EXIT`), and unpopulated in 1 `Retire Out` wicket (Match 40709, Ball 127899). In the reconstruction pipeline, the automatic striker fallback was removed to preserve raw NaN ground truth while retaining team-wicket status. |
| `extras_type` | `string` | 189,167 (94.11%) | 7 | **Confirmed Meaning**: Category of extras: `wide` (7,714), `legbyes` (2,748), `Overstep` (576), `byes` (529), `other` (264), `Penalty` (1), `NaN` (189,167).<br>**Assumptions**: `Overstep` and `other` represent No Balls.<br>**Unresolved Questions**: 2 anomaly rows where extras_type is NaN but extras1_runs or extras_2_runs > 0. |
| `extras1_runs` | `int64` | 0 (0.00%) | 6 | **Confirmed Meaning**: Primary extra runs awarded on the delivery (e.g., 1 for wide, 1 for overstep no-ball, 1-4 for byes/leg-byes, 5 for penalty).<br>**Assumptions**: Bowler is charged for wides and no-balls, but not byes/leg-byes.<br>**Unresolved Questions**: None. |
| `extras_2_runs` | `int64` | 0 (0.00%) | 3 | **Confirmed Meaning**: Secondary extra runs on compound delivery events (36 occurrences: 20 times 1 run, 16 times 4 runs).<br>**Assumptions**: Occurs when a No Ball (`Overstep` or `other`) is accompanied by byes, leg-byes, or overthrows.<br>**Unresolved Questions**: Total delivery runs = `runs + extras1_runs + extras_2_runs`. |
| `pace_or_spin` | `string` | 0 (0.00%) | 2 | **Confirmed Meaning**: Categorical classification of bowling type: `Pace` (123,886) vs `Spin` (77,113).<br>**Assumptions**: Reliable macro-level bowling category.<br>**Unresolved Questions**: None. |
| `bowl_speed` | `float64` | 0 (0.00%) | 1033 | **Confirmed Meaning**: Recorded delivery speed in km/h.<br>**Assumptions**: Median speed is 91.7 km/h.<br>**Unresolved Questions**: 77,861 rows (38.74%) have `bowl_speed == 0.0` (unrecorded/no speed radar). Values like `-1.0` and `1456.1` indicate data entry scaling bugs. Cannot be used without imputation/filtering. |
| `stroke` | `string` | 6,158 (3.06%) | 31 | **Confirmed Meaning**: Classification of the batting shot played (e.g., `Pull shot`, `Cover Drive`, `Frontfoot defensive`, etc.).<br>**Assumptions**: Coded by video analysts.<br>**Unresolved Questions**: 6,158 missing values on unplayed/left deliveries or missing tracking. |
| `delivery_style` | `string` | 391 (0.19%) | 35 | **Confirmed Meaning**: Trajectory/variation of the ball (e.g., `Seamed In`, `Orthodox`, `Leg Break`, `Off Cutter`, `Googly`, `Yorker`, etc.).<br>**Assumptions**: Pitch-tracking / analyst classification.<br>**Unresolved Questions**: 391 missing values. |
| `over_or_around` | `string` | 407 (0.20%) | 3 | **Confirmed Meaning**: Bowler delivery side relative to the stumps: `Over` (154,670), `Around` (45,922), `NaN` (407).<br>**Assumptions**: Crucial bowling angle context.<br>**Unresolved Questions**: 407 missing values. |
| `on_or_off` | `string` | 0 (0.00%) | 2 | **Confirmed Meaning**: Pitch landing or shot sector: `Off-side` (104,875) vs `On-side` (96,124).<br>**Assumptions**: Macro field sector distribution.<br>**Unresolved Questions**: None. |
| `delivery_ist_time` | `string` (Timestamp) | 0 (0.00%) | 200,826 | **Confirmed Meaning**: Timestamp of delivery recording in Indian Standard Time formatted string (`YYYY-MM-DD HH:MM:SS UTC`).<br>**Assumptions**: Provides chronological ordering within over/match.<br>**Unresolved Questions**: Labeled `ist_time` but contains `UTC` suffix string. Chronology within match is already strictly guaranteed by `innings`, `overid`, and `innings_ball_num`. |

# SupeRR Selector Season 2 - Coverage Analysis

This report documents the geographical, seasonal, competitive, and player coverage of the supplied data pack.

---

## 1. Executive Coverage Overview

| Metric | Metric Count | Notes |
| :--- | :--- | :--- |
| **Total Competitions** | 141 | 138 with scheduled matches; 3 scheduled future/unplayed series |
| **Total Matches** | 883 | 867 played with ball-by-ball records; 16 abandoned without play |
| **Total Deliveries** | 200,999 | Complete ball-by-ball records |
| **Total Teams** | 38 | 10 IPL franchises, 12 Full Member nations, 11 Associate nations, 5 'A' sides |
| **Total Players Mapped** | 1,217 | Master player registry in `competition_team_player_mapping.csv` |
| **Players in Playing XIs** | 1,082 | Players named in matchday squads in `playing_eleven.csv` |
| **Active Strikers** | 888 | Distinct batters who faced at least one delivery in `ball_by_ball.csv` |
| **Active Bowlers** | 647 | Distinct bowlers who bowled at least one delivery in `ball_by_ball.csv` |
| **Calendar Span** | 2022-01-22 to 2026-11-01 | Covers 4.8 calendar years (2022 through 2026) |

---

## 2. Explicit Competition Categories & Coverage

Competitions are explicitly classified into 5 distinct categories, ensuring domestic emerging tournaments are distinctly identified from senior international and franchise competitions:

| Category | Description | Competitions Count | Matches Count | Deliveries Count | Date Range |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IPL (Franchise)** | Senior domestic franchise tournament (IPL seasons 2022 to 2026) | 5 | 371 | 88,811 | 2022-03-26 to 2026-05-31 |
| **Emerging Teams (T20)** | Men's T20 Emerging Teams Asia Cup (2024) & Asia Cup Rising Stars (2025) | 2 | 30 | 4,001 | 2024-10-18 to 2025-11-23 |
| **Bilateral Series (T20I)** | Official bilateral international tours between national teams | 123 | 411 | 91,446 | 2022-01-22 to 2026-11-01 |
| **Multi-Nation Tournament (T20I)** | Senior Asia Cup (2022, 2025) and Asia Cup Qualifiers (2022) | 3 | 38 | 8,879 | 2022-08-20 to 2025-09-28 |
| **International Tri-Series (T20I)** | Multi-team tri-nation international series (NZ, Netherlands, UAE, Pakistan) | 5 | 33 | 7,862 | 2022-10-07 to 2025-11-29 |
| **Total** | | **138 with matches** | **883** | **200,999** | **2022-01-22 to 2026-11-01** |

> [!IMPORTANT]
> **Season Completeness Note**: Match and delivery counts alone do not imply calendar completeness of international T20 cricket. International bilateral series are scheduled asynchronously via the ICC Future Tours Programme (FTP). Furthermore, dates spanning 2025 and 2026 reflect tournament calendar schedules and projected records in the data pack. Emerging team tournaments involve 'A' teams and junior national prospects and must be analyzed with explicit category controls.

---

## 3. Season & Format Distribution Matrix

The dataset spans from 2022 to 2026, including complete data for recent and upcoming seasons:

| Season | Domestic / Franchise T20 | International T20I | Total Matches | Matches with Ball-By-Ball | Abandoned Matches | Total Deliveries |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2022** | 74 (IPL 2022) | 94 | 168 | 168 | 0 | 39,268 |
| **2022/23** | 0 | 12 | 12 | 12 | 0 | 2,752 |
| **2023** | 74 (IPL 2023) | 63 | 137 | 137 | 0 | 31,902 |
| **2023/24** | 0 | 3 | 3 | 3 | 0 | 702 |
| **2024** | 89 (IPL + Emerging) | 109 | 198 | 190 | 8 | 44,057 |
| **2024/25** | 0 | 3 | 3 | 3 | 0 | 707 |
| **2025** | 90 (IPL + Rising Stars) | 126 | 216 | 210 | 6 | 48,930 |
| **2026** | 74 (IPL 2026) | 72 | 146 | 144 | 2 | 32,681 |
| **All Seasons** | **401** | **482** | **883** | **867** | **16** | **200,999** |

---

## 4. Key Competitions Coverage

### 4.1 Indian Premier League (IPL)
Every IPL season from 2022 to 2026 is fully represented with full fixture lists and ball-by-ball delivery records:
- **IPL 2022**: 74 matches (2022-03-26 to 2022-05-29) - 17,988 balls
- **IPL 2023**: 74 matches (2023-03-31 to 2023-05-29) - 17,863 balls
- **IPL 2024**: 74 matches (2024-03-22 to 2024-05-26) - 17,211 balls (3 matches abandoned)
- **IPL 2025**: 75 matches (2025-03-22 to 2025-06-03) - 17,867 balls (1 match abandoned)
- **IPL 2026**: 74 matches (2026-03-28 to 2026-05-31) - 17,882 balls

### 4.2 International & Multi-Nation Tournaments
- **Asia Cup 2025**: 19 matches
- **Mens Twenty20 Asia Cup 2022**: 13 matches
- **Mens T20 Emerging Teams Asia Cup 2024**: 15 matches
- **Asia Cup Rising Stars 2025**: 15 matches
- **Tri-Series & Bilaterals**: High volume of matches involving England, India, Pakistan, Australia, South Africa, New Zealand, West Indies, Sri Lanka, Afghanistan, Bangladesh, Ireland, and Zimbabwe.

---

## 5. Tournament Stages & Pressure Environments

The dataset includes explicit match stages, offering clear differentiation between high-stakes knockout games and regular league games:

| Match Stage | Match Count | Knockout Flag (`knock_out == 1`) | Pressure Context |
| :--- | :--- | :--- | :--- |
| **League** | 620 | 0 | Regular season points matches |
| **Others** | 226 | 0 | Bilateral series encounters |
| **Final** | 12 | 12 | Direct championship deciders |
| **Qualifier** | 10 | 10 | Playoff qualification games |
| **Super 4** | 6 | 0 | Multi-nation tournament second round |
| **Eliminator** | 5 | 5 | Do-or-die playoff elimination |
| **Semi Final** | 4 | 4 | Direct tournament knockout |
| **Total** | **883** | **31** | **31 official knockout games** |

---

## 6. Geographical & Venue Coverage

Matches were contested across 17 host nations and 98 distinct venues:

| Host Country | Matches Played | Major Venues Included |
| :--- | :--- | :--- |
| **India** | 425 | Wankhede Stadium, Eden Gardens, Narendra Modi Stadium, Chinnaswamy, Chepauk |
| **United Arab Emirates** | 69 | Dubai International Stadium, Sharjah Cricket Stadium, Zayed Stadium Abu Dhabi |
| **New Zealand** | 52 | Eden Park Auckland, Hagley Oval Christchurch, Seddon Park Hamilton |
| **United Kingdom** | 49 | Lord's, The Oval, Edgbaston, Old Trafford, Trent Bridge, Headingley |
| **West Indies** | 44 | Kensington Oval Barbados, Brian Lara Stadium Trinidad, National Stadium Guyana |
| **Zimbabwe** | 38 | Harare Sports Club, Queens Sports Club Bulawayo |
| **Pakistan** | 36 | Gaddafi Stadium Lahore, National Stadium Karachi, Rawalpindi Cricket Stadium |
| **Bangladesh** | 34 | Sher-e-Bangla National Cricket Stadium Mirpur, Sylhet International Stadium |
| **Sri Lanka** | 26 | R. Premadasa Stadium Colombo, Pallekele International Cricket Stadium |
| **Australia** | 24 | MCG, SCG, Adelaide Oval, Perth Stadium, The Gabba |
| **Oman** | 21 | Al Amerat Cricket Ground Muscat |
| **South Africa** | 18 | Wanderers Johannesburg, SuperSport Park Centurion, Newlands Cape Town |
| **Qatar** | 15 | West End Park International Cricket Stadium Doha |
| **Netherlands** | 14 | VRA Cricket Ground Amstelveen, Hazelaarweg Rotterdam |
| **Ireland** | 10 | Malahide Cricket Club Dublin, Bready Cricket Club |
| **United States** | 7 | Central Broward Regional Park Lauderhill, Grand Prairie Stadium Texas |
| **Japan** | 1 | Sano International Cricket Ground |

---

## 7. Player Volume & Role Demographics

- **Master Player Registry**: 1,217 distinct cricketers across international and franchise teams.
- **Batters**:
  - 888 players have faced at least one ball.
  - Handedness: 131,006 deliveries faced by Right-Hand Batters (RHB, 65.18%); 69,993 faced by Left-Hand Batters (LHB, 34.82%).
- **Bowlers**:
  - 647 players have delivered at least one ball.
  - Bowling style split: 123,886 deliveries by Pace bowlers (61.64%); 77,113 deliveries by Spin bowlers (38.36%).
  - 12 distinct bowling sub-types recorded (Right-arm Leg-Break, Right-arm medium-fast, Right-arm Fast, Slow left-arm orthodox, etc.).
- **Impact Players**:
  - 558 instances of Impact Players entering the game (`is_impact == 1`).
  - 558 instances of players being substituted off (`is_impact_off == 1`).

import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

import pandas as pd
import numpy as np
from config.settings import settings

b_all = pd.read_csv(settings.OUTPUTS_DIR / 'tables' / 'batting_rankings_all.csv')
bw_all = pd.read_csv(settings.OUTPUTS_DIR / 'tables' / 'bowling_rankings_all.csv')
pme = pd.read_csv(settings.OUTPUTS_DIR / 'tables' / 'player_match_evidence.csv')
mappings = pd.read_csv(settings.MAPPINGS_PATH)

target_names = [
    'Rashid Khan', 'Abdul Samad', 'Haider Ali', 'Basil Hameed',
    'Muhammad Farooq', 'Bashir Ahmad', 'Mahendra Singh Dhoni',
    'Piyush Chawla', 'Ishant Sharma', 'Nathan Bracken', 'Virat Kohli',
    'Faf du Plessis', 'Wriddhiman Saha', 'Rohit Sharma', 'Shikhar Dhawan',
    'Dinesh Karthik', 'Pradeep Sangwan', 'Ravindra Jadeja',
    'Amit Mishra', 'Dwayne Bravo'
]

print("=== Batting Rankings matches ===")
for n in target_names:
    sub = b_all[b_all['player_name'].str.contains(n, case=False, na=False)]
    if len(sub) > 0:
        for _, r in sub.iterrows():
            print(f"Batter: {r['player_name']} (ID: {r['player_id']}) - Rank: {r['rank']}, Conserv: {r['conservative_score']:.3f}, P_Balls: {r['p_balls']}, P_Matches: {r['p_matches']}, NP_Balls: {r['np_balls']}")
    else:
        print(f"Batter: {n} -> NOT IN BATTING ELIGIBLE RANKINGS")

print("\n=== Bowling Rankings matches ===")
for n in target_names:
    sub = bw_all[bw_all['player_name'].str.contains(n, case=False, na=False)]
    if len(sub) > 0:
        for _, r in sub.iterrows():
            print(f"Bowler: {r['player_name']} (ID: {r['player_id']}) - Rank: {r['rank']}, Conserv: {r['conservative_score']:.3f}, P_Balls: {r['pressure_balls']}, P_Matches: {r['p_matches']}, NP_Balls: {r['np_balls']}")
    else:
        print(f"Bowler: {n} -> NOT IN BOWLING ELIGIBLE RANKINGS")

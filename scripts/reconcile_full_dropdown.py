import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

import pandas as pd
import numpy as np
from config.settings import settings
from src.analysis.preflight import run_preflight
from src.analysis.pressure import apply_pressure_definitions

# 1. Load usable senior dataset
matches = pd.read_csv(settings.MATCHES_PATH)
df_senior, _, _ = run_preflight()
df_aug, _, _ = apply_pressure_definitions(df_senior, matches)

# Also check mappings
mappings = pd.read_csv(settings.MAPPINGS_PATH)

target_names = [
    'Rashid Khan', 'Abdul Samad', 'Haider Ali', 'Basil Hameed',
    'Muhammad Farooq', 'Bashir Ahmad', 'Mahendra Singh Dhoni',
    'Piyush Chawla', 'Ishant Sharma', 'Nathan Bracken', 'Virat Kohli',
    'Faf du Plessis', 'Wriddhiman Saha', 'Rohit Sharma', 'Shikhar Dhawan',
    'Dinesh Karthik', 'Pradeep Sangwan', 'Ravindra Jadeja',
    'Amit Mishra', 'Dwayne Bravo'
]

results = []

for n in target_names:
    sub_map = mappings[mappings['player_name'].str.contains(n, case=False, na=False)][['player_id', 'player_name']].drop_duplicates()
    for _, r in sub_map.iterrows():
        pid = r['player_id']
        pname = r['player_name']
        
        # Batting stats
        bat_balls = df_aug[(df_aug['striker_id'] == pid) & (df_aug['delivery_is_batter_ball_faced'] == True)]
        bat_p_balls = bat_balls[bat_balls['is_pressure_benchmark'] == True]
        bat_np_balls = bat_balls[bat_balls['is_pressure_benchmark'] == False]
        
        n_bat_p_balls = len(bat_p_balls)
        n_bat_p_matches = bat_p_balls['match_id'].nunique()
        n_bat_np_balls = len(bat_np_balls)
        
        # Bowling stats
        bowl_balls = df_aug[(df_aug['bowler_id'] == pid) & (df_aug['delivery_is_legal'] == True)]
        bowl_p_balls = bowl_balls[bowl_balls['is_pressure_benchmark'] == True]
        bowl_np_balls = bowl_balls[bowl_balls['is_pressure_benchmark'] == False]
        
        n_bowl_p_balls = len(bowl_p_balls)
        n_bowl_p_matches = bowl_p_balls['match_id'].nunique()
        n_bowl_np_balls = len(bowl_np_balls)
        
        # Total overall appearances in senior dataset
        all_appearances = len(df_aug[(df_aug['striker_id'] == pid) | (df_aug['bowler_id'] == pid) | (df_aug['non_striker_id'] == pid)])
        
        results.append({
            'query_name': n,
            'player_id': pid,
            'player_name': pname,
            'senior_total_deliveries': all_appearances,
            'bat_p_balls': n_bat_p_balls,
            'bat_p_matches': n_bat_p_matches,
            'bat_np_balls': n_bat_np_balls,
            'bowl_p_balls': n_bowl_p_balls,
            'bowl_p_matches': n_bowl_p_matches,
            'bowl_np_balls': n_bowl_np_balls,
        })

df_res = pd.DataFrame(results)
print(df_res.to_string())

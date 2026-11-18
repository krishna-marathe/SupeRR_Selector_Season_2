import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

import pandas as pd
import numpy as np
from config.settings import settings
from src.analysis.preflight import run_preflight
from src.analysis.pressure import apply_pressure_definitions
from src.models.expected_performance import evaluate_and_score_models

# Load files
matches = pd.read_csv(settings.MATCHES_PATH)
mappings = pd.read_csv(settings.MAPPINGS_PATH)
b_all = pd.read_csv(settings.OUTPUTS_DIR / 'tables' / 'batting_rankings_all.csv')
bw_all = pd.read_csv(settings.OUTPUTS_DIR / 'tables' / 'bowling_rankings_all.csv')

df_senior, _, _ = run_preflight()
df_aug, _, _ = apply_pressure_definitions(df_senior, matches)
df_scored, _, _ = evaluate_and_score_models(df_aug)

# Residuals
df_scored['res_bat_runs'] = df_scored['delivery_runs'] - df_scored['exp_batter_runs']
df_scored['res_bat_surv'] = df_scored['exp_striker_dismissal_prob'] - df_scored['is_striker_dismissal'].astype(float)
df_scored['res_bowl_prev'] = df_scored['exp_bowler_conceded_runs'] - df_scored['delivery_bowler_runs_conceded']
df_scored['res_bowl_wkt'] = df_scored['delivery_is_bowler_wicket'].astype(float) - df_scored['exp_bowler_wicket_prob']

# Target names in dropdown order
target_names = [
    "Rashid Khan", "Abdul Samad", "Haider Ali", "Basil Hameed",
    "Muhammad Farooq", "Bashir Ahmad", "Mahendra Singh Dhoni",
    "Piyush Chawla", "Ishant Sharma", "Nathan Bracken", "Virat Kohli",
    "Faf du Plessis", "Wriddhiman Saha", "Rohit Sharma", "Shikhar Dhawan",
    "Dinesh Karthik", "Pradeep Sangwan", "Ravindra Jadeja",
    "Amit Mishra", "Dwayne Bravo"
]

# Primary eligibility thresholds
B_MIN_P_BALLS = 100
B_MIN_P_MATCHES = 10
B_MIN_NP_BALLS = 100

BW_MIN_P_LEGAL = 100
BW_MIN_P_MATCHES = 10
BW_MIN_NP_LEGAL = 100

rows = []

for name in target_names:
    sub_map = mappings[mappings['player_name'].str.contains(name, case=False, na=False)][['player_id', 'player_name', 'team_name']].drop_duplicates()
    unique_ids = sub_map['player_id'].unique()
    
    for pid in unique_ids:
        p_name = sub_map[sub_map['player_id'] == pid]['player_name'].iloc[0]
        teams = ", ".join(sub_map[sub_map['player_id'] == pid]['team_name'].unique()[:3])
        
        # --- BATTING ROLE ---
        df_bat = df_scored[(df_scored['striker_id'] == pid) & (df_scored['delivery_is_batter_ball_faced'] == True)]
        bat_p = df_bat[df_bat['is_pressure_benchmark'] == True]
        bat_np = df_bat[df_bat['is_pressure_benchmark'] == False]
        
        b_p_balls = len(bat_p)
        b_p_matches = bat_p['match_id'].nunique()
        b_np_balls = len(bat_np)
        
        # Check eligibility
        b_reasons = []
        if b_p_balls < B_MIN_P_BALLS:
            b_reasons.append(f"Pressure balls < {B_MIN_P_BALLS} ({b_p_balls})")
        if b_p_matches < B_MIN_P_MATCHES:
            b_reasons.append(f"Pressure matches < {B_MIN_P_MATCHES} ({b_p_matches})")
        if b_np_balls < B_MIN_NP_BALLS:
            b_reasons.append(f"Baseline balls < {B_MIN_NP_BALLS} ({b_np_balls})")
            
        b_eligible = len(b_reasons) == 0
        b_status = "Eligible" if b_eligible else "Excluded"
        b_excl_reason = "None (Eligible)" if b_eligible else "; ".join(b_reasons)
        
        # Batting score lookup
        in_b_all = b_all[b_all['player_id'] == pid]
        if len(in_b_all) > 0:
            b_rank = in_b_all['rank'].iloc[0]
            b_cons = in_b_all['conservative_score'].iloc[0]
            b_cent = in_b_all['central_score'].iloc[0]
            b_ci = f"[{in_b_all['ci_lower'].iloc[0]:.3f}, {in_b_all['ci_upper'].iloc[0]:.3f}]"
            b_score_status = "Official Baseline"
        elif b_p_balls > 0:
            # Exploratory estimate
            r_run = bat_p['res_bat_runs'].sum() / b_p_balls
            r_surv = bat_p['res_bat_surv'].sum() / b_p_balls
            b_rank = "N/A (Ineligible)"
            b_cons = "N/A"
            b_cent = round(0.6 * (r_run / 0.35) + 0.4 * (r_surv / 0.04), 3)
            b_ci = "N/A"
            b_score_status = "Exploratory (Insufficient Sample)"
        else:
            b_rank = "N/A (No Balls)"
            b_cons = "N/A"
            b_cent = "N/A"
            b_ci = "N/A"
            b_score_status = "No Pressure Data"
            
        rows.append({
            "dropdown_name": name,
            "resolved_player_id": pid,
            "dataset_player_name": p_name,
            "associated_teams": teams,
            "role": "Batter",
            "pressure_balls": b_p_balls,
            "pressure_matches": b_p_matches,
            "non_pressure_balls": b_np_balls,
            "eligibility_status": b_status,
            "exact_exclusion_reason": b_excl_reason,
            "official_rank": b_rank,
            "conservative_score_q05": b_cons,
            "central_score": b_cent,
            "score_90_ci": b_ci,
            "score_classification": b_score_status,
        })
        
        # --- BOWLING ROLE ---
        df_bowl = df_scored[(df_scored['bowler_id'] == pid) & (df_scored['delivery_is_legal'] == True)]
        bowl_p = df_bowl[df_bowl['is_pressure_benchmark'] == True]
        bowl_np = df_bowl[df_bowl['is_pressure_benchmark'] == False]
        
        bw_p_balls = len(bowl_p)
        bw_p_matches = bowl_p['match_id'].nunique()
        bw_np_balls = len(bowl_np)
        
        bw_reasons = []
        if bw_p_balls < BW_MIN_P_LEGAL:
            bw_reasons.append(f"Pressure legal balls < {BW_MIN_P_LEGAL} ({bw_p_balls})")
        if bw_p_matches < BW_MIN_P_MATCHES:
            bw_reasons.append(f"Pressure matches < {BW_MIN_P_MATCHES} ({bw_p_matches})")
        if bw_np_balls < BW_MIN_NP_LEGAL:
            bw_reasons.append(f"Baseline legal balls < {BW_MIN_NP_LEGAL} ({bw_np_balls})")
            
        bw_eligible = len(bw_reasons) == 0
        bw_status = "Eligible" if bw_eligible else "Excluded"
        bw_excl_reason = "None (Eligible)" if bw_eligible else "; ".join(bw_reasons)
        
        in_bw_all = bw_all[bw_all['player_id'] == pid]
        if len(in_bw_all) > 0:
            bw_rank = in_bw_all['rank'].iloc[0]
            bw_cons = in_bw_all['conservative_score'].iloc[0]
            bw_cent = in_bw_all['central_score'].iloc[0]
            bw_ci = f"[{in_bw_all['ci_lower'].iloc[0]:.3f}, {in_bw_all['ci_upper'].iloc[0]:.3f}]"
            bw_score_status = "Official Baseline"
        elif bw_p_balls > 0:
            r_prev = bowl_p['res_bowl_prev'].sum() / bw_p_balls
            r_wkt = bowl_p['res_bowl_wkt'].sum() / bw_p_balls
            bw_rank = "N/A (Ineligible)"
            bw_cons = "N/A"
            bw_cent = round(0.6 * (r_prev / 0.30) + 0.4 * (r_wkt / 0.035), 3)
            bw_ci = "N/A"
            bw_score_status = "Exploratory (Insufficient Sample)"
        else:
            bw_rank = "N/A (No Balls)"
            bw_cons = "N/A"
            bw_cent = "N/A"
            bw_ci = "N/A"
            bw_score_status = "No Pressure Data"
            
        rows.append({
            "dropdown_name": name,
            "resolved_player_id": pid,
            "dataset_player_name": p_name,
            "associated_teams": teams,
            "role": "Bowler",
            "pressure_balls": bw_p_balls,
            "pressure_matches": bw_p_matches,
            "non_pressure_balls": bw_np_balls,
            "eligibility_status": bw_status,
            "exact_exclusion_reason": bw_excl_reason,
            "official_rank": bw_rank,
            "conservative_score_q05": bw_cons,
            "central_score": bw_cent,
            "score_90_ci": bw_ci,
            "score_classification": bw_score_status,
        })

df_reconciliation = pd.DataFrame(rows)
out_path = settings.OUTPUTS_DIR / "tables" / "dropdown_player_reconciliation.csv"
df_reconciliation.to_csv(out_path, index=False)
print(f"Exported dropdown reconciliation to {out_path} ({len(df_reconciliation)} rows).")

# Print summary
print("\n=== ELIGIBILITY SUMMARY FOR DROPDOWN CANDIDATES ===")
print(df_reconciliation[df_reconciliation['eligibility_status'] == 'Eligible'][['dropdown_name', 'resolved_player_id', 'role', 'pressure_balls', 'pressure_matches', 'official_rank', 'conservative_score_q05']])

print("\n=== EXCLUDED PLAYERS BREAKDOWN ===")
print(df_reconciliation[df_reconciliation['eligibility_status'] == 'Excluded'][['dropdown_name', 'resolved_player_id', 'role', 'pressure_balls', 'pressure_matches', 'exact_exclusion_reason']].head(15))

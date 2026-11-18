import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
import pandas as pd
import numpy as np

# Load reconstructed match states
df = pd.read_parquet(settings.OUTPUTS_DIR / 'match_states.parquet')
matches = pd.read_csv(settings.MATCHES_PATH)
bbb = pd.read_csv(settings.BALL_BY_BALL_PATH)
p11 = pd.read_csv(settings.PLAYING_ELEVEN_PATH)
mappings = pd.read_csv(settings.MAPPINGS_PATH)
players = mappings[['player_id', 'player_name']].drop_duplicates()
reconcil = pd.read_csv(settings.OUTPUTS_DIR / 'reconciliation_checks.csv')

print("=== 1. MATCH 13511 INNINGS 2 TRACE ===")
m13511 = df[(df['match_id'] == 13511) & (df['innings'] == 2)].sort_values('innings_ball_num').copy()
m13511['legal_balls_after'] = m13511['pre_legal_balls'] + m13511['delivery_is_legal'].astype(int)

# Check last 5 balls
print("Tail of Match 13511 Inn 2:")
cols = ['innings_ball_num', 'overid', 'pre_legal_balls', 'legal_balls_after', 'pre_score', 'pre_runs_required', 'pre_rrr', 'delivery_runs', 'delivery_total_team_runs', 'striker_name', 'bowler_name']
print(m13511[cols].tail(6).to_string())

print("\nExplanation of 103 balls vs Over 18.1 / 17.1:")
last_row = m13511.iloc[-1]
print(f"Final delivery physical attempt: {last_row['innings_ball_num']}")
print(f"Final delivery source overid: {last_row['overid']}")
print(f"Final delivery legal balls before: {last_row['pre_legal_balls']}")
print(f"Final delivery legal balls after: {last_row['legal_balls_after']}")
print(f"Target: {last_row['applicable_target']}, Pre-score: {last_row['pre_score']}, Runs required: {last_row['pre_runs_required']}")

print("\n=== 2. TRACING 12 UNEXPLAINED EXITS ===")
# Find the 12 unexplained exits
flagged = bbb[(bbb['is_wicket'] == False) & (bbb['dismissal_type'].isna()) & (bbb['dismissed_player_id'].notna())].copy()
flagged = flagged.merge(players[['player_id', 'player_name']], left_on='dismissed_player_id', right_on='player_id', how='left')

traces = []
for idx, row in flagged.iterrows():
    m_id = row['match_id']
    inn = row['innings']
    b_num = row['innings_ball_num']
    p_id = row['dismissed_player_id']
    p_name = row['player_name']
    
    inn_balls = bbb[(bbb['match_id'] == m_id) & (bbb['innings'] == inn)].sort_values('innings_ball_num')
    
    # Check if p_id was striker or non-striker on the exit ball
    exit_ball = inn_balls[inn_balls['innings_ball_num'] == b_num].iloc[0]
    is_striker = (exit_ball['striker_id'] == p_id)
    is_non_striker = (exit_ball['non_striker_id'] == p_id)
    role_at_exit = "Striker" if is_striker else ("Non-Striker" if is_non_striker else "Neither (Squad/Error)")
    
    # Check subsequent balls in that innings
    subsequent = inn_balls[inn_balls['innings_ball_num'] > b_num]
    appeared_again = ((subsequent['striker_id'] == p_id) | (subsequent['non_striker_id'] == p_id)).any()
    
    # Next ball participants
    if len(subsequent) > 0:
        next_ball = subsequent.iloc[0]
        next_striker = players.loc[players['player_id'] == next_ball['striker_id'], 'player_name'].values
        next_striker = next_striker[0] if len(next_striker) > 0 else str(next_ball['striker_id'])
        next_non_striker = players.loc[players['player_id'] == next_ball['non_striker_id'], 'player_name'].values
        next_non_striker = next_non_striker[0] if len(next_non_striker) > 0 else str(next_ball['non_striker_id'])
        next_batter = f"Str: {next_striker}, NonStr: {next_non_striker}"
    else:
        next_batter = "End of Innings"
        
    traces.append({
        'match_id': m_id,
        'innings': inn,
        'ball_num': b_num,
        'overid': row['overid'],
        'player_id': int(p_id),
        'player_name': p_name,
        'role_at_exit': role_at_exit,
        'subsequent_appearance': appeared_again,
        'next_ball_crease': next_batter
    })

df_traces = pd.DataFrame(traces)
print(df_traces.to_string())

print("\n=== 3. SUPER OVER COMPARISON ===")
# Matches where result mentions tie, eliminator, super over, etc.
tie_matches = matches[matches['result'].str.contains('Eliminator|Super Over|Tie|one over', case=False, na=False)].copy()
# Also check if any other matches have Innings 3 or 4 in BBB
bbb_super_overs = bbb[bbb['innings'].isin([3, 4])]['match_id'].unique()

all_so_candidate_ids = sorted(list(set(tie_matches['match_id'].tolist() + list(bbb_super_overs))))
so_comparison = []

for m_id in all_so_candidate_ids:
    m_row = matches[matches['match_id'] == m_id].iloc[0]
    inn3_4 = bbb[(bbb['match_id'] == m_id) & (bbb['innings'].isin([3, 4]))]
    has_bbb = len(inn3_4) > 0
    ball_count = len(inn3_4)
    inn_list = sorted(bbb[bbb['match_id'] == m_id]['innings'].unique().tolist())
    
    so_comparison.append({
        'match_id': m_id,
        'match_date': m_row['match_date'],
        'result': m_row['result'],
        'has_bbb_so': has_bbb,
        'so_ball_count': ball_count,
        'bbb_innings_present': str(inn_list),
        'status': 'FULL_COVERAGE' if has_bbb else 'MISSING_TIE_BREAKER_DELIVERIES'
    })

df_so = pd.DataFrame(so_comparison)
print(df_so.to_string())

print("\n=== 4. RECONCILIATION CHECKS BREAKDOWN ===")
print(reconcil['reconciliation_status'].value_counts())
print("\nFails:")
print(reconcil[reconcil['reconciliation_status'] == 'FAIL'][['match_id', 'expected_result', 'reconstructed_result', 'status_reason']].to_string())
print("\nNot Checkable Sample (first 5):")
print(reconcil[reconcil['reconciliation_status'] == 'NOT CHECKABLE'][['match_id', 'expected_result', 'status_reason']].head(5).to_string())

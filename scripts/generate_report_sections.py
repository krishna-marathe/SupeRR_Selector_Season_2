import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
import pandas as pd
import numpy as np

df = pd.read_parquet(settings.OUTPUTS_DIR / 'match_states.parquet')
matches = pd.read_csv(settings.MATCHES_PATH)
bbb = pd.read_csv(settings.BALL_BY_BALL_PATH)
mappings = pd.read_csv(settings.MAPPINGS_PATH)
players = mappings[['player_id', 'player_name']].drop_duplicates()
reconcil = pd.read_csv(settings.OUTPUTS_DIR / 'reconciliation_checks.csv')

print("--- SECTION 1: MATCH 13511 INNINGS 2 TRACE ---")
m13511 = df[(df['match_id'] == 13511) & (df['innings'] == 2)].sort_values('innings_ball_num').copy()
m13511['legal_balls_after'] = m13511['pre_legal_balls'] + m13511['delivery_is_legal'].astype(int)

sample_rows = [1, 2, 3, 4, 18, 19, 98, 99, 100, 101, 102, 103]
sub = m13511[m13511['innings_ball_num'].isin(sample_rows)]

print('| Attempt Index | Source Over (`overid`) | Cricket Ball Label | Legal Balls Before | Legal Balls After | Pre-Delivery Score | Runs Required | Pre-Delivery CRR | Pre-Delivery RRR | Delivery Outcome | Bowler | Striker |')
print('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
for _, r in sub.iterrows():
    b_num = int(r['innings_ball_num'])
    ov_src = int(r['overid'])
    completed_overs = int(r['pre_legal_balls']) // 6
    ball_in_over = (int(r['pre_legal_balls']) % 6) + 1
    ov_cricket = f"{completed_overs}.{ball_in_over}"
    lb_before = int(r['pre_legal_balls'])
    lb_after = int(r['legal_balls_after'])
    pre_sc = int(r['pre_score'])
    req = int(r['pre_runs_required'])
    crr = f"{r['pre_crr']:.2f}" if pd.notna(r['pre_crr']) else "Undefined (0.0 ov)"
    rrr = f"{r['pre_rrr']:.3f}" if pd.notna(r['pre_rrr']) else "NaN"
    outcome = f"{int(r['delivery_total_team_runs'])} runs"
    if r['delivery_is_team_wicket']:
        outcome += " (Wicket)"
    print(f"| **{b_num}** | Over {ov_src} | Over {ov_cricket} | {lb_before} | {lb_after} | {pre_sc}/{int(r['pre_wickets'])} | {req} | {crr} | {rrr} | {outcome} | {r['bowler_name']} | {r['striker_name']} |")

print("\n--- SECTION 2: 12 UNEXPLAINED EXITS TRACE ---")
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
    exit_ball = inn_balls[inn_balls['innings_ball_num'] == b_num].iloc[0]
    is_striker = (exit_ball['striker_id'] == p_id)
    is_non_striker = (exit_ball['non_striker_id'] == p_id)
    role_at_exit = "Striker" if is_striker else ("Non-Striker" if is_non_striker else "Neither")
    
    subsequent = inn_balls[inn_balls['innings_ball_num'] > b_num]
    appeared_again = ((subsequent['striker_id'] == p_id) | (subsequent['non_striker_id'] == p_id)).any()
    
    if len(subsequent) > 0:
        next_ball = subsequent.iloc[0]
        n_str = players.loc[players['player_id'] == next_ball['striker_id'], 'player_name'].values
        next_striker = n_str[0] if len(n_str) > 0 else str(next_ball['striker_id'])
        n_nstr = players.loc[players['player_id'] == next_ball['non_striker_id'], 'player_name'].values
        next_non_striker = n_nstr[0] if len(n_nstr) > 0 else str(next_ball['non_striker_id'])
        next_batter = f"{next_striker} & {next_non_striker}"
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
        'subsequent_appearance': "No (Never returned)" if not appeared_again else "Yes",
        'next_ball_crease': next_batter
    })

df_traces = pd.DataFrame(traces)
print('| Match ID | Inn | Ball Index | Source Over | Exiting Player (ID) | Role at Exit | Returned Later? | Next Ball Crease | Status / Treatment |')
print('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
for _, r in df_traces.iterrows():
    print(f"| **{r['match_id']}** | Inn {r['innings']} | Ball {r['ball_num']} | Over {r['overid']} | **{r['player_name']}** ({r['player_id']}) | {r['role_at_exit']} | {r['subsequent_appearance']} | {r['next_ball_crease']} | `UNRESOLVED_EXIT` (Excluded from not-out) |")

print("\n--- SECTION 3: SUPER OVER COMPARISON ---")
tie_matches = matches[matches['result'].str.contains('Eliminator|Super Over|Tie|one over', case=False, na=False)].copy()
bbb_super_overs = bbb[bbb['innings'].isin([3, 4])]['match_id'].unique()
all_so_candidate_ids = sorted(list(set(tie_matches['match_id'].tolist() + list(bbb_super_overs))))

print('| Match ID | Match Date | Result String (`matches.csv`) | Ball-by-Ball Coverage | Innings Present in BBB | Super Over Balls | Coverage Status & Analytical Consequence |')
print('| :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
for m_id in all_so_candidate_ids:
    m_row = matches[matches['match_id'] == m_id].iloc[0]
    inn3_4 = bbb[(bbb['match_id'] == m_id) & (bbb['innings'].isin([3, 4]))]
    has_bbb = len(inn3_4) > 0
    ball_count = len(inn3_4)
    inn_list = sorted(bbb[bbb['match_id'] == m_id]['innings'].unique().tolist())
    status_str = f"**Recorded** ({ball_count} balls in Inn 3/4; isolated from regular states)" if has_bbb else "**Missing Delivery Data** (Result records tie-breaker, but BBB ends at Inn 2)"
    print(f"| **{m_id}** | {m_row['match_date']} | `{m_row['result']}` | {'Yes' if has_bbb else 'No'} | {inn_list} | {ball_count} balls | {status_str} |")

print("\n--- SECTION 4: RECONCILIATION SUMMARY ---")
vc = reconcil['status'].value_counts()
print(f"Total Matches Checked: {len(reconcil)}")
print(f"PASS: {vc.get('PASS', 0)} ({vc.get('PASS', 0)/len(reconcil)*100:.2f}%)")
print(f"NOT CHECKABLE: {vc.get('NOT CHECKABLE', 0)} ({vc.get('NOT CHECKABLE', 0)/len(reconcil)*100:.2f}%)")
print(f"FAIL: {vc.get('FAIL', 0)} ({vc.get('FAIL', 0)/len(reconcil)*100:.2f}%)")

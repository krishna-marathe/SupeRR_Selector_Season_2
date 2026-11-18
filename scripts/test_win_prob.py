import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss
from config.settings import settings

df = pd.read_parquet(settings.OUTPUTS_DIR / 'match_states.parquet')
matches = pd.read_csv(settings.MATCHES_PATH)

def get_chase_outcome(res):
    if pd.isna(res): return 'UNRESOLVED'
    s = str(res).lower()
    if 'no result' in s or 'abandoned' in s: return 'NO_RESULT'
    if 'super over' in s or 'eliminator' in s or 'tie' in s: return 'TIED'
    if 'wicket' in s or 'wkt' in s: return 'WIN'
    if 'run' in s: return 'LOSS'
    return 'UNRESOLVED'

matches['chase_outcome'] = matches['result'].apply(get_chase_outcome)
df = df.merge(matches[['match_id', 'chase_outcome']], on='match_id', how='left')

# Innings 2 valid chase sample
chase = df[
    (df['innings'] == 2) &
    (df['is_valid_pressure_state'] == True) &
    (df['is_target_valid'] == True) &
    (df['is_rrr_valid'] == True) &
    (df['chase_outcome'].isin(['WIN', 'LOSS'])) &
    (~df['match_id'].isin([18532, 20190, 48610]))
].copy()

chase['target_win'] = (chase['chase_outcome'] == 'WIN').astype(int)
chase['year'] = pd.to_datetime(chase['match_date']).dt.year

counts = chase.groupby('match_id')['delivery_key'].transform('count')
chase['sample_weight'] = 1.0 / counts

features = ['pre_runs_required', 'pre_legal_balls_remaining', 'pre_wickets', 'applicable_target', 'pre_crr', 'pre_rrr']
chase['pre_crr'] = chase['pre_crr'].fillna(0.0)

train = chase[chase['year'] <= 2024]
test = chase[chase['year'] >= 2025]

print(f"Chase train deliveries: {len(train)}, test deliveries: {len(test)}")

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(train[features], train['target_win'], sample_weight=train['sample_weight'])
p_lr = lr.predict_proba(test[features])[:, 1]

hgb = HistGradientBoostingClassifier(max_iter=100, random_state=42)
hgb.fit(train[features], train['target_win'], sample_weight=train['sample_weight'])
p_hgb = hgb.predict_proba(test[features])[:, 1]

b_lr = brier_score_loss(test['target_win'], p_lr, sample_weight=test['sample_weight'])
l_lr = log_loss(test['target_win'], p_lr, sample_weight=test['sample_weight'])

b_hgb = brier_score_loss(test['target_win'], p_hgb, sample_weight=test['sample_weight'])
l_hgb = log_loss(test['target_win'], p_hgb, sample_weight=test['sample_weight'])

print("Logistic Regression:")
print(f"  Brier Score: {b_lr:.4f}, Log Loss: {l_lr:.4f}")

print("HistGradientBoosting:")
print(f"  Brier Score: {b_hgb:.4f}, Log Loss: {l_hgb:.4f}")

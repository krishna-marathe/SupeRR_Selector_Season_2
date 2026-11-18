"""Preflight and sample partitioning module.

Applies exclusion rules, quarantines failed reconciliations, isolates supplementary
competitions, and flags data anomalies without modifying raw data.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

# Root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from config.settings import settings
from config.analysis_config import analysis_settings


def run_preflight() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute preflight sample preparation.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        - df_senior: Primary analysis dataset (IPL + Senior T20Is, clean states).
        - df_emerging: Supplementary dataset (Emerging Teams, Rising Stars).
        - df_exclusions: Tabular summary of excluded matches, innings, and deliveries.
    """
    parquet_path = settings.OUTPUTS_DIR / "match_states.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Reconstructed match states not found at {parquet_path}")

    df = pd.read_parquet(parquet_path)
    total_deliveries = len(df)
    total_matches = df["match_id"].nunique()

    # 1. Identify Quarantined Matches
    quarantined = set(analysis_settings.preflight.quarantined_matches)
    is_quarantined = df["match_id"].isin(quarantined)

    # 2. Flag Anomalies on Missing extras_type with Positive Extras
    # Deliveries 36854 and 107489 have strokes ('Flick' and 'Worked') with extras but NaN extras_type.
    # To avoid arbitrary charges or unverified legality, flag them explicitly.
    df["is_missing_extras_anomaly"] = False
    anomaly_indices = [idx for idx in analysis_settings.preflight.anomaly_missing_extras_rows if idx in df.index]
    if anomaly_indices:
        df.loc[anomaly_indices, "is_missing_extras_anomaly"] = True
        # For bowler conceded runs, do not charge ambiguous extras on these 2 balls without evidence
        # runs were 0, extras were 1; stroke was bat-pad. Keep bowler conceded runs = 0
        df.loc[anomaly_indices, "delivery_bowler_runs_conceded"] = 0

    # 3. Preserve Unresolved Dismissal Attribution
    # Ball 127899 in Match 40709 (Retire Out, NaN dismissed player)
    df["is_dismissal_identity_resolved"] = True
    unresolved_dismissals = [idx for idx in analysis_settings.preflight.unresolved_dismissal_rows if idx in df.index]
    if unresolved_dismissals:
        df.loc[unresolved_dismissals, "is_dismissal_identity_resolved"] = False

    # 4. Partition by Competition Scope
    senior_mask = df["comp_category"].isin(analysis_settings.preflight.senior_competitions)
    emerging_mask = df["comp_category"].isin(analysis_settings.preflight.supplementary_competitions)

    # 5. Validity filter (must have valid pressure state and not quarantined)
    valid_mask = df["is_valid_pressure_state"] & (~is_quarantined)

    df_senior = df[senior_mask & valid_mask].copy()
    df_emerging = df[emerging_mask & valid_mask].copy()

    # 6. Generate Exclusions Summary Table
    quarantined_delivs = is_quarantined.sum()
    quarantined_matches_count = len(quarantined)

    rain_excluded_delivs = (~df["is_valid_pressure_state"]).sum()
    super_over_delivs = df["is_super_over"].sum()

    senior_eligible_delivs = len(df_senior)
    senior_eligible_matches = df_senior["match_id"].nunique()

    emerging_eligible_delivs = len(df_emerging)
    emerging_eligible_matches = df_emerging["match_id"].nunique()

    exclusions_data = [
        {
            "Scope": "Total Dataset Deliveries",
            "Count": total_deliveries,
            "Matches": total_matches,
            "Action": "Catalog baseline",
            "Reason": "All recorded deliveries in ball_by_ball.csv",
        },
        {
            "Scope": "Quarantined Reconciliation Fails",
            "Count": int(quarantined_delivs),
            "Matches": quarantined_matches_count,
            "Action": "Quarantined from primary analysis",
            "Reason": "Unresolved scorecard/DLS result text divergence (Matches 18532, 20190, 48610)",
        },
        {
            "Scope": "Rain-Interrupted Deliveries Excluded",
            "Count": int(rain_excluded_delivs - super_over_delivs),
            "Matches": 34,
            "Action": "Excluded from 20-over pressure curves",
            "Reason": "Unverified mid-innings stoppage or target revision timing",
        },
        {
            "Scope": "Super Over Deliveries Isolated",
            "Count": int(super_over_delivs),
            "Matches": 6,
            "Action": "Isolated as distinct tie-breaker state",
            "Reason": "Innings 3 & 4 operate under non-standard 6-ball / 2-wicket limits",
        },
        {
            "Scope": "Emerging / 'A' Team Competitions",
            "Count": emerging_eligible_delivs,
            "Matches": emerging_eligible_matches,
            "Action": "Preserved in supplementary analysis",
            "Reason": "Distinct player development context (Asia Cup Rising Stars / Emerging Cup)",
        },
        {
            "Scope": "Primary Senior Analysis Sample",
            "Count": senior_eligible_delivs,
            "Matches": senior_eligible_matches,
            "Action": "Retained for Primary Ratings",
            "Reason": "Verified senior IPL and T20I matches with standard 20-over match states",
        },
    ]

    df_exclusions = pd.DataFrame(exclusions_data)
    out_table_path = settings.OUTPUTS_DIR / "tables" / "exclusions_summary.csv"
    out_table_path.parent.mkdir(parents=True, exist_ok=True)
    df_exclusions.to_csv(out_table_path, index=False)
    print(f"Preflight completed. Primary Senior sample: {senior_eligible_delivs} balls across {senior_eligible_matches} matches.")

    return df_senior, df_emerging, df_exclusions


if __name__ == "__main__":
    df_s, df_e, df_ex = run_preflight()
    print(df_ex.to_string())

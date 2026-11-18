"""Pressure assessment module.

Computes pre-delivery transparent benchmark pressure flags, trains and evaluates
the model-assisted chase win-probability alternative, and profiles coverage.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss
from config.settings import settings
from config.analysis_config import analysis_settings


def apply_pressure_definitions(df: pd.DataFrame, matches_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """Apply transparent benchmark and model-assisted pressure flags.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned delivery-level match-state dataset.
    matches_df : pd.DataFrame
        Source matches fixture table for chase regulation outcome mapping.

    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]
        - df: Augmented dataframe with pressure flags.
        - model_metrics: Dictionary comparing win-probability models.
        - coverage_summary: Detailed coverage summary table across splits.
    """
    df = df.copy()

    # 1. Benchmark Flags (Pre-delivery state strictly)
    # Late Chase: Innings 2, <= 30 balls remaining, RRR >= 8.0, target not reached
    c_late_chase = (
        (df["innings"] == 2)
        & (df["is_legal_balls_remaining_valid"])
        & (df["pre_legal_balls_remaining"] <= analysis_settings.pressure.late_chase_max_balls)
        & (df["is_rrr_valid"])
        & (df["pre_rrr"] >= analysis_settings.pressure.late_chase_min_rrr)
        & (df["pre_runs_required"] > 0)
    )

    # Resource Pressure: <= 4 wickets in hand (pre_wickets >= 6), >= 30 balls remaining
    c_resource = (
        (df["innings"].isin([1, 2]))
        & (df["pre_wickets"] >= (10 - analysis_settings.pressure.resource_max_wickets_in_hand))
        & (df["is_legal_balls_remaining_valid"])
        & (df["pre_legal_balls_remaining"] >= analysis_settings.pressure.resource_min_balls_remaining)
    )

    # First-Innings Finishing Phase: Innings 1, <= 30 balls remaining (Phase-based importance proxy)
    c_inn1_finish = (
        (df["innings"] == 1)
        & (df["is_legal_balls_remaining_valid"])
        & (df["pre_legal_balls_remaining"] <= analysis_settings.pressure.inn1_finish_max_balls)
    )

    df["pressure_late_chase"] = c_late_chase
    df["pressure_resource"] = c_resource
    df["pressure_inn1_finish"] = c_inn1_finish

    # Union Benchmark Flag
    df["is_pressure_benchmark"] = c_late_chase | c_resource | c_inn1_finish

    # Construct descriptive reason strings
    reasons = []
    for lc, res, inf in zip(c_late_chase, c_resource, c_inn1_finish):
        r = []
        if lc: r.append("LATE_CHASE")
        if res: r.append("RESOURCE_PRESSURE")
        if inf: r.append("INN1_FINISH_PHASE")
        reasons.append("|".join(r) if r else "NONE")
    df["pressure_benchmark_reasons"] = reasons

    # 2. Model-Assisted Chase Pressure Alternative
    # Parse regulation match outcomes from matches_df
    def get_regulation_outcome(res: Any) -> str:
        if pd.isna(res): return "UNRESOLVED"
        s = str(res).lower()
        if "no result" in s or "abandoned" in s: return "NO_RESULT"
        if "super over" in s or "eliminator" in s or "tie" in s: return "TIED_REGULATION"
        if "wicket" in s or "wkt" in s: return "CHASE_WIN"
        if "run" in s: return "CHASE_LOSS"
        return "UNRESOLVED"

    match_outcomes = matches_df[["match_id", "result"]].copy()
    match_outcomes["reg_outcome"] = match_outcomes["result"].apply(get_regulation_outcome)
    
    if "reg_outcome" not in df.columns:
        df = df.merge(match_outcomes[["match_id", "reg_outcome"]], on="match_id", how="left")

    # Filter binary chase training data (exclude tied regulation, no-results, unresolved)
    chase_mask = (
        (df["innings"] == 2)
        & (df["is_valid_pressure_state"])
        & (df["is_target_valid"])
        & (df["is_rrr_valid"])
        & (df["reg_outcome"].isin(["CHASE_WIN", "CHASE_LOSS"]))
    )
    chase_df = df[chase_mask].copy()

    # Per-innings inverse length weighting so long chases do not dominate
    innings_ball_counts = chase_df.groupby("match_id")["delivery_key"].transform("count")
    chase_df["sample_weight"] = 1.0 / innings_ball_counts

    chase_df["target_win"] = (chase_df["reg_outcome"] == "CHASE_WIN").astype(int)
    chase_df["year"] = pd.to_datetime(chase_df["match_date"]).dt.year

    features = [
        "pre_runs_required",
        "pre_legal_balls_remaining",
        "pre_wickets",
        "applicable_target",
        "pre_crr",
        "pre_rrr",
    ]
    # Impute CRR if 0 balls
    chase_df["pre_crr"] = chase_df["pre_crr"].fillna(0.0)

    # Chronological partition for evaluation: Train <= 2024, Test >= 2025
    train_split = chase_df[chase_df["year"] <= analysis_settings.temporal.development_years[-1]]
    test_split = chase_df[chase_df["year"] >= analysis_settings.temporal.validation_year]

    # Model A: Logistic Regression
    lr = LogisticRegression(max_iter=analysis_settings.model.lr_max_iter, random_state=analysis_settings.model.random_seed)
    lr.fit(train_split[features], train_split["target_win"], sample_weight=train_split["sample_weight"])
    p_test_lr = lr.predict_proba(test_split[features])[:, 1]

    # Model B: HistGradientBoostingClassifier
    hgb = HistGradientBoostingClassifier(
        max_iter=analysis_settings.model.hgb_max_iter,
        min_samples_leaf=analysis_settings.model.hgb_min_samples_leaf,
        learning_rate=analysis_settings.model.hgb_learning_rate,
        random_state=analysis_settings.model.random_seed,
    )
    hgb.fit(train_split[features], train_split["target_win"], sample_weight=train_split["sample_weight"])
    p_test_hgb = hgb.predict_proba(test_split[features])[:, 1]

    brier_lr = brier_score_loss(test_split["target_win"], p_test_lr, sample_weight=test_split["sample_weight"])
    logloss_lr = log_loss(test_split["target_win"], p_test_lr, sample_weight=test_split["sample_weight"])

    brier_hgb = brier_score_loss(test_split["target_win"], p_test_hgb, sample_weight=test_split["sample_weight"])
    logloss_hgb = log_loss(test_split["target_win"], p_test_hgb, sample_weight=test_split["sample_weight"])

    model_metrics = {
        "LogisticRegression": {"Brier": float(brier_lr), "LogLoss": float(logloss_lr), "Winner": brier_lr < brier_hgb},
        "HistGradientBoosting": {"Brier": float(brier_hgb), "LogLoss": float(logloss_hgb), "Winner": brier_hgb < brier_lr},
    }

    # Generate out-of-sample predictions on full dataset using expanding windows
    df["est_chase_win_prob"] = np.nan
    # Fit expanding models:
    years = sorted(df["match_date"].apply(lambda d: int(str(d)[:4])).unique())
    # For year 2022, use match-level 5-fold CV to ensure out-of-sample validity
    matches_2022 = chase_df[chase_df["year"] == 2022]["match_id"].unique()
    np.random.seed(analysis_settings.model.random_seed)
    folds = np.array_split(np.random.permutation(matches_2022), 5)
    
    for fold_matches in folds:
        train_idx = chase_df[(chase_df["year"] == 2022) & (~chase_df["match_id"].isin(fold_matches))].index
        val_idx = chase_df[(chase_df["year"] == 2022) & (chase_df["match_id"].isin(fold_matches))].index
        if len(train_idx) > 0 and len(val_idx) > 0:
            m = LogisticRegression(max_iter=1000, random_state=42)
            m.fit(chase_df.loc[train_idx, features], chase_df.loc[train_idx, "target_win"], sample_weight=chase_df.loc[train_idx, "sample_weight"])
            df.loc[val_idx, "est_chase_win_prob"] = m.predict_proba(chase_df.loc[val_idx, features].fillna(0))[:, 1]

    # For subsequent years (2023..2026), train strictly on all prior years (expanding window)
    for yr in range(2023, max(years) + 1):
        tr = chase_df[chase_df["year"] < yr]
        te = chase_df[chase_df["year"] == yr]
        if len(tr) > 0 and len(te) > 0:
            m = LogisticRegression(max_iter=1000, random_state=42)
            m.fit(tr[features], tr["target_win"], sample_weight=tr["sample_weight"])
            df.loc[te.index, "est_chase_win_prob"] = m.predict_proba(te[features].fillna(0))[:, 1]

    # Define Model-Assisted Competitive Late Chase Flag:
    # <= 60 legal balls remaining, win probability in [0.10, 0.90]
    c_model_assisted = (
        (df["innings"] == 2)
        & (df["is_legal_balls_remaining_valid"])
        & (df["pre_legal_balls_remaining"] <= analysis_settings.pressure.model_assisted_max_balls)
        & (df["est_chase_win_prob"] >= analysis_settings.pressure.model_assisted_min_win_prob)
        & (df["est_chase_win_prob"] <= analysis_settings.pressure.model_assisted_max_win_prob)
    )
    df["pressure_model_assisted_chase"] = c_model_assisted

    # 3. Pressure Coverage Analysis Breakdown
    cov_rows = []
    # By Innings
    for inn, grp in df.groupby("innings"):
        cov_rows.append({
            "Dimension": "Innings",
            "Category": f"Innings {inn}",
            "Total_Deliveries": len(grp),
            "Benchmark_Pressure_Deliveries": grp["is_pressure_benchmark"].sum(),
            "Benchmark_Pressure_Pct": round(grp["is_pressure_benchmark"].mean() * 100, 2),
            "Late_Chase_Balls": grp["pressure_late_chase"].sum(),
            "Resource_Pressure_Balls": grp["pressure_resource"].sum(),
            "Inn1_Finish_Balls": grp["pressure_inn1_finish"].sum(),
            "Model_Assisted_Balls": grp["pressure_model_assisted_chase"].sum(),
        })

    # By Phase
    for ph, grp in df.groupby("innings_phase"):
        cov_rows.append({
            "Dimension": "Phase",
            "Category": ph,
            "Total_Deliveries": len(grp),
            "Benchmark_Pressure_Deliveries": grp["is_pressure_benchmark"].sum(),
            "Benchmark_Pressure_Pct": round(grp["is_pressure_benchmark"].mean() * 100, 2),
            "Late_Chase_Balls": grp["pressure_late_chase"].sum(),
            "Resource_Pressure_Balls": grp["pressure_resource"].sum(),
            "Inn1_Finish_Balls": grp["pressure_inn1_finish"].sum(),
            "Model_Assisted_Balls": grp["pressure_model_assisted_chase"].sum(),
        })

    # By Competition Category
    for comp, grp in df.groupby("comp_category"):
        cov_rows.append({
            "Dimension": "Competition",
            "Category": comp,
            "Total_Deliveries": len(grp),
            "Benchmark_Pressure_Deliveries": grp["is_pressure_benchmark"].sum(),
            "Benchmark_Pressure_Pct": round(grp["is_pressure_benchmark"].mean() * 100, 2),
            "Late_Chase_Balls": grp["pressure_late_chase"].sum(),
            "Resource_Pressure_Balls": grp["pressure_resource"].sum(),
            "Inn1_Finish_Balls": grp["pressure_inn1_finish"].sum(),
            "Model_Assisted_Balls": grp["pressure_model_assisted_chase"].sum(),
        })

    # By Season
    for s, grp in df.groupby("season"):
        cov_rows.append({
            "Dimension": "Season",
            "Category": s,
            "Total_Deliveries": len(grp),
            "Benchmark_Pressure_Deliveries": grp["is_pressure_benchmark"].sum(),
            "Benchmark_Pressure_Pct": round(grp["is_pressure_benchmark"].mean() * 100, 2),
            "Late_Chase_Balls": grp["pressure_late_chase"].sum(),
            "Resource_Pressure_Balls": grp["pressure_resource"].sum(),
            "Inn1_Finish_Balls": grp["pressure_inn1_finish"].sum(),
            "Model_Assisted_Balls": grp["pressure_model_assisted_chase"].sum(),
        })

    coverage_summary = pd.DataFrame(cov_rows)
    out_cov_path = settings.OUTPUTS_DIR / "tables" / "pressure_coverage.csv"
    coverage_summary.to_csv(out_cov_path, index=False)
    print(f"Pressure definitions applied. Benchmark pressure balls: {df['is_pressure_benchmark'].sum()} ({df['is_pressure_benchmark'].mean()*100:.2f}%)")

    return df, model_metrics, coverage_summary


if __name__ == "__main__":
    from src.analysis.preflight import run_preflight
    matches = pd.read_csv(settings.MATCHES_PATH)
    df_senior, _, _ = run_preflight()
    df_aug, metrics, cov = apply_pressure_definitions(df_senior, matches)
    print("\nWin Prob Model Comparison:", metrics)
    print("\nPressure Coverage Sample:")
    print(cov.head(10).to_string())

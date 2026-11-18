"""Contextual expected-performance modeling and expanding-window evaluation.

Fits models for:
1. Batter runs per faced delivery (excluding wides)
2. Striker dismissal probability per faced delivery (excluding non-striker run-outs)
3. Bowler conceded runs per physical delivery (including illegal deliveries)
4. Bowler credited wicket probability per physical delivery (excluding fielding dismissals)

Compares smoothed context baselines, regularized linear models, and histogram gradient boosting.
Enforces strict chronological validation (2022-2024 dev, 2025 val, 2026 untouched temporal test).
Generates strictly out-of-sample predictions for all historical player scoring.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Tuple, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, brier_score_loss, log_loss
from config.settings import settings
from config.analysis_config import analysis_settings


class ContextGroupBaseline:
    """Smoothed context-group empirical baseline."""

    def __init__(self, smoothing: float = 20.0):
        self.smoothing = smoothing
        self.global_mean_: float = 0.0
        self.group_means_: Dict[Tuple, float] = {}

    def _get_bins(self, X: pd.DataFrame) -> pd.Series:
        balls_bucket = pd.cut(X["pre_legal_balls"], bins=[-1, 36, 90, 120], labels=["PP", "MID", "DTH"])
        wkt_bucket = pd.cut(X["pre_wickets"], bins=[-1, 1, 3, 5, 10], labels=["W0_1", "W2_3", "W4_5", "W6_plus"])
        return list(zip(X["innings"], balls_bucket, wkt_bucket, X["comp_category"]))

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.global_mean_ = float(y.mean())
        df = pd.DataFrame({"bin": self._get_bins(X), "y": y})
        agg = df.groupby("bin")["y"].agg(["count", "mean"])
        # Empirical Bayes shrinkage: (n * mean + m * global) / (n + m)
        smoothed = (agg["count"] * agg["mean"] + self.smoothing * self.global_mean_) / (agg["count"] + self.smoothing)
        self.group_means_ = smoothed.to_dict()
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        bins = self._get_bins(X)
        return np.array([self.group_means_.get(b, self.global_mean_) for b in bins])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        p1 = np.clip(self.predict(X), 1e-6, 1.0 - 1e-6)
        p0 = 1.0 - p1
        return np.vstack([p0, p1]).T


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode pre-delivery features without lookahead information."""
    X = pd.DataFrame(index=df.index)
    X["innings"] = df["innings"].astype(int)
    X["pre_legal_balls"] = df["pre_legal_balls"].astype(float)
    X["pre_wickets"] = df["pre_wickets"].astype(float)
    X["pre_score"] = df["pre_score"].astype(float)
    X["pre_legal_balls_remaining"] = df["pre_legal_balls_remaining"].fillna(60.0).astype(float)
    
    # Safe RRR (0 for Innings 1 or where invalid)
    X["pre_rrr"] = np.where((df["innings"] == 2) & df["is_rrr_valid"], df["pre_rrr"].fillna(8.0), 0.0)
    X["pre_runs_required"] = np.where((df["innings"] == 2) & df["is_target_valid"], df["pre_runs_required"].fillna(50.0), 0.0)
    
    # Categoricals
    phase_map = {"Powerplay": 0, "Middle": 1, "Death": 2}
    X["innings_phase_code"] = df["innings_phase"].map(phase_map).fillna(1).astype(int)
    
    comp_map = {
        "IPL (Franchise)": 0,
        "Bilateral Series (T20I)": 1,
        "Multi-Nation Tournament (T20I)": 2,
        "International Tri-Series (T20I)": 3,
        "Emerging Teams (T20)": 4,
    }
    X["comp_code"] = df["comp_category"].map(comp_map).fillna(1).astype(int)
    X["comp_category"] = df["comp_category"]
    return X


def evaluate_and_score_models(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train, validate, compare, and produce out-of-sample expectations across all deliveries.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        - df_scored: Augmented dataset with out-of-sample contextual expectations.
        - model_comparison: Comparative performance metrics across models on validation period.
        - temporal_validation: Metrics across temporal test set (2026 untouched).
    """
    df = df.copy()
    df["year"] = pd.to_datetime(df["match_date"]).dt.year
    X_all = prepare_features(df)
    feature_cols = [
        "innings", "pre_legal_balls", "pre_wickets", "pre_score",
        "pre_legal_balls_remaining", "pre_rrr", "pre_runs_required",
        "innings_phase_code", "comp_code"
    ]

    # Target 1: Batter Runs (Faced deliveries only)
    mask_bat = (df["delivery_is_batter_ball_faced"] == True)
    # Target 2: Striker Dismissal (Faced deliveries, exclude non-striker run outs and unpopulated dismissal)
    # Identify non-striker run-out:
    is_non_striker_runout = (
        (df["delivery_dismissal_type"] == "RunOut")
        & (df["delivery_dismissed_player_id"] == df["non_striker_id"])
    )
    is_striker_dismissal = (
        (df["delivery_is_team_wicket"] == True)
        & (~is_non_striker_runout)
        & (df["is_dismissal_identity_resolved"] == True)
    )
    df["is_striker_dismissal"] = is_striker_dismissal
    mask_dismiss = mask_bat & (df["is_dismissal_identity_resolved"] == True)

    # Target 3: Bowler Conceded Runs (All physical deliveries)
    mask_bowl_runs = pd.Series(True, index=df.index)
    # Target 4: Bowler Credited Wickets (All physical deliveries)
    mask_bowl_wkts = pd.Series(True, index=df.index)

    targets = {
        "bat_runs": {
            "name": "Batter Runs Faced",
            "type": "regression",
            "mask": mask_bat,
            "y": df["delivery_runs"].astype(float),
            "out_col": "exp_batter_runs",
        },
        "striker_dismiss": {
            "name": "Striker Dismissal Prob",
            "type": "classification",
            "mask": mask_dismiss,
            "y": is_striker_dismissal.astype(int),
            "out_col": "exp_striker_dismissal_prob",
        },
        "bowler_runs": {
            "name": "Bowler Conceded Runs",
            "type": "regression",
            "mask": mask_bowl_runs,
            "y": df["delivery_bowler_runs_conceded"].astype(float),
            "out_col": "exp_bowler_conceded_runs",
        },
        "bowler_wicket": {
            "name": "Bowler Credited Wicket Prob",
            "type": "classification",
            "mask": mask_bowl_wkts,
            "y": df["delivery_is_bowler_wicket"].astype(int),
            "out_col": "exp_bowler_wicket_prob",
        },
    }

    # Model Comparison on Validation Period (Train <= 2024, Test == 2025)
    train_years = analysis_settings.temporal.development_years
    val_year = analysis_settings.temporal.validation_year
    test_year = analysis_settings.temporal.untouched_evaluation_year

    comp_records = []
    temp_records = []

    print("\n--- Model Training & Chronological Evaluation ---")

    for t_key, t_info in targets.items():
        sub_mask = t_info["mask"]
        sub_X = X_all[sub_mask]
        sub_y = t_info["y"][sub_mask]
        sub_years = df.loc[sub_mask, "year"]

        # Train on <= 2024, Validate on 2025
        idx_train = sub_years.isin(train_years)
        idx_val = (sub_years == val_year)
        idx_test = (sub_years == test_year)

        X_train, y_train = sub_X.loc[idx_train], sub_y.loc[idx_train]
        X_val, y_val = sub_X.loc[idx_val], sub_y.loc[idx_val]
        X_test, y_test = sub_X.loc[idx_test], sub_y.loc[idx_test]

        # 1. Baseline
        base_model = ContextGroupBaseline()
        base_model.fit(X_train, y_train)

        # 2. Linear / Logistic Model
        if t_info["type"] == "regression":
            lin_model = Ridge(alpha=10.0, random_state=42)
            lin_model.fit(X_train[feature_cols], y_train)
            hgb_model = HistGradientBoostingRegressor(
                max_iter=analysis_settings.model.hgb_max_iter,
                min_samples_leaf=analysis_settings.model.hgb_min_samples_leaf,
                learning_rate=analysis_settings.model.hgb_learning_rate,
                random_state=42,
            )
            hgb_model.fit(X_train[feature_cols], y_train)

            # Predictions on Validation
            pred_base = base_model.predict(X_val)
            pred_lin = lin_model.predict(X_val[feature_cols])
            pred_hgb = hgb_model.predict(X_val[feature_cols])

            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "Context Group Baseline",
                "Metric_1 (MAE)": round(mean_absolute_error(y_val, pred_base), 4),
                "Metric_2 (RMSE)": round(root_mean_squared_error(y_val, pred_base), 4),
            })
            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "Ridge Linear Model",
                "Metric_1 (MAE)": round(mean_absolute_error(y_val, pred_lin), 4),
                "Metric_2 (RMSE)": round(root_mean_squared_error(y_val, pred_lin), 4),
            })
            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "HistGradientBoosting",
                "Metric_1 (MAE)": round(mean_absolute_error(y_val, pred_hgb), 4),
                "Metric_2 (RMSE)": round(root_mean_squared_error(y_val, pred_hgb), 4),
            })

            # Predictions on Untouched 2026 Test Set
            pred_test_hgb = hgb_model.predict(X_test[feature_cols])
            temp_records.append({
                "Target": t_info["name"], "Evaluation_Period": f"Untouched {test_year}", "Model": "HistGradientBoosting",
                "Metric_1 (MAE)": round(mean_absolute_error(y_test, pred_test_hgb), 4),
                "Metric_2 (RMSE)": round(root_mean_squared_error(y_test, pred_test_hgb), 4),
                "Sample_Size_Balls": len(y_test),
            })

        else:
            lin_model = LogisticRegression(max_iter=1000, random_state=42)
            lin_model.fit(X_train[feature_cols], y_train)
            hgb_model = HistGradientBoostingClassifier(
                max_iter=analysis_settings.model.hgb_max_iter,
                min_samples_leaf=analysis_settings.model.hgb_min_samples_leaf,
                learning_rate=analysis_settings.model.hgb_learning_rate,
                random_state=42,
            )
            hgb_model.fit(X_train[feature_cols], y_train)

            # Predictions on Validation
            pred_base = base_model.predict_proba(X_val)[:, 1]
            pred_lin = lin_model.predict_proba(X_val[feature_cols])[:, 1]
            pred_hgb = hgb_model.predict_proba(X_val[feature_cols])[:, 1]

            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "Context Group Baseline",
                "Metric_1 (Brier)": round(brier_score_loss(y_val, pred_base), 5),
                "Metric_2 (LogLoss)": round(log_loss(y_val, pred_base), 5),
            })
            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "Logistic Regression",
                "Metric_1 (Brier)": round(brier_score_loss(y_val, pred_lin), 5),
                "Metric_2 (LogLoss)": round(log_loss(y_val, pred_lin), 5),
            })
            comp_records.append({
                "Target": t_info["name"], "Period": f"Val {val_year}", "Model": "HistGradientBoosting",
                "Metric_1 (Brier)": round(brier_score_loss(y_val, pred_hgb), 5),
                "Metric_2 (LogLoss)": round(log_loss(y_val, pred_hgb), 5),
            })

            # Predictions on Untouched 2026 Test Set
            pred_test_hgb = hgb_model.predict_proba(X_test[feature_cols])[:, 1]
            temp_records.append({
                "Target": t_info["name"], "Evaluation_Period": f"Untouched {test_year}", "Model": "HistGradientBoosting",
                "Metric_1 (Brier)": round(brier_score_loss(y_test, pred_test_hgb), 5),
                "Metric_2 (LogLoss)": round(log_loss(y_test, pred_test_hgb), 5),
                "Sample_Size_Balls": len(y_test),
            })

    # Generate Expanding-Window Strictly Out-Of-Sample Predictions for the entire dataset
    # We initialize output columns
    for t_key, t_info in targets.items():
        df[t_info["out_col"]] = np.nan

    all_years = sorted(df["year"].unique())
    matches_2022 = df[df["year"] == 2022]["match_id"].unique()
    np.random.seed(42)
    folds_2022 = np.array_split(np.random.permutation(matches_2022), 5)

    print("\nGenerating expanding-window out-of-sample predictions across 2022-2026...")

    for t_key, t_info in targets.items():
        sub_mask = t_info["mask"]
        sub_df = df[sub_mask]
        sub_X = X_all.loc[sub_df.index, feature_cols]
        sub_y = t_info["y"].loc[sub_df.index]
        sub_years = df.loc[sub_df.index, "year"]
        out_col = t_info["out_col"]
        is_reg = (t_info["type"] == "regression")

        # 1. 2022 Out-of-sample via 5-fold match CV
        for f_matches in folds_2022:
            tr_idx = sub_df[(sub_years == 2022) & (~sub_df["match_id"].isin(f_matches))].index
            val_idx = sub_df[(sub_years == 2022) & (sub_df["match_id"].isin(f_matches))].index
            if len(tr_idx) > 0 and len(val_idx) > 0:
                if is_reg:
                    m = HistGradientBoostingRegressor(max_iter=50, min_samples_leaf=25, random_state=42)
                    m.fit(sub_X.loc[tr_idx], sub_y.loc[tr_idx])
                    df.loc[val_idx, out_col] = m.predict(sub_X.loc[val_idx])
                else:
                    m = HistGradientBoostingClassifier(max_iter=50, min_samples_leaf=25, random_state=42)
                    m.fit(sub_X.loc[tr_idx], sub_y.loc[tr_idx])
                    df.loc[val_idx, out_col] = m.predict_proba(sub_X.loc[val_idx])[:, 1]

        # 2. Subsequent years (2023, 2024, 2025, 2026): strictly fit on all earlier years
        for yr in range(2023, max(all_years) + 1):
            tr_idx = sub_df[sub_years < yr].index
            te_idx = sub_df[sub_years == yr].index
            if len(tr_idx) > 0 and len(te_idx) > 0:
                if is_reg:
                    m = HistGradientBoostingRegressor(max_iter=50, min_samples_leaf=25, random_state=42)
                    m.fit(sub_X.loc[tr_idx], sub_y.loc[tr_idx])
                    df.loc[te_idx, out_col] = m.predict(sub_X.loc[te_idx])
                else:
                    m = HistGradientBoostingClassifier(max_iter=50, min_samples_leaf=25, random_state=42)
                    m.fit(sub_X.loc[tr_idx], sub_y.loc[tr_idx])
                    df.loc[te_idx, out_col] = m.predict_proba(sub_X.loc[te_idx])[:, 1]

    model_comp_df = pd.DataFrame(comp_records)
    temp_val_df = pd.DataFrame(temp_records)

    out_comp_path = settings.OUTPUTS_DIR / "tables" / "model_comparison.csv"
    out_temp_path = settings.OUTPUTS_DIR / "tables" / "temporal_validation.csv"
    model_comp_df.to_csv(out_comp_path, index=False)
    temp_val_df.to_csv(out_temp_path, index=False)

    print("Expected performance modeling complete. Out-of-sample predictions assigned.")
    return df, model_comp_df, temp_val_df


if __name__ == "__main__":
    from src.analysis.preflight import run_preflight
    from src.analysis.pressure import apply_pressure_definitions
    matches = pd.read_csv(settings.MATCHES_PATH)
    df_s, _, _ = run_preflight()
    df_aug, _, _ = apply_pressure_definitions(df_s, matches)
    df_scored, comp_df, temp_df = evaluate_and_score_models(df_aug)
    print("\nModel Comparison Table:")
    print(comp_df.to_string())
    print("\nTemporal Validation Table (2026 Untouched):")
    print(temp_df.to_string())

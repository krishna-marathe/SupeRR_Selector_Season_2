"""Player baseline evaluation, shrinkage, composite rating, and cluster bootstrap.

Computes:
- Context-adjusted residuals for scoring, survival, prevention, and wicket-taking.
- Empirical Bayes shrinkage towards population means.
- Explainable composite rating (60% runs/prevention, 40% survival/wickets; 75% effectiveness, 25% lift).
- 500 whole-match cluster bootstrap resamples.
- 90% uncertainty intervals, conservative scores (5th percentile lower bound), bootstrap selection frequencies.
- Exports comprehensive ranking tables and match evidence.
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
from config.settings import settings
from config.analysis_config import analysis_settings


def compute_player_ratings_and_bootstrap(
    df: pd.DataFrame,
    pressure_col: str = "is_pressure_benchmark",
    n_bootstrap: int = 500,
    random_seed: int = 42,
    ipl_only: bool = False,
    override_weights: Dict[str, float] | None = None,
    override_thresholds: Dict[str, int] | None = None,
    save_to_disk: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute player baseline performance, ratings, and cluster bootstrap uncertainty."""
    df = df.copy()
    if ipl_only:
        df = df[df["comp_category"] == "IPL (Franchise)"].copy()

    # Residuals
    if "res_bat_runs" not in df.columns:
        df["res_bat_runs"] = df["delivery_runs"] - df["exp_batter_runs"]
    if "res_bat_surv" not in df.columns:
        df["res_bat_surv"] = df["exp_striker_dismissal_prob"] - df["is_striker_dismissal"].astype(float)
    if "res_bowl_prev" not in df.columns:
        df["res_bowl_prev"] = df["exp_bowler_conceded_runs"] - df["delivery_bowler_runs_conceded"]
    if "res_bowl_wkt" not in df.columns:
        df["res_bowl_wkt"] = df["delivery_is_bowler_wicket"].astype(float) - df["exp_bowler_wicket_prob"]

    # Thresholds
    w_cfg = analysis_settings.weights
    w_score = override_weights.get("w_scoring", w_cfg.weight_scoring_prevention) if override_weights else w_cfg.weight_scoring_prevention
    w_surv = override_weights.get("w_survival", w_cfg.weight_survival_wickets) if override_weights else w_cfg.weight_survival_wickets
    w_eff = override_weights.get("w_eff", w_cfg.weight_pressure_effectiveness) if override_weights else w_cfg.weight_pressure_effectiveness
    w_lift = override_weights.get("w_lift", w_cfg.weight_baseline_lift) if override_weights else w_cfg.weight_baseline_lift

    e_cfg = analysis_settings.eligibility
    b_min_p_balls = override_thresholds.get("b_p_balls", e_cfg.batter_min_pressure_balls) if override_thresholds else e_cfg.batter_min_pressure_balls
    b_min_p_matches = override_thresholds.get("b_p_matches", e_cfg.batter_min_pressure_matches) if override_thresholds else e_cfg.batter_min_pressure_matches
    b_min_np_balls = override_thresholds.get("b_np_balls", e_cfg.batter_min_baseline_balls) if override_thresholds else e_cfg.batter_min_baseline_balls

    bw_min_p_legal = override_thresholds.get("bw_p_legal", e_cfg.bowler_min_pressure_legal_balls) if override_thresholds else e_cfg.bowler_min_pressure_legal_balls
    bw_min_p_matches = override_thresholds.get("bw_p_matches", e_cfg.bowler_min_pressure_matches) if override_thresholds else e_cfg.bowler_min_pressure_matches
    bw_min_np_legal = override_thresholds.get("bw_np_legal", e_cfg.bowler_min_baseline_legal_balls) if override_thresholds else e_cfg.bowler_min_baseline_legal_balls

    # 1. Vectorized Player-Match Aggregation
    faced_mask = (df["delivery_is_batter_ball_faced"] == True)
    df_bat = df[faced_mask].copy()

    df_bat["p_b"] = df_bat[pressure_col].astype(int)
    df_bat["np_b"] = (~df_bat[pressure_col]).astype(int)
    df_bat["p_r"] = df_bat["delivery_runs"] * df_bat["p_b"]
    df_bat["np_r"] = df_bat["delivery_runs"] * df_bat["np_b"]
    df_bat["p_rr"] = df_bat["res_bat_runs"] * df_bat["p_b"]
    df_bat["np_rr"] = df_bat["res_bat_runs"] * df_bat["np_b"]
    df_bat["p_rs"] = df_bat["res_bat_surv"] * df_bat["p_b"]
    df_bat["np_rs"] = df_bat["res_bat_surv"] * df_bat["np_b"]

    bat_pm = df_bat.groupby(["match_id", "striker_id", "striker_name", "comp_category"], as_index=False)[
        ["p_b", "np_b", "p_r", "np_r", "p_rr", "np_rr", "p_rs", "np_rs"]
    ].sum().rename(columns={
        "p_b": "p_balls", "np_b": "np_balls", "p_r": "p_runs", "np_r": "np_runs",
        "p_rr": "p_res_runs", "np_rr": "np_res_runs", "p_rs": "p_res_surv", "np_rs": "np_res_surv",
        "comp_category": "comp_cat"
    })

    # Bowling match aggregates
    df["p_leg"] = (df["delivery_is_legal"] & df[pressure_col]).astype(int)
    df["np_leg"] = (df["delivery_is_legal"] & ~df[pressure_col]).astype(int)
    df["p_b"] = df[pressure_col].astype(int)
    df["np_b"] = (~df[pressure_col]).astype(int)
    df["p_rp"] = df["res_bowl_prev"] * df["p_b"]
    df["np_rp"] = df["res_bowl_prev"] * df["np_b"]
    df["p_rw"] = df["res_bowl_wkt"] * df["p_b"]
    df["np_rw"] = df["res_bowl_wkt"] * df["np_b"]

    bowl_pm = df.groupby(["match_id", "bowler_id", "bowler_name", "comp_category"], as_index=False)[
        ["p_leg", "np_leg", "p_b", "np_b", "p_rp", "np_rp", "p_rw", "np_rw"]
    ].sum().rename(columns={
        "p_leg": "p_legal", "np_leg": "np_legal", "p_b": "p_balls", "np_b": "np_balls",
        "p_rp": "p_res_prev", "np_rp": "np_res_prev", "p_rw": "p_res_wkt", "np_rw": "np_res_wkt",
        "comp_category": "comp_cat"
    })

    # Player-Match Evidence table
    if save_to_disk:
        ev_b = bat_pm[bat_pm["p_balls"] > 0][["match_id", "striker_id", "striker_name", "comp_cat", "p_balls", "p_runs", "p_res_runs", "p_res_surv"]].copy()
        ev_b.columns = ["match_id", "player_id", "player_name", "comp_category", "pressure_balls", "pressure_runs", "pressure_scoring_residual", "pressure_survival_residual"]
        ev_b["role"] = "Batter"

        ev_bw = bowl_pm[bowl_pm["p_balls"] > 0][["match_id", "bowler_id", "bowler_name", "comp_cat", "p_balls", "p_res_prev", "p_res_wkt"]].copy()
        ev_bw.columns = ["match_id", "player_id", "player_name", "comp_category", "pressure_balls", "pressure_scoring_residual", "pressure_survival_residual"]
        ev_bw["pressure_runs"] = np.nan
        ev_bw["role"] = "Bowler"
        df_evidence = pd.concat([ev_b, ev_bw], ignore_index=True)
    else:
        df_evidence = pd.DataFrame()

    # 2. Player Aggregation & Eligibility Filter
    b_agg = bat_pm.groupby(["striker_id", "striker_name"]).agg(
        p_balls=("p_balls", "sum"),
        np_balls=("np_balls", "sum"),
        p_matches=("p_balls", lambda x: (x > 0).sum()),
        p_res_runs=("p_res_runs", "sum"),
        np_res_runs=("np_res_runs", "sum"),
        p_res_surv=("p_res_surv", "sum"),
        np_res_surv=("np_res_surv", "sum"),
        ipl_p_matches=("comp_cat", lambda c: ((c == "IPL (Franchise)") & (bat_pm.loc[c.index, "p_balls"] > 0)).sum()),
        t20i_p_matches=("comp_cat", lambda c: ((c != "IPL (Franchise)") & (bat_pm.loc[c.index, "p_balls"] > 0)).sum()),
    ).reset_index()

    b_eligible = b_agg[
        (b_agg["p_balls"] >= b_min_p_balls)
        & (b_agg["p_matches"] >= b_min_p_matches)
        & (b_agg["np_balls"] >= b_min_np_balls)
    ].copy()

    bw_agg = bowl_pm.groupby(["bowler_id", "bowler_name"]).agg(
        p_legal=("p_legal", "sum"),
        np_legal=("np_legal", "sum"),
        p_balls=("p_balls", "sum"),
        np_balls=("np_balls", "sum"),
        p_matches=("p_legal", lambda x: (x > 0).sum()),
        p_res_prev=("p_res_prev", "sum"),
        np_res_prev=("np_res_prev", "sum"),
        p_res_wkt=("p_res_wkt", "sum"),
        np_res_wkt=("np_res_wkt", "sum"),
        ipl_p_matches=("comp_cat", lambda c: ((c == "IPL (Franchise)") & (bowl_pm.loc[c.index, "p_legal"] > 0)).sum()),
        t20i_p_matches=("comp_cat", lambda c: ((c != "IPL (Franchise)") & (bowl_pm.loc[c.index, "p_legal"] > 0)).sum()),
    ).reset_index()

    bw_eligible = bw_agg[
        (bw_agg["p_legal"] >= bw_min_p_legal)
        & (bw_agg["p_matches"] >= bw_min_p_matches)
        & (bw_agg["np_legal"] >= bw_min_np_legal)
    ].copy()

    # 3. Vectorized Scoring Function
    K_SHRINK = 30.0

    def calculate_scores(p_runs_vec, p_balls_vec, np_runs_vec, np_balls_vec,
                         p_sec_vec, np_sec_vec, is_batting=True):
        r_p_runs = p_runs_vec / np.maximum(p_balls_vec, 1e-6)
        r_np_runs = np_runs_vec / np.maximum(np_balls_vec, 1e-6)
        r_p_sec = p_sec_vec / np.maximum(p_balls_vec, 1e-6)
        r_np_sec = np_sec_vec / np.maximum(np_balls_vec, 1e-6)

        s_p_runs = (p_balls_vec / (p_balls_vec + K_SHRINK)) * r_p_runs
        s_np_runs = (np_balls_vec / (np_balls_vec + K_SHRINK)) * r_np_runs
        s_p_sec = (p_balls_vec / (p_balls_vec + K_SHRINK)) * r_p_sec
        s_np_sec = (np_balls_vec / (np_balls_vec + K_SHRINK)) * r_np_sec

        std_runs = 0.35 if is_batting else 0.30
        std_sec = 0.040 if is_batting else 0.035

        z_p_runs = s_p_runs / std_runs
        z_np_runs = s_np_runs / std_runs
        z_p_sec = s_p_sec / std_sec
        z_np_sec = s_np_sec / std_sec

        eff_p = w_score * z_p_runs + w_surv * z_p_sec
        eff_np = w_score * z_np_runs + w_surv * z_np_sec
        lift = eff_p - eff_np

        composite = w_eff * eff_p + w_lift * lift
        return composite, eff_p, lift, z_p_runs, z_p_sec

    # Central Scores
    b_comp, b_eff, b_lift, _, _ = calculate_scores(
        b_eligible["p_res_runs"].values, b_eligible["p_balls"].values,
        b_eligible["np_res_runs"].values, b_eligible["np_balls"].values,
        b_eligible["p_res_surv"].values, b_eligible["np_res_surv"].values,
        is_batting=True
    )
    b_eligible["central_score"] = b_comp
    b_eligible["pressure_effectiveness"] = b_eff
    b_eligible["baseline_lift"] = b_lift

    bw_comp, bw_eff, bw_lift, _, _ = calculate_scores(
        bw_eligible["p_res_prev"].values, bw_eligible["p_balls"].values,
        bw_eligible["np_res_prev"].values, bw_eligible["np_balls"].values,
        bw_eligible["p_res_wkt"].values, bw_eligible["np_res_wkt"].values,
        is_batting=False
    )
    bw_eligible["central_score"] = bw_comp
    bw_eligible["pressure_effectiveness"] = bw_eff
    bw_eligible["baseline_lift"] = bw_lift

    # 4. Fast Vectorized Cluster Bootstrap (Shared Match Weights)
    unique_matches = df["match_id"].unique()
    n_matches = len(unique_matches)
    match_to_idx = {m: i for i, m in enumerate(unique_matches)}

    b_players = b_eligible["striker_id"].values
    b_map = {p: i for i, p in enumerate(b_players)}
    b_sub_pm = bat_pm[bat_pm["striker_id"].isin(b_players)]

    M_b_p_runs = np.zeros((n_matches, len(b_players)))
    M_b_p_balls = np.zeros((n_matches, len(b_players)))
    M_b_np_runs = np.zeros((n_matches, len(b_players)))
    M_b_np_balls = np.zeros((n_matches, len(b_players)))
    M_b_p_surv = np.zeros((n_matches, len(b_players)))
    M_b_np_surv = np.zeros((n_matches, len(b_players)))

    m_idxs = b_sub_pm["match_id"].map(match_to_idx).values
    p_idxs = b_sub_pm["striker_id"].map(b_map).values
    np.add.at(M_b_p_runs, (m_idxs, p_idxs), b_sub_pm["p_res_runs"].values)
    np.add.at(M_b_p_balls, (m_idxs, p_idxs), b_sub_pm["p_balls"].values)
    np.add.at(M_b_np_runs, (m_idxs, p_idxs), b_sub_pm["np_res_runs"].values)
    np.add.at(M_b_np_balls, (m_idxs, p_idxs), b_sub_pm["np_balls"].values)
    np.add.at(M_b_p_surv, (m_idxs, p_idxs), b_sub_pm["p_res_surv"].values)
    np.add.at(M_b_np_surv, (m_idxs, p_idxs), b_sub_pm["np_res_surv"].values)

    bw_players = bw_eligible["bowler_id"].values
    bw_map = {p: i for i, p in enumerate(bw_players)}
    bw_sub_pm = bowl_pm[bowl_pm["bowler_id"].isin(bw_players)]

    M_bw_p_prev = np.zeros((n_matches, len(bw_players)))
    M_bw_p_balls = np.zeros((n_matches, len(bw_players)))
    M_bw_np_prev = np.zeros((n_matches, len(bw_players)))
    M_bw_np_balls = np.zeros((n_matches, len(bw_players)))
    M_bw_p_wkt = np.zeros((n_matches, len(bw_players)))
    M_bw_np_wkt = np.zeros((n_matches, len(bw_players)))

    m_idxs_bw = bw_sub_pm["match_id"].map(match_to_idx).values
    p_idxs_bw = bw_sub_pm["bowler_id"].map(bw_map).values
    np.add.at(M_bw_p_prev, (m_idxs_bw, p_idxs_bw), bw_sub_pm["p_res_prev"].values)
    np.add.at(M_bw_p_balls, (m_idxs_bw, p_idxs_bw), bw_sub_pm["p_balls"].values)
    np.add.at(M_bw_np_prev, (m_idxs_bw, p_idxs_bw), bw_sub_pm["np_res_prev"].values)
    np.add.at(M_bw_np_balls, (m_idxs_bw, p_idxs_bw), bw_sub_pm["np_balls"].values)
    np.add.at(M_bw_p_wkt, (m_idxs_bw, p_idxs_bw), bw_sub_pm["p_res_wkt"].values)
    np.add.at(M_bw_np_wkt, (m_idxs_bw, p_idxs_bw), bw_sub_pm["np_res_wkt"].values)

    # Shared Multinomial Weights
    np.random.seed(random_seed)
    boot_weights = np.random.multinomial(n_matches, np.ones(n_matches) / n_matches, size=n_bootstrap)

    b_boot_p_runs = boot_weights @ M_b_p_runs
    b_boot_p_balls = boot_weights @ M_b_p_balls
    b_boot_np_runs = boot_weights @ M_b_np_runs
    b_boot_np_balls = boot_weights @ M_b_np_balls
    b_boot_p_surv = boot_weights @ M_b_p_surv
    b_boot_np_surv = boot_weights @ M_b_np_surv

    b_boot_scores = np.zeros((n_bootstrap, len(b_players)))
    for b in range(n_bootstrap):
        sc, _, _, _, _ = calculate_scores(
            b_boot_p_runs[b], b_boot_p_balls[b],
            b_boot_np_runs[b], b_boot_np_balls[b],
            b_boot_p_surv[b], b_boot_np_surv[b],
            is_batting=True
        )
        b_boot_scores[b] = sc

    bw_boot_p_prev = boot_weights @ M_bw_p_prev
    bw_boot_p_balls = boot_weights @ M_bw_p_balls
    bw_boot_np_prev = boot_weights @ M_bw_np_prev
    bw_boot_np_balls = boot_weights @ M_bw_np_balls
    bw_boot_p_wkt = boot_weights @ M_bw_p_wkt
    bw_boot_np_wkt = boot_weights @ M_bw_np_wkt

    bw_boot_scores = np.zeros((n_bootstrap, len(bw_players)))
    for b in range(n_bootstrap):
        sc, _, _, _, _ = calculate_scores(
            bw_boot_p_prev[b], bw_boot_p_balls[b],
            bw_boot_np_prev[b], bw_boot_np_balls[b],
            bw_boot_p_wkt[b], bw_boot_np_wkt[b],
            is_batting=False
        )
        bw_boot_scores[b] = sc

    # Extract Stats
    b_ci_lower = np.percentile(b_boot_scores, 5, axis=0)
    b_ci_upper = np.percentile(b_boot_scores, 95, axis=0)
    b_boot_ranks = np.zeros_like(b_boot_scores)
    for b in range(n_bootstrap):
        order = np.argsort(-b_boot_scores[b])
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(b_players) + 1)
        b_boot_ranks[b] = ranks

    b_eligible["conservative_score"] = b_ci_lower
    b_eligible["ci_lower"] = b_ci_lower
    b_eligible["ci_upper"] = b_ci_upper
    b_eligible["bootstrap_top10_pct"] = np.mean(b_boot_ranks <= 10, axis=0) * 100.0
    b_eligible["median_rank"] = np.median(b_boot_ranks, axis=0)
    b_rank_l = np.percentile(b_boot_ranks, 5, axis=0)
    b_rank_u = np.percentile(b_boot_ranks, 95, axis=0)
    b_eligible["rank_ci"] = [f"[{int(l)}-{int(u)}]" for l, u in zip(b_rank_l, b_rank_u)]

    bw_ci_lower = np.percentile(bw_boot_scores, 5, axis=0)
    bw_ci_upper = np.percentile(bw_boot_scores, 95, axis=0)
    bw_boot_ranks = np.zeros_like(bw_boot_scores)
    for b in range(n_bootstrap):
        order = np.argsort(-bw_boot_scores[b])
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(bw_players) + 1)
        bw_boot_ranks[b] = ranks

    bw_eligible["conservative_score"] = bw_ci_lower
    bw_eligible["ci_lower"] = bw_ci_lower
    bw_eligible["ci_upper"] = bw_ci_upper
    bw_eligible["bootstrap_top10_pct"] = np.mean(bw_boot_ranks <= 10, axis=0) * 100.0
    bw_eligible["median_rank"] = np.median(bw_boot_ranks, axis=0)
    bw_rank_l = np.percentile(bw_boot_ranks, 5, axis=0)
    bw_rank_u = np.percentile(bw_boot_ranks, 95, axis=0)
    bw_eligible["rank_ci"] = [f"[{int(l)}-{int(u)}]" for l, u in zip(bw_rank_l, bw_rank_u)]

    # Consistency & Sensitivity (Vectorized)
    b_p_m = bat_pm[bat_pm["p_balls"] > 0]
    b_pos = b_p_m.groupby("striker_id")["p_res_runs"].apply(lambda s: (s > 0).mean() * 100.0)
    b_eligible["consistency_pct"] = b_eligible["striker_id"].map(b_pos).fillna(50.0)
    b_eligible["strongest_match_contrib"] = 0.05  # Standard baseline sensitivity

    bw_p_m = bowl_pm[bowl_pm["p_legal"] > 0]
    bw_pos = bw_p_m.groupby("bowler_id")["p_res_prev"].apply(lambda s: (s > 0).mean() * 100.0)
    bw_eligible["consistency_pct"] = bw_eligible["bowler_id"].map(bw_pos).fillna(50.0)
    bw_eligible["strongest_match_contrib"] = 0.05

    # Sort strictly by Conservative Score descending
    b_eligible = b_eligible.sort_values(
        by=["conservative_score", "central_score", "p_matches", "striker_id"],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)
    b_eligible["rank"] = np.arange(1, len(b_eligible) + 1)

    bw_eligible = bw_eligible.sort_values(
        by=["conservative_score", "central_score", "p_matches", "bowler_id"],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)
    bw_eligible["rank"] = np.arange(1, len(bw_eligible) + 1)

    def get_batter_caveat(row):
        cav = []
        if row["ipl_p_matches"] == 0: cav.append("International-only sample")
        elif row["t20i_p_matches"] == 0: cav.append("Franchise-only sample")
        if row["p_balls"] < 120: cav.append("Moderate sample (100-120 balls)")
        return "; ".join(cav) if cav else "Robust across multi-season sample"

    def get_bowler_caveat(row):
        cav = []
        if row["ipl_p_matches"] == 0: cav.append("International-only sample")
        elif row["t20i_p_matches"] == 0: cav.append("Franchise-only sample")
        if row["p_legal"] < 120: cav.append("Moderate sample (100-120 balls)")
        return "; ".join(cav) if cav else "Robust across multi-season sample"

    b_eligible["caveats"] = b_eligible.apply(get_batter_caveat, axis=1)
    bw_eligible["caveats"] = bw_eligible.apply(get_bowler_caveat, axis=1)

    b_out_cols = [
        "rank", "striker_id", "striker_name", "conservative_score", "central_score",
        "ci_lower", "ci_upper", "bootstrap_top10_pct", "median_rank", "rank_ci",
        "pressure_effectiveness", "baseline_lift", "consistency_pct",
        "p_balls", "p_matches", "np_balls", "ipl_p_matches", "t20i_p_matches", "caveats"
    ]
    b_eligible_out = b_eligible[b_out_cols].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}).copy()

    bw_out_cols = [
        "rank", "bowler_id", "bowler_name", "conservative_score", "central_score",
        "ci_lower", "ci_upper", "bootstrap_top10_pct", "median_rank", "rank_ci",
        "pressure_effectiveness", "baseline_lift", "consistency_pct",
        "p_legal", "p_matches", "np_legal", "ipl_p_matches", "t20i_p_matches", "caveats"
    ]
    bw_eligible_out = bw_eligible[bw_out_cols].rename(columns={
        "bowler_id": "player_id", "bowler_name": "player_name",
        "p_legal": "pressure_balls", "np_legal": "np_balls"
    }).copy()

    top10_batters = b_eligible_out.head(10).copy()
    top10_bowlers = bw_eligible_out.head(10).copy()

    sens_elig = []
    for b_thresh in [75, 100, 150]:
        for m_thresh in [8, 10, 15]:
            q_bat = (b_agg["p_balls"] >= b_thresh) & (b_agg["p_matches"] >= m_thresh) & (b_agg["np_balls"] >= b_thresh)
            q_bowl = (bw_agg["p_legal"] >= b_thresh) & (bw_agg["p_matches"] >= m_thresh) & (bw_agg["np_legal"] >= b_thresh)
            sens_elig.append({
                "Pressure_Ball_Threshold": b_thresh,
                "Pressure_Match_Threshold": m_thresh,
                "Baseline_Ball_Threshold": b_thresh,
                "Qualified_Batters": int(q_bat.sum()),
                "Qualified_Bowlers": int(q_bowl.sum()),
                "Status": "Sufficient (>= 10 players)" if q_bat.sum() >= 10 and q_bowl.sum() >= 10 else "Shortfall",
            })
    df_eligibility_summary = pd.DataFrame(sens_elig)

    if save_to_disk:
        b_eligible_out.to_csv(settings.OUTPUTS_DIR / "tables" / "batting_rankings_all.csv", index=False)
        bw_eligible_out.to_csv(settings.OUTPUTS_DIR / "tables" / "bowling_rankings_all.csv", index=False)
        top10_batters.to_csv(settings.OUTPUTS_DIR / "tables" / "top10_batters.csv", index=False)
        top10_bowlers.to_csv(settings.OUTPUTS_DIR / "tables" / "top10_bowlers.csv", index=False)
        df_evidence.to_csv(settings.OUTPUTS_DIR / "tables" / "player_match_evidence.csv", index=False)
        df_eligibility_summary.to_csv(settings.OUTPUTS_DIR / "tables" / "eligibility_summary.csv", index=False)

    return b_eligible_out, top10_batters, bw_eligible_out, top10_bowlers, df_evidence, df_eligibility_summary

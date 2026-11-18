"""Match-State Reconstruction Engine.

Builds a fully validated, delivery-by-delivery pre-delivery match-state dataset
from raw cricket data pack files, adhering strictly to official cricket calculation
rules and distinguishing pre-delivery state from post-delivery outcomes.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from config.settings import settings
from src.data.loader import (
    load_ball_by_ball,
    load_competitions,
    load_matches,
    load_teams,
    get_clean_playing_eleven,
    load_mappings,
)
from src.state.rules import (
    calculate_bowler_runs_conceded,
    calculate_crr,
    calculate_rrr,
    calculate_team_runs,
    get_innings_phase,
    is_batter_ball_faced,
    is_bowler_wicket,
    is_legal_delivery,
    is_team_wicket,
)
from src.utils.logging_utils import setup_logger

logger = setup_logger("match_state_reconstructor")


def categorize_competition(comp_name: str, match_format: str) -> str:
    """Classify competition into clean, explicit domain categories."""
    name = str(comp_name)
    fmt = str(match_format)
    if "IPL" in name:
        return "IPL (Franchise)"
    elif "Emerging" in name or "Rising Stars" in name:
        return "Emerging Teams (T20)"
    elif any(kw in name for kw in ["Tri Series", "Tri-Series", "Tri-Nation"]):
        return "International Tri-Series (T20I)"
    elif "Asia Cup" in name:
        return "Multi-Nation Tournament (T20I)"
    elif fmt == "T20I":
        return "Bilateral Series (T20I)"
    else:
        return "Other T20"


class MatchStateReconstructor:
    """Reconstructs pre-delivery match state across all matches and deliveries."""

    def __init__(
        self,
        bbb: Optional[pd.DataFrame] = None,
        matches: Optional[pd.DataFrame] = None,
        competitions: Optional[pd.DataFrame] = None,
        teams: Optional[pd.DataFrame] = None,
    ) -> None:
        self.bbb = bbb if bbb is not None else load_ball_by_ball()
        self.matches = matches if matches is not None else load_matches()
        self.competitions = competitions if competitions is not None else load_competitions()
        self.teams = teams if teams is not None else load_teams()

    def reconstruct(self) -> pd.DataFrame:
        """Execute full match-state reconstruction with field-level validity flags."""
        logger.info("Starting match-state reconstruction across 200,999 deliveries...")

        # 1. Prepare delivery-level outcome fields
        df = self.bbb.copy()
        df = df.sort_values(
            by=["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
        ).reset_index(drop=True)

        # Stable unique delivery key
        df["delivery_key"] = (
            df["match_id"].astype(str)
            + "_"
            + df["innings"].astype(str)
            + "_"
            + df["innings_ball_num"].astype(str)
        )

        # Calculate delivery-level outcomes
        df["delivery_runs"] = df["runs"].astype(int)
        df["delivery_extras1"] = df["extras1_runs"].astype(int)
        df["delivery_extras2"] = df["extras_2_runs"].astype(int)

        # Team runs on delivery: runs + extras1 + extras2
        df["delivery_total_team_runs"] = (
            df["delivery_runs"] + df["delivery_extras1"] + df["delivery_extras2"]
        )

        # Legal delivery flag: False for wide, Overstep, other
        df["delivery_is_legal"] = ~df["extras_type"].isin(["wide", "Overstep", "other"])

        # Batter ball faced flag: False strictly for wides (No-balls count as balls faced)
        df["delivery_is_batter_ball_faced"] = df["extras_type"] != "wide"

        # Team wicket flag: True when is_wicket is True
        df["delivery_is_team_wicket"] = df["is_wicket"].astype(bool)

        # Bowler wicket flag: True strictly for bowler-credited dismissals
        bowler_types = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}
        df["delivery_is_bowler_wicket"] = df["delivery_is_team_wicket"] & df["dismissal_type"].isin(bowler_types)
        df["delivery_dismissal_type"] = df["dismissal_type"]

        # Note: Do NOT automatically fall back to striker_id if dismissed_player_id is NaN!
        # Preserve known raw attribution without inventing identities.
        df["delivery_dismissed_player_id"] = df["dismissed_player_id"]

        # Bowler runs conceded:
        # Standard ordinary delivery without extras charges bat runs + any extra1
        is_wide = df["extras_type"] == "wide"
        is_noball = df["extras_type"].isin(["Overstep", "other"])
        is_field_extra = df["extras_type"].isin(["byes", "legbyes", "Penalty"])
        df["delivery_bowler_runs_conceded"] = np.where(
            is_field_extra,
            df["delivery_runs"],
            df["delivery_runs"] + df["delivery_extras1"],
        )

        # 2. Cumulative pre-delivery state within each (match_id, innings)
        grouped = df.groupby(["match_id", "innings"])
        df["pre_score"] = grouped["delivery_total_team_runs"].cumsum() - df["delivery_total_team_runs"]
        df["pre_legal_balls"] = grouped["delivery_is_legal"].cumsum() - df["delivery_is_legal"]
        df["pre_wickets"] = grouped["delivery_is_team_wicket"].cumsum() - df["delivery_is_team_wicket"]

        # Current Run Rate (CRR): pre_score / (pre_legal_balls / 6.0)
        # Safe undefined-value handling: NaN when pre_legal_balls == 0
        df["is_crr_valid"] = df["pre_legal_balls"] > 0
        df["pre_crr"] = np.where(
            df["is_crr_valid"],
            np.round((df["pre_score"] / df["pre_legal_balls"]) * 6.0, 3),
            np.nan,
        )

        # 3. Innings totals for target calculations
        inn1_scores = df[df["innings"] == 1].groupby("match_id")["delivery_total_team_runs"].sum().rename("inn1_total")
        inn3_scores = df[df["innings"] == 3].groupby("match_id")["delivery_total_team_runs"].sum().rename("inn3_total")

        df = df.merge(inn1_scores, on="match_id", how="left")
        df = df.merge(inn3_scores, on="match_id", how="left")

        # 4. Match metadata enrichment
        match_cols = [
            "match_id",
            "comp_id",
            "match_date",
            "stage",
            "knock_out",
            "home_team_id",
            "home_team",
            "away_team_id",
            "away_team",
            "first_inn_revised_overs",
            "second_inn_revised_overs",
            "revised_target",
            "result",
        ]
        df = df.merge(self.matches[match_cols], on="match_id", how="left")

        # Competition metadata enrichment
        comp_cols = ["comp_id", "comp_name", "match_format", "season"]
        df = df.merge(self.competitions[comp_cols], on="comp_id", how="left")
        df["comp_category"] = df.apply(
            lambda r: categorize_competition(r["comp_name"], r["match_format"]), axis=1
        )

        # Team name enrichment
        team_lookup = self.teams[["team_id", "team_name"]].drop_duplicates().set_index("team_id")["team_name"].to_dict()
        df["batting_team_name"] = df["batting_team_id"].map(team_lookup)
        df["bowling_team_name"] = df["bowling_team_id"].map(team_lookup)

        # 5. Super Over and Innings Delivery Limits
        df["is_super_over"] = df["innings"].isin([3, 4])

        # Delivery limits:
        # Standard: 120 balls (20 overs)
        # Super over: 6 balls
        # Shortened pre-match: revised overs (stored as balls, e.g. 48.0 = 48 balls = 8 overs)
        has_revised_o1 = df["first_inn_revised_overs"].notna()
        has_revised_o2 = df["second_inn_revised_overs"].notna()
        has_revised_target = df["revised_target"].notna()

        # Check for mid-innings rain stoppages:
        # An innings has an unresolved limit timing if overs were revised but source metadata
        # cannot verify that the reduction was established before ball 1 of that innings.
        is_inn1_revised = has_revised_o1
        is_inn2_revised = has_revised_o2 | has_revised_target

        limit_series = pd.Series(120, index=df.index, dtype=int)
        limit_series = np.where(df["is_super_over"], 6, limit_series)
        
        # When first_inn_revised_overs is populated:
        first_rev_filled = df["first_inn_revised_overs"].fillna(120).astype(int)
        second_rev_filled = df["second_inn_revised_overs"].fillna(120).astype(int)
        
        limit_series = np.where((~df["is_super_over"]) & has_revised_o1 & (df["innings"] == 1), first_rev_filled, limit_series)
        limit_series = np.where((~df["is_super_over"]) & has_revised_o2 & (df["innings"] == 2), second_rev_filled, limit_series)
        df["innings_legal_ball_limit"] = limit_series

        # Unclipped legal balls remaining
        df["unclipped_remaining_balls"] = df["innings_legal_ball_limit"] - df["pre_legal_balls"]
        # Explicitly flag any negative remaining-ball anomaly before clipping
        df["is_remaining_balls_anomaly"] = df["unclipped_remaining_balls"] < 0
        df["pre_legal_balls_remaining"] = np.maximum(0, df["unclipped_remaining_balls"])

        # Field-level validity flag: is_legal_balls_remaining_valid
        # False if the innings had a rain interruption where stoppage timing is unknown
        df["is_legal_balls_remaining_valid"] = (
            (~df["is_super_over"])
            & (~((df["innings"] == 2) & is_inn2_revised))
            & (~((df["innings"] == 1) & is_inn1_revised))
        ) | (df["is_super_over"])

        # 6. Target and Required Run Rate (RRR)
        # For standard uninterrupted Innings 2: target is inn1_total + 1
        # For Super Over Innings 4: target is inn3_total + 1
        # For rain-affected chases: target timing is unresolved without ball-by-ball stoppage markers
        df["is_target_valid"] = (
            ((df["innings"] == 2) & (~is_inn2_revised) & df["inn1_total"].notna())
            | ((df["innings"] == 4) & df["inn3_total"].notna())
        )

        target_series = pd.Series(np.nan, index=df.index, dtype=float)
        target_series = np.where((df["innings"] == 2) & (~is_inn2_revised) & df["inn1_total"].notna(), df["inn1_total"] + 1, target_series)
        target_series = np.where((df["innings"] == 4) & df["inn3_total"].notna(), df["inn3_total"] + 1, target_series)
        df["applicable_target"] = target_series

        # Runs required before delivery
        df["pre_runs_required"] = np.where(
            df["is_target_valid"],
            np.maximum(0, df["applicable_target"] - df["pre_score"]),
            np.nan,
        )

        # Field-level validity flag: is_rrr_valid
        df["is_rrr_valid"] = (
            df["is_target_valid"]
            & df["is_legal_balls_remaining_valid"]
            & (df["pre_legal_balls_remaining"] > 0)
        )

        target_reached = df["is_target_valid"] & (df["pre_runs_required"] <= 0)
        can_compute_rrr = df["is_rrr_valid"] & (df["pre_runs_required"] > 0)

        rrr_series = pd.Series(np.nan, index=df.index, dtype=float)
        rrr_series = np.where(target_reached, 0.0, rrr_series)
        rrr_series = np.where(
            can_compute_rrr,
            np.round((df["pre_runs_required"] / df["pre_legal_balls_remaining"]) * 6.0, 3),
            rrr_series,
        )
        df["pre_rrr"] = rrr_series

        # 7. Innings Phase
        df["innings_phase"] = [
            get_innings_phase(overid, is_so, limit)
            for overid, is_so, limit in zip(
                df["overid"], df["is_super_over"], df["innings_legal_ball_limit"]
            )
        ]

        # 8. Detailed Quality Flags & Exclusion Register
        # Identify specific exclusion reasons for each delivery
        exclusion_lists: List[str] = []
        for is_so, inn, inn1_rev, inn2_rev in zip(
            df["is_super_over"], df["innings"], is_inn1_revised, is_inn2_revised
        ):
            reasons = []
            if is_so:
                reasons.append("SUPER_OVER_SEPARATE_STATE")
            if inn == 2 and inn2_rev:
                reasons.append("INTERRUPTED_TARGET_TIMING_UNRESOLVED")
            if inn == 1 and inn1_rev:
                reasons.append("INTERRUPTED_FIRST_INNINGS_TIMING_UNRESOLVED")
            exclusion_lists.append(";".join(reasons) if reasons else "NONE")

        df["exclusion_reasons"] = exclusion_lists

        # Eligible pressure state:
        # Deliveries in standard 20-over uninterrupted innings (both inn 1 and inn 2)
        df["is_valid_pressure_state"] = (
            (~df["is_super_over"])
            & (~((df["innings"] == 2) & is_inn2_revised))
            & (~((df["innings"] == 1) & is_inn1_revised))
            & (df["innings"].isin([1, 2]))
        )

        # Select and order final reconstructed columns
        output_cols = [
            "delivery_key",
            "match_id",
            "comp_id",
            "comp_name",
            "comp_category",
            "match_format",
            "season",
            "match_date",
            "stage",
            "knock_out",
            "batting_team_id",
            "batting_team_name",
            "bowling_team_id",
            "bowling_team_name",
            "striker_id",
            "striker_name",
            "non_striker_id",
            "non_striker_name",
            "bowler_id",
            "bowler_name",
            "innings",
            "is_super_over",
            "overid",
            "over_ball_num",
            "innings_ball_num",
            "delivery_ist_time",
            "pre_score",
            "pre_wickets",
            "pre_legal_balls",
            "innings_legal_ball_limit",
            "unclipped_remaining_balls",
            "is_remaining_balls_anomaly",
            "pre_legal_balls_remaining",
            "is_legal_balls_remaining_valid",
            "applicable_target",
            "is_target_valid",
            "pre_runs_required",
            "is_crr_valid",
            "pre_crr",
            "is_rrr_valid",
            "pre_rrr",
            "innings_phase",
            "delivery_runs",
            "delivery_extras1",
            "delivery_extras2",
            "delivery_total_team_runs",
            "delivery_bowler_runs_conceded",
            "delivery_is_legal",
            "delivery_is_batter_ball_faced",
            "delivery_is_team_wicket",
            "delivery_is_bowler_wicket",
            "delivery_dismissal_type",
            "delivery_dismissed_player_id",
            "pace_or_spin",
            "stroke",
            "delivery_style",
            "is_valid_pressure_state",
            "exclusion_reasons",
        ]

        logger.info(f"Reconstruction complete: {len(df):,} delivery states generated.")
        return df[output_cols]

    def save_dataset(self, df: Optional[pd.DataFrame] = None) -> Tuple[Path, Path]:
        """Save reconstructed dataset to Parquet and compressed CSV."""
        if df is None:
            df = self.reconstruct()

        settings.ensure_directories()
        parquet_path = settings.OUTPUTS_DIR / "match_states.parquet"
        csv_path = settings.OUTPUTS_DIR / "match_states_summary.csv"

        logger.info(f"Saving match states to {parquet_path}...")
        df.to_parquet(parquet_path, index=False)

        logger.info(f"Saving sample summary to {csv_path}...")
        df.head(1000).to_csv(csv_path, index=False)

        return parquet_path, csv_path

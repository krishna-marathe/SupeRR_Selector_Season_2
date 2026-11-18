"""Tests for match-state reconstruction, target rules, Super Overs, and join integrity."""

import pytest
import numpy as np
import pandas as pd
from config.settings import settings
from src.data.loader import (
    load_ball_by_ball,
    load_matches,
    load_competitions,
    load_teams,
    load_playing_eleven,
    get_clean_playing_eleven,
    load_mappings,
)
from src.state.reconstructor import MatchStateReconstructor


@pytest.fixture(scope="session")
def match_state_df():
    """Build or load reconstructed match states for the test session."""
    parquet_path = settings.OUTPUTS_DIR / "match_states.parquet"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    rec = MatchStateReconstructor()
    return rec.reconstruct()


def test_first_delivery_of_innings_state(match_state_df):
    """Test that at ball 1 of every innings, pre-delivery counters are zero and CRR is undefined."""
    first_balls = match_state_df[match_state_df["innings_ball_num"] == 1]
    assert len(first_balls) > 0

    # At ball 1, score before delivery must be 0
    assert (first_balls["pre_score"] == 0).all()
    # At ball 1, wickets lost before delivery must be 0
    assert (first_balls["pre_wickets"] == 0).all()
    # At ball 1, legal balls bowled before delivery must be 0
    assert (first_balls["pre_legal_balls"] == 0).all()
    # At ball 1, Current Run Rate is mathematically undefined (NaN)
    assert first_balls["pre_crr"].isna().all()


def test_reconstruction_row_count_and_keys(match_state_df):
    """Assert reconstruction preserves exactly 200,999 delivery rows and keys are strictly unique."""
    assert len(match_state_df) == 200999
    assert match_state_df["delivery_key"].is_unique


def test_compound_extras_in_dataset(match_state_df):
    """Verify compound extras handling (extras_2_runs > 0) in the reconstructed dataset."""
    compound = match_state_df[match_state_df["delivery_extras2"] > 0]
    assert len(compound) == 36
    # On compound extras (e.g. no ball + byes), total team runs is runs + extras1 + extras2
    expected_team = compound["delivery_runs"] + compound["delivery_extras1"] + compound["delivery_extras2"]
    assert (compound["delivery_total_team_runs"] == expected_team).all()
    # Bowler conceded runs does not include extras2 (byes/leg-byes)
    assert (compound["delivery_bowler_runs_conceded"] < compound["delivery_total_team_runs"]).all()


def test_super_overs_isolation(match_state_df):
    """Verify Super Overs (innings 3 & 4) are flagged and isolated."""
    so_deliveries = match_state_df[match_state_df["innings"].isin([3, 4])]
    assert len(so_deliveries) == 38  # 25 in inn 3, 13 in inn 4 across 6 matches
    assert so_deliveries["is_super_over"].all()
    assert (so_deliveries["innings_legal_ball_limit"] == 6).all()
    assert (so_deliveries["innings_phase"] == "Super Over").all()
    # Super Overs are excluded from regular 20-over pressure states
    assert (~so_deliveries["is_valid_pressure_state"]).all()
    assert (so_deliveries["exclusion_reasons"] == "SUPER_OVER_SEPARATE_STATE").all()


def test_target_revisions_known_vs_unknown_timing(match_state_df):
    """Verify target handling: do not assume equal revised limits occurred before play without evidence."""
    # Match with revised overs/target: match 17395 (India vs SA)
    m17395 = match_state_df[match_state_df["match_id"] == 17395]
    inn2_17395 = m17395[m17395["innings"] == 2]
    # Because source data does not record exact mid-match stoppage timing, target timing is unresolved
    assert (~inn2_17395["is_target_valid"]).all()
    assert inn2_17395["applicable_target"].isna().all()
    assert inn2_17395["pre_rrr"].isna().all()
    assert (inn2_17395["exclusion_reasons"] == "INTERRUPTED_TARGET_TIMING_UNRESOLVED").all()
    assert (~inn2_17395["is_valid_pressure_state"]).all()

    # Standard uninterrupted chase: match 13511 (West Indies vs England)
    m13511 = match_state_df[match_state_df["match_id"] == 13511]
    inn2_13511 = m13511[m13511["innings"] == 2]
    assert inn2_13511["is_target_valid"].all()
    assert (inn2_13511["applicable_target"] == 104.0).all()
    assert inn2_13511["is_valid_pressure_state"].all()
    assert (inn2_13511["exclusion_reasons"] == "NONE").all()


def test_no_negative_remaining_balls_anomalies(match_state_df):
    """Verify that unclipped remaining balls was never strictly negative across the dataset."""
    assert (match_state_df["is_remaining_balls_anomaly"] == False).all()
    assert (match_state_df["unclipped_remaining_balls"] >= 0).all()


def test_playing_eleven_clean_resolution():
    """Verify documented resolution of the 40 duplicate records in playing_eleven."""
    raw_p11 = load_playing_eleven()
    assert len(raw_p11) == 28381

    clean_p11 = get_clean_playing_eleven()
    assert len(clean_p11) == 28341  # Exactly 40 duplicates resolved
    assert clean_p11.duplicated(subset=["match_id", "player_id"]).sum() == 0

    # Verify for match 28962 player 126 (Rohit Sharma) that the actual batting order (2.0) was retained
    # In raw p11, row 7313 had 1.0 and row 7317 had 2.0. The second row (2.0) was the true one!
    rohit_p11 = clean_p11[(clean_p11["match_id"] == 28962) & (clean_p11["player_id"] == 126)]
    assert len(rohit_p11) == 1
    assert rohit_p11["batting_order"].iloc[0] == 2.0


def test_join_multiplication_prevention():
    """Assert that joining ball_by_ball with clean playing_eleven produces zero row inflation."""
    bbb = load_ball_by_ball()
    clean_p11 = get_clean_playing_eleven()

    # Join on striker
    merged = bbb.merge(
        clean_p11[["match_id", "player_id", "is_captain", "is_wk"]],
        left_on=["match_id", "striker_id"],
        right_on=["match_id", "player_id"],
        how="left",
    )
    assert len(merged) == len(bbb) == 200999

"""Tests for cricket calculation rules and delivery domain semantics."""

import pytest
import numpy as np
from src.state.rules import (
    calculate_team_runs,
    calculate_bowler_runs_conceded,
    is_legal_delivery,
    is_batter_ball_faced,
    is_team_wicket,
    is_bowler_wicket,
    get_innings_phase,
    calculate_crr,
    calculate_rrr,
    BOWLER_DISMISSAL_TYPES,
    FIELDING_DISMISSAL_TYPES,
)


def test_ordinary_scoring_delivery():
    """Test standard off-the-bat scoring deliveries."""
    # Dot ball
    assert calculate_team_runs(0, 0, 0) == 0
    assert calculate_bowler_runs_conceded(0, 0, 0, None) == 0
    assert is_legal_delivery(None) is True
    assert is_batter_ball_faced(None) is True

    # Single
    assert calculate_team_runs(1, 0, 0) == 1
    assert calculate_bowler_runs_conceded(1, 0, 0, None) == 1

    # Boundary four and six
    assert calculate_team_runs(4, 0, 0) == 4
    assert calculate_bowler_runs_conceded(4, 0, 0, None) == 4
    assert calculate_team_runs(6, 0, 0) == 6
    assert calculate_bowler_runs_conceded(6, 0, 0, None) == 6


def test_wide_delivery():
    """Test wide delivery rules and ball faced semantics."""
    # 1 wide
    assert calculate_team_runs(0, 1, 0) == 1
    assert calculate_bowler_runs_conceded(0, 1, 0, "wide") == 1
    assert is_legal_delivery("wide") is False
    assert is_batter_ball_faced("wide") is False  # Wides do NOT count as balls faced

    # Wide + 4 running/byes (5 wides)
    assert calculate_team_runs(0, 5, 0) == 5
    assert calculate_bowler_runs_conceded(0, 5, 0, "wide") == 5
    assert is_legal_delivery("wide") is False
    assert is_batter_ball_faced("wide") is False


def test_no_ball_delivery():
    """Test no-ball rules and ball faced semantics."""
    # No-ball dot
    assert calculate_team_runs(0, 1, 0) == 1
    assert calculate_bowler_runs_conceded(0, 1, 0, "Overstep") == 1
    assert is_legal_delivery("Overstep") is False
    assert is_batter_ball_faced("Overstep") is True  # No-balls DO count as balls faced

    # No-ball hit for 4
    assert calculate_team_runs(4, 1, 0) == 5
    assert calculate_bowler_runs_conceded(4, 1, 0, "Overstep") == 5
    assert is_legal_delivery("Overstep") is False
    assert is_batter_ball_faced("Overstep") is True


def test_compound_extras():
    """Test compound extras (No-ball with byes/leg-byes)."""
    # Overstep (1 run penalty) + 4 byes (extras_2_runs = 4)
    team = calculate_team_runs(0, 1, 4)
    bowler = calculate_bowler_runs_conceded(0, 1, 4, "Overstep")
    assert team == 5
    # Bowler is charged only with the no-ball penalty (1 run), NOT the byes/leg-byes
    assert bowler == 1
    assert is_legal_delivery("Overstep") is False
    assert is_batter_ball_faced("Overstep") is True


def test_byes_and_leg_byes():
    """Test byes and leg-byes scoring and bowler exemption."""
    # 4 byes
    assert calculate_team_runs(0, 4, 0) == 4
    assert calculate_bowler_runs_conceded(0, 4, 0, "byes") == 0
    assert is_legal_delivery("byes") is True
    assert is_batter_ball_faced("byes") is True

    # 1 leg-bye
    assert calculate_team_runs(0, 1, 0) == 1
    assert calculate_bowler_runs_conceded(0, 1, 0, "legbyes") == 0
    assert is_legal_delivery("legbyes") is True
    assert is_batter_ball_faced("legbyes") is True


def test_striker_and_non_striker_wickets():
    """Test wickets credited to bowler vs fielding dismissals."""
    # Bowler wicket: Caught
    assert is_team_wicket(True) is True
    assert is_bowler_wicket(True, "Caught") is True
    assert is_bowler_wicket(True, "Bowled") is True
    assert is_bowler_wicket(True, "LBW") is True
    assert is_bowler_wicket(True, "Stump") is True
    assert is_bowler_wicket(True, "Hit Wicket") is True

    # Fielding wicket: RunOut (striker or non-striker)
    assert is_team_wicket(True) is True
    assert is_bowler_wicket(True, "RunOut") is False

    # Retired Out
    assert is_team_wicket(True) is True
    assert is_bowler_wicket(True, "Retire Out") is False

    # Unresolved departure / Retired hurt where is_wicket is False
    assert is_team_wicket(False) is False
    assert is_bowler_wicket(False, None) is False


def test_run_rate_edge_cases():
    """Test Current Run Rate (CRR) and Required Run Rate (RRR) edge cases."""
    # First delivery of innings (0 legal balls bowled)
    assert calculate_crr(0, 0) is None
    assert calculate_crr(5, 0) is None

    # Normal CRR
    assert calculate_crr(10, 6) == 10.0
    assert calculate_crr(15, 12) == 7.5

    # Target already achieved (runs_required <= 0)
    assert calculate_rrr(0, 10) == 0.0
    assert calculate_rrr(-2, 10) == 0.0

    # Balls exhausted but runs still needed (infinite / impossible)
    assert calculate_rrr(5, 0) is None

    # Normal RRR
    assert calculate_rrr(36, 18) == 12.0
    assert calculate_rrr(10, 6) == 10.0


def test_innings_phases():
    """Test standard and special match phases."""
    # Standard 20 overs
    assert get_innings_phase(1, is_super_over=False, innings_legal_limit=120) == "Powerplay"
    assert get_innings_phase(6, is_super_over=False, innings_legal_limit=120) == "Powerplay"
    assert get_innings_phase(7, is_super_over=False, innings_legal_limit=120) == "Middle"
    assert get_innings_phase(15, is_super_over=False, innings_legal_limit=120) == "Middle"
    assert get_innings_phase(16, is_super_over=False, innings_legal_limit=120) == "Death"
    assert get_innings_phase(20, is_super_over=False, innings_legal_limit=120) == "Death"

    # Super over
    assert get_innings_phase(1, is_super_over=True, innings_legal_limit=6) == "Super Over"

    # Shortened match
    assert get_innings_phase(3, is_super_over=False, innings_legal_limit=48) == "Shortened"

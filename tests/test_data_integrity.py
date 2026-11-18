"""Automated data integrity and referential constraint tests."""

import pytest
import pandas as pd
from config.settings import settings
from src.data.loader import load_all_data


@pytest.fixture(scope="session")
def dataset():
    """Load the dataset once per test session."""
    return load_all_data()


def test_files_exist_and_non_empty(dataset):
    """Ensure all required tables are present and non-empty."""
    for table_name, df in dataset.items():
        assert len(df) > 0, f"Table {table_name} is unexpectedly empty."


def test_no_full_duplicate_rows(dataset):
    """Ensure no table contains completely duplicated rows."""
    for table_name, df in dataset.items():
        assert df.duplicated().sum() == 0, f"Table {table_name} contains duplicate rows."


def test_primary_keys_unique(dataset):
    """Verify primary key uniqueness on core entity tables."""
    # Competitions: comp_id
    assert dataset["competitions"]["comp_id"].is_unique, "competitions.comp_id must be unique"

    # Teams: (comp_id, team_id)
    assert not dataset["teams"].duplicated(subset=["comp_id", "team_id"]).any(), (
        "teams (comp_id, team_id) must be unique"
    )

    # Matches: match_id
    assert dataset["matches"]["match_id"].is_unique, "matches.match_id must be unique"

    # Ball by ball: (match_id, innings, innings_ball_num)
    assert not dataset["ball_by_ball"].duplicated(
        subset=["match_id", "innings", "innings_ball_num"]
    ).any(), "ball_by_ball (match_id, innings, innings_ball_num) must be unique"


def test_referential_integrity(dataset):
    """Check foreign key references across tables."""
    comps = dataset["competitions"]
    teams = dataset["teams"]
    matches = dataset["matches"]
    bbb = dataset["ball_by_ball"]
    p11 = dataset["playing_eleven"]

    # All matches reference valid competitions
    assert set(matches["comp_id"]).issubset(set(comps["comp_id"]))

    # All teams reference valid competitions
    assert set(teams["comp_id"]).issubset(set(comps["comp_id"]))

    # All match home and away teams reference valid teams
    match_teams = set(matches["home_team_id"]).union(set(matches["away_team_id"]))
    assert match_teams.issubset(set(teams["team_id"]))

    # All BBB matches reference valid matches in matches.csv
    assert set(bbb["match_id"]).issubset(set(matches["match_id"]))

    # All playing_eleven matches reference valid matches
    assert set(p11["match_id"]).issubset(set(matches["match_id"]))


def test_delivery_runs_consistency(dataset):
    """Ensure runs and extras are non-negative and well-formed."""
    bbb = dataset["ball_by_ball"]
    assert (bbb["runs"] >= 0).all(), "runs must be non-negative"
    assert (bbb["extras1_runs"] >= 0).all(), "extras1_runs must be non-negative"
    assert (bbb["extras_2_runs"] >= 0).all(), "extras_2_runs must be non-negative"

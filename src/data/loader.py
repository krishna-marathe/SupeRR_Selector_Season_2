"""Safe, reproducible data loaders for SupeRR Selector raw CSV data pack.

Guarantees:
1. Zero in-place modifications to the raw source CSVs.
2. Resolution of paths via project settings (configurable via env var DATA_PACK_DIR).
3. Consistent type handling and missing value representations.
"""

from __future__ import annotations
import pandas as pd
from typing import Dict
from config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("data_loader")


def load_competitions() -> pd.DataFrame:
    """Load competitions.csv."""
    path = settings.COMPETITIONS_PATH
    if not path.exists():
        raise FileNotFoundError(f"competitions.csv not found at {path}")
    logger.debug(f"Loading competitions from {path}")
    df = pd.read_csv(path)
    return df


def load_teams() -> pd.DataFrame:
    """Load teams.csv."""
    path = settings.TEAMS_PATH
    if not path.exists():
        raise FileNotFoundError(f"teams.csv not found at {path}")
    logger.debug(f"Loading teams from {path}")
    df = pd.read_csv(path)
    return df


def load_matches() -> pd.DataFrame:
    """Load matches.csv with standardized nullable integer & date types."""
    path = settings.MATCHES_PATH
    if not path.exists():
        raise FileNotFoundError(f"matches.csv not found at {path}")
    logger.debug(f"Loading matches from {path}")
    df = pd.read_csv(
        path,
        dtype={
            "home_team_captain_id": "Float64",
            "away_team_captain_id": "Float64",
            "toss_win_team_id": "Float64",
            "win_team_id": "Float64",
            "first_inn_revised_overs": "Float64",
            "second_inn_revised_overs": "Float64",
            "revised_target": "Float64",
        },
    )
    return df


def load_playing_eleven() -> pd.DataFrame:
    """Load playing_eleven.csv."""
    path = settings.PLAYING_ELEVEN_PATH
    if not path.exists():
        raise FileNotFoundError(f"playing_eleven.csv not found at {path}")
    logger.debug(f"Loading playing_eleven from {path}")
    df = pd.read_csv(
        path,
        dtype={
            "batting_order": "Float64",
            "is_played": "boolean",
            "is_captain": "boolean",
            "is_wk": "boolean",
        },
    )
    return df


def load_mappings() -> pd.DataFrame:
    """Load competition_team_player_mapping.csv."""
    path = settings.MAPPINGS_PATH
    if not path.exists():
        raise FileNotFoundError(f"competition_team_player_mapping.csv not found at {path}")
    logger.debug(f"Loading competition_team_player_mapping from {path}")
    df = pd.read_csv(path)
    return df


def load_ball_by_ball() -> pd.DataFrame:
    """Load ball_by_ball.csv with memory efficiency and preserved original records."""
    path = settings.BALL_BY_BALL_PATH
    if not path.exists():
        raise FileNotFoundError(f"ball_by_ball.csv not found at {path}")
    logger.debug(f"Loading ball_by_ball from {path} (low_memory=False)")
    df = pd.read_csv(
        path,
        low_memory=False,
        dtype={
            "dismissal_type_id": "Float64",
            "dismissed_player_id": "Float64",
            "bowl_speed": "float64",
            "is_four": "boolean",
            "is_six": "boolean",
            "is_wicket": "boolean",
        },
    )
    return df


def load_all_data() -> Dict[str, pd.DataFrame]:
    """Load all 6 tables into an in-memory dictionary of DataFrames."""
    logger.info("Loading all raw data pack tables...")
    return {
        "competitions": load_competitions(),
        "teams": load_teams(),
        "matches": load_matches(),
        "playing_eleven": load_playing_eleven(),
        "competition_team_player_mapping": load_mappings(),
        "ball_by_ball": load_ball_by_ball(),
    }

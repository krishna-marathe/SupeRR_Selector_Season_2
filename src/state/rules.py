"""Cricket calculation rules and domain logic for match-state reconstruction."""

from __future__ import annotations
from typing import Optional, Set
import numpy as np
import pandas as pd

# Bowler-credited dismissal categories under ICC/MCC rules
BOWLER_DISMISSAL_TYPES: Set[str] = {
    "Caught",
    "Bowled",
    "LBW",
    "Stump",
    "Hit Wicket",
}

# Non-bowler dismissal categories (fielding / batter errors)
FIELDING_DISMISSAL_TYPES: Set[str] = {
    "RunOut",
    "Retire Out",
    "Obstracting the field",  # Note: spelling in source data
    "Obstructing the field",
}

# Deliveries requiring re-bowling (illegal deliveries)
ILLEGAL_EXTRAS_TYPES: Set[str] = {
    "wide",
    "Overstep",
    "other",
}


def calculate_team_runs(runs: int, extras1: int, extras2: int) -> int:
    """Calculate total team runs scored on a delivery.
    
    Formula: runs (bat) + extras1_runs (primary penalty) + extras_2_runs (compound extras).
    """
    return int(runs + extras1 + extras2)


def calculate_bowler_runs_conceded(
    runs: int, extras1: int, extras2: int, extras_type: Optional[str]
) -> int:
    """Calculate runs charged to the bowler's individual bowling analysis.
    
    Rules:
    - Ordinary deliveries with missing/NaN extras_type: Bowler concedes bat runs + any extra1.
    - Batter runs off the bat ('runs') are always charged to the bowler.
    - Wides: bowler is charged with wide penalty and running runs in extras1.
    - No-balls ('Overstep', 'other'): bowler is charged with the 1-run penalty in extras1.
      Any byes/leg-byes on a no-ball (recorded in extras_2_runs) are NOT charged to the bowler.
    - Byes, Leg Byes, and Penalty runs are NOT charged to the bowler.
    """
    if extras_type is None or pd.isna(extras_type) or str(extras_type).lower() in ("nan", "none", ""):
        # Standard ordinary delivery without extras
        return int(runs + extras1)

    et = str(extras_type).strip()
    if et in ("wide", "Overstep", "other"):
        return int(runs + extras1)
    elif et in ("byes", "legbyes", "Penalty"):
        return int(runs)
    else:
        # Fallback for any other recorded category
        return int(runs + extras1)


def is_legal_delivery(extras_type: Optional[str]) -> bool:
    """Determine if a delivery is a legal delivery that advances the over ball count.
    
    Wides and No-balls (Overstep, other) are illegal deliveries and must be re-bowled.
    Byes, leg-byes, penalties, and standard deliveries are legal deliveries.
    """
    if extras_type is None or pd.isna(extras_type) or str(extras_type).lower() in ("nan", "none", ""):
        return True
    return str(extras_type).strip() not in ILLEGAL_EXTRAS_TYPES


def is_batter_ball_faced(extras_type: Optional[str]) -> bool:
    """Determine if a delivery counts as a ball faced for the striker's batting statistics.
    
    Rules:
    - Wides do NOT count as a ball faced (batter had no opportunity to hit).
    - No-balls DO count as a ball faced by the batter.
    - All legal deliveries (including byes, leg-byes, and dot balls) count as a ball faced.
    """
    if extras_type is None or pd.isna(extras_type) or str(extras_type).lower() in ("nan", "none", ""):
        return True
    return str(extras_type).strip() != "wide"


def is_team_wicket(is_wicket_flag: bool) -> bool:
    """Determine if an official wicket fell for the batting team on this delivery."""
    return bool(is_wicket_flag)


def is_bowler_wicket(is_wicket_flag: bool, dismissal_type: Optional[str]) -> bool:
    """Determine if a wicket is credited to the bowler's individual figures.
    
    Credits bowler for Caught, Bowled, LBW, Stump, and Hit Wicket.
    Excludes Run Outs, Retire Outs, and Obstructing the field.
    """
    if not is_wicket_flag or dismissal_type is None or pd.isna(dismissal_type) or str(dismissal_type).lower() in ("nan", "none", ""):
        return False
    return str(dismissal_type).strip() in BOWLER_DISMISSAL_TYPES


def get_innings_phase(
    overid: int, is_super_over: bool = False, innings_legal_limit: int = 120
) -> str:
    """Classify the match phase of a delivery under documented rules.
    
    Standard 20-over match (120 legal balls):
    - Overs 1 to 6 (overid 1-6): 'Powerplay'
    - Overs 7 to 15 (overid 7-15): 'Middle'
    - Overs 16 to 20 (overid 16-20): 'Death'
    
    Special cases:
    - Super Over (innings 3 & 4): 'Super Over'
    - Shortened match (limit < 120): 'Shortened'
    """
    if is_super_over:
        return "Super Over"
    if innings_legal_limit < 120:
        return "Shortened"
    if 1 <= overid <= 6:
        return "Powerplay"
    elif 7 <= overid <= 15:
        return "Middle"
    elif 16 <= overid <= 20:
        return "Death"
    return "Other"


def calculate_crr(score: int, legal_balls: int) -> Optional[float]:
    """Calculate Current Run Rate (runs per 6 legal balls).
    
    Handles pre-match and ball-1 edge cases safely:
    - When legal_balls == 0, returns None (mathematically undefined 0/0).
    """
    if legal_balls <= 0:
        return None
    return round((score / legal_balls) * 6.0, 3)


def calculate_rrr(runs_required: int, legal_balls_remaining: int) -> Optional[float]:
    """Calculate Required Run Rate (runs needed per 6 legal balls remaining).
    
    Handles chase state boundary conditions:
    - If runs_required <= 0: returns 0.0 (target already reached / match won).
    - If legal_balls_remaining <= 0 and runs_required > 0: returns None (mathematically impossible / infinite).
    """
    if runs_required <= 0:
        return 0.0
    if legal_balls_remaining <= 0:
        return None
    return round((runs_required / legal_balls_remaining) * 6.0, 3)

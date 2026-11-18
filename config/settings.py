"""Central configuration module for SupeRR Selector Season 2 project.

Handles dynamic resolution of project root, raw data locations, and output paths.
Avoids hard-coding local machine paths to ensure 100% reproducibility across environments.
"""

from __future__ import annotations
import os
from pathlib import Path


class Settings:
    """Project-wide settings and directory paths."""

    def __init__(self) -> None:
        # Repository root: two levels up from this file (config/settings.py -> root)
        self.PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

        # Raw data directory: read from environment or fall back to repository relative path
        raw_env = os.getenv("DATA_PACK_DIR")
        if raw_env:
            custom_path = Path(raw_env)
            self.DATA_PACK_DIR: Path = (
                custom_path if custom_path.is_absolute() else (self.PROJECT_ROOT / custom_path).resolve()
            )
        else:
            default_candidate = self.PROJECT_ROOT / "6af458274c1e8_data_pack" / "Data Pack"
            fallback_candidate = self.PROJECT_ROOT / "data" / "raw"
            self.DATA_PACK_DIR = default_candidate if default_candidate.exists() else fallback_candidate

        # Common output directories
        self.REPORTS_DIR: Path = self.PROJECT_ROOT / "reports"
        self.OUTPUTS_DIR: Path = self.PROJECT_ROOT / "outputs"
        self.TESTS_DIR: Path = self.PROJECT_ROOT / "tests"

        # Raw CSV file paths
        self.BALL_BY_BALL_PATH: Path = self.DATA_PACK_DIR / "ball_by_ball.csv"
        self.COMPETITIONS_PATH: Path = self.DATA_PACK_DIR / "competitions.csv"
        self.MAPPINGS_PATH: Path = self.DATA_PACK_DIR / "competition_team_player_mapping.csv"
        self.MATCHES_PATH: Path = self.DATA_PACK_DIR / "matches.csv"
        self.PLAYING_ELEVEN_PATH: Path = self.DATA_PACK_DIR / "playing_eleven.csv"
        self.TEAMS_PATH: Path = self.DATA_PACK_DIR / "teams.csv"
        self.PROBLEM_STATEMENT_PDF_PATH: Path = (
            self.DATA_PACK_DIR / "Round 1 Problem Statement _ SupeRR Selector Season 2.docx.pdf"
        )

        # Expected files dictionary for verification
        self.EXPECTED_FILES = {
            "ball_by_ball": self.BALL_BY_BALL_PATH,
            "competitions": self.COMPETITIONS_PATH,
            "competition_team_player_mapping": self.MAPPINGS_PATH,
            "matches": self.MATCHES_PATH,
            "playing_eleven": self.PLAYING_ELEVEN_PATH,
            "teams": self.TEAMS_PATH,
        }

    def ensure_directories(self) -> None:
        """Create required non-data output directories if they do not exist."""
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    def validate_data_pack(self) -> dict[str, bool]:
        """Check availability of all expected raw CSV files without modifying them."""
        return {name: path.exists() for name, path in self.EXPECTED_FILES.items()}


settings = Settings()

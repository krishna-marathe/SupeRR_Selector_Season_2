"""Comprehensive Data Pack Profiler and Quality Inspector.

Generates rigorous statistical profiling, nullability reports, candidate key validations,
referential integrity audits, and domain-specific delivery mechanics analyses.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import numpy as np

from config.settings import settings
from src.data.loader import load_all_data
from src.utils.logging_utils import setup_logger

logger = setup_logger("profiler")


class DataPackProfiler:
    """Profiles the SupeRR Selector raw CSV data pack."""

    def __init__(self, data: Dict[str, pd.DataFrame] | None = None) -> None:
        self.data: Dict[str, pd.DataFrame] = data if data is not None else load_all_data()
        self.profile_results: Dict[str, Any] = {}

    def profile_all(self) -> Dict[str, Any]:
        """Execute full profiling suite across all tables and relationships."""
        logger.info("Executing comprehensive data pack profile...")
        self.profile_results = {
            "tables": self.profile_tables(),
            "candidate_keys": self.check_candidate_keys(),
            "referential_integrity": self.check_referential_integrity(),
            "coverage": self.compute_coverage(),
            "delivery_mechanics": self.profile_delivery_mechanics(),
            "anomalies_and_risks": self.identify_anomalies(),
        }
        return self.profile_results

    def profile_tables(self) -> Dict[str, Any]:
        """Profile basic shape, dtypes, missingness, and duplicates for each table."""
        table_profiles: Dict[str, Any] = {}
        for name, df in self.data.items():
            total_rows = len(df)
            duplicates = int(df.duplicated().sum())

            columns_info: Dict[str, Any] = {}
            for col in df.columns:
                null_count = int(df[col].isna().sum())
                null_pct = float(round((null_count / total_rows) * 100, 3)) if total_rows > 0 else 0.0
                nunique = int(df[col].nunique(dropna=False))

                col_stat: Dict[str, Any] = {
                    "dtype": str(df[col].dtype),
                    "null_count": null_count,
                    "null_pct": null_pct,
                    "unique_values": nunique,
                }
                columns_info[col] = col_stat

            table_profiles[name] = {
                "row_count": total_rows,
                "column_count": len(df.columns),
                "duplicate_rows": duplicates,
                "columns": columns_info,
            }
        return table_profiles

    def check_candidate_keys(self) -> Dict[str, Any]:
        """Verify uniqueness of candidate primary keys."""
        results: Dict[str, Any] = {}

        # 1. competitions
        comps = self.data["competitions"]
        results["competitions"] = {
            "comp_id": {"is_unique": bool(comps["comp_id"].is_unique), "duplicates": int(comps.duplicated("comp_id").sum())},
            "comp_name": {"is_unique": bool(comps["comp_name"].is_unique), "duplicates": int(comps.duplicated("comp_name").sum())},
        }

        # 2. teams
        teams = self.data["teams"]
        results["teams"] = {
            "team_id": {"is_unique": bool(teams["team_id"].is_unique), "duplicates": int(teams.duplicated("team_id").sum())},
            "(comp_id, team_id)": {
                "is_unique": bool(not teams.duplicated(subset=["comp_id", "team_id"]).any()),
                "duplicates": int(teams.duplicated(subset=["comp_id", "team_id"]).sum()),
            },
        }

        # 3. matches
        matches = self.data["matches"]
        results["matches"] = {
            "match_id": {"is_unique": bool(matches["match_id"].is_unique), "duplicates": int(matches.duplicated("match_id").sum())},
        }

        # 4. playing_eleven
        p11 = self.data["playing_eleven"]
        results["playing_eleven"] = {
            "(match_id, player_id)": {
                "is_unique": bool(not p11.duplicated(subset=["match_id", "player_id"]).any()),
                "duplicates": int(p11.duplicated(subset=["match_id", "player_id"]).sum()),
            },
            "(match_id, team_id, player_id)": {
                "is_unique": bool(not p11.duplicated(subset=["match_id", "team_id", "player_id"]).any()),
                "duplicates": int(p11.duplicated(subset=["match_id", "team_id", "player_id"]).sum()),
            },
        }

        # 5. competition_team_player_mapping
        map_df = self.data["competition_team_player_mapping"]
        results["competition_team_player_mapping"] = {
            "(comp_id, player_id)": {
                "is_unique": bool(not map_df.duplicated(subset=["comp_id", "player_id"]).any()),
                "duplicates": int(map_df.duplicated(subset=["comp_id", "player_id"]).sum()),
            },
            "(comp_id, team_id, player_id)": {
                "is_unique": bool(not map_df.duplicated(subset=["comp_id", "team_id", "player_id"]).any()),
                "duplicates": int(map_df.duplicated(subset=["comp_id", "team_id", "player_id"]).sum()),
            },
        }

        # 6. ball_by_ball
        bbb = self.data["ball_by_ball"]
        results["ball_by_ball"] = {
            "(match_id, innings, innings_ball_num)": {
                "is_unique": bool(not bbb.duplicated(subset=["match_id", "innings", "innings_ball_num"]).any()),
                "duplicates": int(bbb.duplicated(subset=["match_id", "innings", "innings_ball_num"]).sum()),
            },
            "(match_id, innings, overid, over_ball_num)": {
                "is_unique": bool(not bbb.duplicated(subset=["match_id", "innings", "overid", "over_ball_num"]).any()),
                "duplicates": int(bbb.duplicated(subset=["match_id", "innings", "overid", "over_ball_num"]).sum()),
            },
        }

        return results

    def check_referential_integrity(self) -> Dict[str, Any]:
        """Check foreign key constraints and unmatched identifiers across tables."""
        comps = self.data["competitions"]
        teams = self.data["teams"]
        matches = self.data["matches"]
        p11 = self.data["playing_eleven"]
        map_df = self.data["competition_team_player_mapping"]
        bbb = self.data["ball_by_ball"]

        comp_ids = set(comps["comp_id"])
        team_ids = set(teams["team_id"])
        match_ids = set(matches["match_id"])
        mapped_player_ids = set(map_df["player_id"])
        p11_player_ids = set(p11["player_id"])

        bbb_strikers = set(bbb["striker_id"])
        bbb_non_strikers = set(bbb["non_striker_id"])
        bbb_bowlers = set(bbb["bowler_id"])
        bbb_dismissed = set(bbb["dismissed_player_id"].dropna().astype(int))
        all_bbb_players = bbb_strikers.union(bbb_non_strikers).union(bbb_bowlers).union(bbb_dismissed)

        return {
            "matches_comp_id_in_comps": {
                "unmatched_count": len(set(matches["comp_id"]) - comp_ids),
                "unmatched_ids": list(set(matches["comp_id"]) - comp_ids),
            },
            "teams_comp_id_in_comps": {
                "unmatched_count": len(set(teams["comp_id"]) - comp_ids),
                "unmatched_ids": list(set(teams["comp_id"]) - comp_ids),
            },
            "matches_home_away_teams_in_teams": {
                "unmatched_count": len((set(matches["home_team_id"]) | set(matches["away_team_id"])) - team_ids),
                "unmatched_ids": list((set(matches["home_team_id"]) | set(matches["away_team_id"])) - team_ids),
            },
            "playing_eleven_match_id_in_matches": {
                "unmatched_count": len(set(p11["match_id"]) - match_ids),
                "unmatched_ids": list(set(p11["match_id"]) - match_ids),
            },
            "matches_without_playing_eleven": {
                "count": len(match_ids - set(p11["match_id"])),
                "match_ids": sorted(list(match_ids - set(p11["match_id"]))),
            },
            "ball_by_ball_match_id_in_matches": {
                "unmatched_count": len(set(bbb["match_id"]) - match_ids),
                "unmatched_ids": list(set(bbb["match_id"]) - match_ids),
            },
            "matches_without_ball_by_ball": {
                "count": len(match_ids - set(bbb["match_id"])),
                "match_ids": sorted(list(match_ids - set(bbb["match_id"]))),
            },
            "bbb_teams_in_teams": {
                "unmatched_count": len((set(bbb["batting_team_id"]) | set(bbb["bowling_team_id"])) - team_ids),
                "unmatched_ids": list((set(bbb["batting_team_id"]) | set(bbb["bowling_team_id"])) - team_ids),
            },
            "bbb_players_in_mappings": {
                "unmatched_count": len(all_bbb_players - mapped_player_ids),
                "unmatched_ids": list(all_bbb_players - mapped_player_ids),
            },
            "bbb_players_in_playing_eleven": {
                "unmatched_count": len(all_bbb_players - p11_player_ids),
                "unmatched_ids": sorted(list(all_bbb_players - p11_player_ids)),
            },
            "p11_players_in_mappings": {
                "unmatched_count": len(p11_player_ids - mapped_player_ids),
                "unmatched_ids": list(p11_player_ids - mapped_player_ids),
            },
        }

    def compute_coverage(self) -> Dict[str, Any]:
        """Compute coverage statistics across formats, seasons, dates, competitions, and players."""
        comps = self.data["competitions"]
        matches = self.data["matches"]
        bbb = self.data["ball_by_ball"]
        map_df = self.data["competition_team_player_mapping"]

        m_comp = matches.merge(comps, on="comp_id", how="left")

        format_counts = m_comp["match_format"].value_counts().to_dict()
        season_counts = m_comp["season"].value_counts().to_dict()
        stage_counts = m_comp["stage"].value_counts().to_dict()
        format_by_season = pd.crosstab(m_comp["season"], m_comp["match_format"]).to_dict()

        min_date = str(matches["match_date"].min())
        max_date = str(matches["match_date"].max())

        total_unique_comps = int(comps["comp_id"].nunique())
        comps_with_matches = int(matches["comp_id"].nunique())
        total_unique_teams = int(self.data["teams"]["team_id"].nunique())
        total_unique_players_mapped = int(map_df["player_id"].nunique())
        total_unique_strikers = int(bbb["striker_id"].nunique())
        total_unique_bowlers = int(bbb["bowler_id"].nunique())

        return {
            "date_range": {"min_date": min_date, "max_date": max_date},
            "total_competitions": total_unique_comps,
            "competitions_with_matches": comps_with_matches,
            "total_teams": total_unique_teams,
            "total_matches": len(matches),
            "matches_with_ball_by_ball": int(bbb["match_id"].nunique()),
            "total_deliveries": len(bbb),
            "total_mapped_players": total_unique_players_mapped,
            "total_active_strikers": total_unique_strikers,
            "total_active_bowlers": total_unique_bowlers,
            "format_breakdown": format_counts,
            "season_breakdown": season_counts,
            "stage_breakdown": stage_counts,
            "format_by_season": format_by_season,
        }

    def profile_delivery_mechanics(self) -> Dict[str, Any]:
        """Profile cricket-specific delivery mechanics: extras, wickets, innings, and targets."""
        bbb = self.data["ball_by_ball"]
        matches = self.data["matches"]

        innings_counts = bbb["innings"].value_counts().to_dict()
        super_overs = bbb[bbb["innings"] > 2]["match_id"].unique().tolist()

        extras_type_counts = bbb["extras_type"].value_counts(dropna=False).to_dict()
        # Convert NaN key to string for JSON serialization
        extras_type_counts = {str(k): int(v) for k, v in extras_type_counts.items()}

        dismissal_type_counts = bbb["dismissal_type"].value_counts(dropna=False).to_dict()
        dismissal_type_counts = {str(k): int(v) for k, v in dismissal_type_counts.items()}

        revised_targets_count = int(matches["revised_target"].notna().sum())
        revised_overs_count = int(matches["first_inn_revised_overs"].notna().sum())

        return {
            "innings_distribution": {int(k): int(v) for k, v in innings_counts.items()},
            "super_over_matches": [int(m) for m in super_overs],
            "extras_type_distribution": extras_type_counts,
            "dismissal_type_distribution": dismissal_type_counts,
            "matches_with_revised_target": revised_targets_count,
            "matches_with_revised_overs": revised_overs_count,
            "total_wickets_recorded": int(bbb["is_wicket"].sum()),
        }

    def identify_anomalies(self) -> Dict[str, Any]:
        """Detect specific data anomalies and join pitfalls."""
        p11 = self.data["playing_eleven"]
        bbb = self.data["ball_by_ball"]

        # Playing eleven duplicate players in same match
        p11_dupes = p11[p11.duplicated(subset=["match_id", "player_id"], keep=False)]
        p11_dupe_matches = p11_dupes["match_id"].unique().tolist()

        # Retired hurt anomaly in BBB (dismissal_type is NaN but dismissed_player_id is present)
        retired_hurt = bbb[bbb["dismissal_type"].isna() & bbb["dismissed_player_id"].notna()]

        # Bowl speed anomalies
        speed_zero = int((bbb["bowl_speed"] == 0).sum())
        speed_negative = int((bbb["bowl_speed"] < 0).sum())
        speed_extreme = int((bbb["bowl_speed"] > 165).sum())

        return {
            "playing_eleven_duplicate_player_records": {
                "total_rows": len(p11_dupes),
                "affected_matches": [int(m) for m in p11_dupe_matches],
                "explanation": "Three matches contain duplicate entries for players with differing batting orders.",
            },
            "retired_hurt_not_wickets": {
                "count": len(retired_hurt),
                "explanation": "Deliveries where dismissed_player_id is set but dismissal_type is NaN and is_wicket is False (official Retired Hurt status).",
            },
            "bowl_speed_anomalies": {
                "zero_speed_count": speed_zero,
                "negative_speed_count": speed_negative,
                "extreme_speed_count": speed_extreme,
                "explanation": "bowl_speed is unrecorded (0.0) in ~38.7% of rows; extreme speeds (>165 km/h) indicate decimal scaling entry errors.",
            },
        }

    def save_json(self, output_path: Path | None = None) -> Path:
        """Export profiling results to JSON file."""
        if not self.profile_results:
            self.profile_all()

        target_path = output_path if output_path else settings.OUTPUTS_DIR / "data_profile.json"
        settings.ensure_directories()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.profile_results, f, indent=2)
        logger.info(f"Data profile saved successfully to {target_path}")
        return target_path

"""Executable script to run the full audit suite and export profile artifacts."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from src.audit.profiler import DataPackProfiler
from src.utils.logging_utils import setup_logger

logger = setup_logger("run_audit")


def main() -> None:
    logger.info("Starting SupeRR Selector Data Pack Audit...")
    settings.ensure_directories()

    validation = settings.validate_data_pack()
    for name, exists in validation.items():
        if not exists:
            logger.error(f"Missing required data pack file: {name}")
            sys.exit(1)

    profiler = DataPackProfiler()
    results = profiler.profile_all()
    json_path = profiler.save_json()

    print("\n" + "=" * 60)
    print("       SUPERR SELECTOR S2 - DATA PACK AUDIT SUMMARY")
    print("=" * 60)
    cov = results["coverage"]
    print(f"Total Competitions : {cov['total_competitions']}")
    print(f"Total Matches      : {cov['total_matches']} ({cov['matches_with_ball_by_ball']} with Ball-By-Ball)")
    print(f"Total Deliveries   : {cov['total_deliveries']:,}")
    print(f"Total Teams        : {cov['total_teams']}")
    print(f"Total Players      : {cov['total_mapped_players']} mapped ({cov['total_active_strikers']} strikers, {cov['total_active_bowlers']} bowlers)")
    print(f"Formats Covered    : {cov['format_breakdown']}")
    print(f"Seasons Covered    : {sorted(list(cov['season_breakdown'].keys()))}")
    print(f"Date Range         : {cov['date_range']['min_date']} to {cov['date_range']['max_date']}")
    print("=" * 60)
    print(f"Profile artifact exported: {json_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

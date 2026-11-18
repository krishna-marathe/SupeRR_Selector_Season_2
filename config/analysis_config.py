"""Analysis configuration for SupeRR Selector Season 2.

Declares all inclusion/exclusion rules, pressure definitions, model specifications,
eligibility thresholds, rating weights, and bootstrap settings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class PreflightConfig:
    """Preflight and sample filtering parameters."""
    quarantined_matches: List[int] = field(default_factory=lambda: [18532, 20190, 48610])
    senior_competitions: List[str] = field(
        default_factory=lambda: [
            "IPL (Franchise)",
            "Bilateral Series (T20I)",
            "Multi-Nation Tournament (T20I)",
            "International Tri-Series (T20I)",
        ]
    )
    supplementary_competitions: List[str] = field(
        default_factory=lambda: ["Emerging Teams (T20)"]
    )
    anomaly_missing_extras_rows: List[int] = field(default_factory=lambda: [36854, 107489])
    unresolved_dismissal_rows: List[int] = field(default_factory=lambda: [127899])


@dataclass
class TemporalSplitsConfig:
    """Chronological partitions for model training and validation."""
    development_years: List[int] = field(default_factory=lambda: [2022, 2023, 2024])
    validation_year: int = 2025
    untouched_evaluation_year: int = 2026
    initial_training_year: int = 2022
    primary_scored_start_year: int = 2023


@dataclass
class PressureConfig:
    """Benchmark and model-assisted pressure definitions."""
    # Benchmark 1: Late Chase
    late_chase_max_balls: int = 30
    late_chase_min_rrr: float = 8.0

    # Benchmark 2: Resource Pressure
    resource_max_wickets_in_hand: int = 4  # pre_wickets >= 6
    resource_min_balls_remaining: int = 30

    # Benchmark 3: First Innings Finishing Phase
    inn1_finish_max_balls: int = 30

    # Model-Assisted Alternative
    model_assisted_max_balls: int = 60
    model_assisted_min_win_prob: float = 0.10
    model_assisted_max_win_prob: float = 0.90

    # Robustness variations
    late_phase_variations: List[int] = field(default_factory=lambda: [24, 30, 36])
    rrr_variations: List[float] = field(default_factory=lambda: [7.0, 8.0, 9.0])


@dataclass
class ModelConfig:
    """Expected-performance model hyperparameters."""
    random_seed: int = 42
    hgb_max_iter: int = 50
    hgb_min_samples_leaf: int = 25
    hgb_learning_rate: float = 0.08
    lr_max_iter: int = 1000
    features_runs: List[str] = field(
        default_factory=lambda: [
            "innings",
            "pre_legal_balls",
            "pre_wickets",
            "pre_score",
            "innings_phase_encoded",
            "comp_category_encoded",
        ]
    )
    features_wickets: List[str] = field(
        default_factory=lambda: [
            "innings",
            "pre_legal_balls",
            "pre_wickets",
            "pre_score",
            "innings_phase_encoded",
            "comp_category_encoded",
        ]
    )


@dataclass
class RatingWeightsConfig:
    """Component and composite rating weights."""
    # Base component weights: scoring/prevention vs survival/wicket-taking
    weight_scoring_prevention: float = 0.60
    weight_survival_wickets: float = 0.40

    # Composite weights: absolute pressure effectiveness vs baseline lift
    weight_pressure_effectiveness: float = 0.75
    weight_baseline_lift: float = 0.25

    # Weight alternatives for robustness testing
    component_weight_alternatives: List[Dict[str, float]] = field(
        default_factory=lambda: [
            {"scoring": 0.50, "wickets": 0.50},
            {"scoring": 0.60, "wickets": 0.40},
            {"scoring": 0.70, "wickets": 0.30},
        ]
    )
    composite_weight_alternatives: List[Dict[str, float]] = field(
        default_factory=lambda: [
            {"effectiveness": 0.60, "lift": 0.40},
            {"effectiveness": 0.75, "lift": 0.25},
            {"effectiveness": 0.90, "lift": 0.10},
        ]
    )


@dataclass
class EligibilityConfig:
    """Sample thresholds for qualification."""
    # Primary Batter Thresholds
    batter_min_pressure_balls: int = 100
    batter_min_pressure_matches: int = 10
    batter_min_baseline_balls: int = 100

    # Primary Bowler Thresholds
    bowler_min_pressure_legal_balls: int = 100
    bowler_min_pressure_matches: int = 10
    bowler_min_baseline_legal_balls: int = 100

    # Sensitivity Variations
    pressure_ball_variations: List[int] = field(default_factory=lambda: [75, 100, 150])
    match_variations: List[int] = field(default_factory=lambda: [8, 10, 15])


@dataclass
class BootstrapConfig:
    """Cluster bootstrap configuration."""
    n_replicates: int = 500
    confidence_level: float = 0.90
    random_seed: int = 42
    ranking_criterion: str = "conservative_lower_bound"  # 5th percentile


@dataclass
class AnalysisSettings:
    """Master configuration container."""
    preflight: PreflightConfig = field(default_factory=PreflightConfig)
    temporal: TemporalSplitsConfig = field(default_factory=TemporalSplitsConfig)
    pressure: PressureConfig = field(default_factory=PressureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    weights: RatingWeightsConfig = field(default_factory=RatingWeightsConfig)
    eligibility: EligibilityConfig = field(default_factory=EligibilityConfig)
    bootstrap: BootstrapConfig = field(default_factory=BootstrapConfig)


analysis_settings = AnalysisSettings()

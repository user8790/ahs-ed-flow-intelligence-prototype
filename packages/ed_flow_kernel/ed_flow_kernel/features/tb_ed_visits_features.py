"""TB_ED_VISITS feature builders and constrained analytics."""

from __future__ import annotations

import pandas as pd

from ed_flow.feature_engineering import arrival_patterns, estimate_baseline_parameters, route_probabilities, stage_duration_distributions


def constrained_feature_bundle(visits: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return constrained ED flow features using only TB_ED_VISITS fields."""

    return {
        "arrival_patterns": arrival_patterns(visits),
        "stage_durations": stage_duration_distributions(visits),
        "route_probabilities": route_probabilities(visits),
        "baseline_parameters": estimate_baseline_parameters(visits),
    }

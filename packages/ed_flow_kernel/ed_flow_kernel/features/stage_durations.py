"""Stage duration feature wrappers."""

from __future__ import annotations

import pandas as pd

from ed_flow.feature_engineering import stage_duration_distributions


def stage_duration_features(visits: pd.DataFrame) -> pd.DataFrame:
    """Return stage duration distributions from constrained visit timestamps."""

    return stage_duration_distributions(visits)

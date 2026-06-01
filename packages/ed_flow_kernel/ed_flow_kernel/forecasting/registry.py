"""Forecast model registry helpers."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.modeling import model_registry_frame


def public_model_registry(features: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Build public pressure model registry rows."""

    return model_registry_frame(features, validation, feature_columns)

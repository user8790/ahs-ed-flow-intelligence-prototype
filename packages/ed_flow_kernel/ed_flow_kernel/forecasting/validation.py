"""Forecast validation wrappers."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.modeling import rolling_origin_backtest


def rolling_backtest(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Run rolling-origin backtest for the public pressure model."""

    return rolling_origin_backtest(feature_frame)

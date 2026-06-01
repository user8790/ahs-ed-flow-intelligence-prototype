"""Simple interpretable baseline forecasts."""

from __future__ import annotations

import numpy as np
import pandas as pd


def seasonal_naive(values: pd.Series, horizon: int, season: int = 24) -> np.ndarray:
    """Repeat the latest seasonal pattern for a forecast horizon."""

    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return np.zeros(horizon)
    tail = numeric.tail(season)
    return np.resize(tail.to_numpy(dtype=float), horizon)


def moving_average(values: pd.Series, horizon: int, window: int = 12) -> np.ndarray:
    """Repeat the latest moving average for a forecast horizon."""

    numeric = pd.to_numeric(values, errors="coerce").dropna()
    value = float(numeric.tail(window).mean()) if not numeric.empty else 0.0
    return np.repeat(value, horizon)

"""Uncertainty interval utilities."""

from __future__ import annotations

import pandas as pd


def ensure_p10_p50_p90(frame: pd.DataFrame, p50_col: str = "p50_pressure") -> pd.DataFrame:
    """Ensure a forecast dataframe has P10/P50/P90 columns."""

    out = frame.copy()
    if p50_col not in out:
        out[p50_col] = 0.0
    out["p10_pressure"] = out.get("p10_pressure", (out[p50_col] - 0.1).clip(0, 1))
    out["p90_pressure"] = out.get("p90_pressure", (out[p50_col] + 0.1).clip(0, 1))
    return out

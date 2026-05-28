"""Small shared utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def ensure_datetime(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Convert present columns to pandas datetimes without mutating input."""

    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_datetime(out[column], errors="coerce")
    return out


def hours_between(start: pd.Series, end: pd.Series) -> pd.Series:
    """Return hours between two datetime-like series."""

    return (pd.to_datetime(end) - pd.to_datetime(start)).dt.total_seconds() / 3600


def minutes_between(start: pd.Series, end: pd.Series) -> pd.Series:
    """Return minutes between two datetime-like series."""

    return (pd.to_datetime(end) - pd.to_datetime(start)).dt.total_seconds() / 60


def quantile_interval(values: Iterable[float], lower: float = 0.1, upper: float = 0.9) -> tuple[float, float]:
    """Return a lower/upper quantile interval with NaN-safe defaults."""

    series = pd.Series(list(values), dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if series.empty:
        return (float("nan"), float("nan"))
    return (float(series.quantile(lower)), float(series.quantile(upper)))


def weighted_choice(rng: np.random.Generator, labels: list[str], weights: list[float]) -> str:
    """Choose one label with numpy's Generator using normalized weights."""

    probabilities = np.array(weights, dtype=float)
    probabilities = probabilities / probabilities.sum()
    return str(rng.choice(labels, p=probabilities))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Avoid noisy division guards in metric code."""

    if denominator in (0, 0.0) or pd.isna(denominator):
        return default
    return float(numerator / denominator)


def project_path(*parts: str) -> Path:
    """Return a path below the repository root."""

    return Path(__file__).resolve().parents[2].joinpath(*parts)


def iso_now() -> str:
    """Return current timestamp as a second-resolution ISO string."""

    return datetime.now().replace(microsecond=0).isoformat()


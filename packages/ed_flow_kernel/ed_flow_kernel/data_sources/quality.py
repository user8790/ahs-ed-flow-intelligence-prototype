"""Data-quality wrappers for constrained and public data."""

from __future__ import annotations

import pandas as pd

from ed_flow.metrics import calculate_data_quality
from ed_flow_intelligence.quality import public_data_quality_summary


def constrained_quality(visits: pd.DataFrame) -> dict[str, object]:
    """Run local constrained data-quality checks."""

    return calculate_data_quality(visits)


def public_quality(public_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run public/open fallback source checks."""

    return public_data_quality_summary(public_data)

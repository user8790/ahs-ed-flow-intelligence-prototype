"""Hybrid public/open plus internal-ready feature targets."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.modeling import forecast_internal_targets


def internal_ready_targets(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str) -> pd.DataFrame:
    """Return internal-ready targets adjusted by public pressure context."""

    return forecast_internal_targets(visits, public_data, facility)

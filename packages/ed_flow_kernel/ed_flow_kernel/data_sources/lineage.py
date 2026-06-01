"""Lineage helpers for public-safe and internal-ready surfaces."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.lineage import category_legend_frame, statuses_to_frame


def lineage_category_frame() -> pd.DataFrame:
    """Return lineage categories and display colors."""

    return category_legend_frame()


def refresh_status_frame(status_rows: list[object]) -> pd.DataFrame:
    """Convert refresh status model rows to a dataframe."""

    return statuses_to_frame(status_rows)

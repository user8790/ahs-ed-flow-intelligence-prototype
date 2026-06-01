"""Backend protocol used by Action Intelligence surfaces."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from ed_flow.data_contracts import VisitFilters


class EdFlowBackend(Protocol):
    """Small backend interface shared by local and Snowflake adapters."""

    def load_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame: ...

    def load_recent_ed_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame: ...

    def load_current_active_visits(self, filters: VisitFilters | None = None) -> pd.DataFrame: ...

    def load_chart_context_by_mrn(self, mrn: str): ...

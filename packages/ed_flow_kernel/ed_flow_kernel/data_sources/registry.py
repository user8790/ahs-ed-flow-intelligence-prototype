"""Kernel registry access over public, synthetic, and internal-ready sources."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.data_sources.registry import load_data_source_registry, registry_to_frame


def source_registry_frame() -> pd.DataFrame:
    """Return the normalized source registry as a dataframe."""

    return registry_to_frame(load_data_source_registry())

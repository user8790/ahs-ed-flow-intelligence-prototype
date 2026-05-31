from __future__ import annotations

import pandas as pd

from app import LINEAGE_STATUS_DISPLAY_COLUMNS, lineage_status_display_frame
from ed_flow_intelligence.constants import V2_TAB_NAMES
from ed_flow_intelligence.data_sources.public_adapters import OpenDataHub
from ed_flow_intelligence.data_sources.registry import load_data_source_registry
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data
from ed_flow_intelligence.lineage import LineageCategory, category_legend_frame, statuses_to_frame


def test_refresh_status_rows_include_fallback_and_snowflake_targets(tmp_path) -> None:
    ensure_public_open_data(tmp_path, force=True)
    hub = OpenDataHub(load_data_source_registry(), tmp_path)
    statuses = statuses_to_frame(hub.status_rows())
    assert {"source_id", "category", "freshness_state", "quality_score", "snowflake_target", "fallback_reason"}.issubset(statuses.columns)
    assert statuses["fallback_reason"].str.len().gt(0).all()
    assert statuses["quality_score"].between(0, 1).all()


def test_lineage_legend_and_tab_order_are_complete() -> None:
    legend = category_legend_frame()
    assert set(legend["category"]) == {category.value for category in LineageCategory}
    assert V2_TAB_NAMES[-1] == "Data Linkages & Refresh Status"
    assert len(V2_TAB_NAMES) == 16


def test_lineage_status_display_frame_tolerates_older_cached_columns() -> None:
    older_cached_status = pd.DataFrame(
        [
            {
                "source_id": "ahs_public_wait_times",
                "display_name": "AHS estimated ED wait times",
                "category": "OPEN_DATA",
                "freshness_state": "synthetic fallback current",
            }
        ]
    )
    display = lineage_status_display_frame(older_cached_status)
    assert list(display.columns) == LINEAGE_STATUS_DISPLAY_COLUMNS
    assert display.loc[0, "source_id"] == "ahs_public_wait_times"
    assert display.loc[0, "activation_status"] == ""

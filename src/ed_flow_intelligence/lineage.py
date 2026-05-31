"""Lineage categories and refresh status contracts for v2."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import pandas as pd
from pydantic import BaseModel, Field


class LineageCategory(StrEnum):
    """Data lineage categories shown throughout the app."""

    OPEN_DATA = "OPEN_DATA"
    SYNTHETIC_DATA = "SYNTHETIC_DATA"
    SECURE_INTERNAL_PLACEHOLDER = "SECURE_INTERNAL_PLACEHOLDER"
    SECURE_INTERNAL_READY_SCHEMA = "SECURE_INTERNAL_READY_SCHEMA"
    HYBRID_OPEN_SYNTHETIC = "HYBRID_OPEN_SYNTHETIC"
    HYBRID_OPEN_INTERNAL_READY = "HYBRID_OPEN_INTERNAL_READY"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    USER_INPUT = "USER_INPUT"


LINEAGE_COLORS = {
    LineageCategory.OPEN_DATA: "#2f6f73",
    LineageCategory.SYNTHETIC_DATA: "#6c7a89",
    LineageCategory.SECURE_INTERNAL_PLACEHOLDER: "#8a5a44",
    LineageCategory.SECURE_INTERNAL_READY_SCHEMA: "#335c81",
    LineageCategory.HYBRID_OPEN_SYNTHETIC: "#7a6f2f",
    LineageCategory.HYBRID_OPEN_INTERNAL_READY: "#4d6f3a",
    LineageCategory.MODEL_OUTPUT: "#7c5c9e",
    LineageCategory.USER_INPUT: "#9a5c2e",
}


class SourceDefinition(BaseModel):
    """Configured public, synthetic, or internal-ready source."""

    source_id: str
    display_name: str
    source_family: str
    category: LineageCategory
    official_url: str | None = None
    owner: str = "Prototype"
    expected_refresh_minutes: int | None = None
    local_dataset: str | None = None
    snowflake_target: str | None = None
    pii_risk: str = "none"
    notes: str = ""


class SourceRefreshStatus(BaseModel):
    """Refresh and data-quality status shown in the final tab."""

    source_id: str
    display_name: str
    category: LineageCategory
    owner: str
    official_url: str | None = None
    local_dataset: str | None = None
    snowflake_target: str | None = None
    last_refresh: datetime | None = None
    max_source_timestamp: datetime | None = None
    expected_refresh_minutes: int | None = None
    row_count: int = 0
    freshness_state: str = "not configured"
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    fallback_reason: str = ""
    pii_risk: str = "none"
    notes: str = ""


def lineage_badge(category: LineageCategory | str) -> str:
    """Return HTML for a compact category badge."""

    cat = LineageCategory(category)
    color = LINEAGE_COLORS[cat]
    return (
        f"<span style='display:inline-block;border-radius:999px;padding:0.12rem 0.55rem;"
        f"background:{color};color:white;font-size:0.74rem;font-weight:650'>{cat.value}</span>"
    )


def statuses_to_frame(statuses: list[SourceRefreshStatus]) -> pd.DataFrame:
    """Convert refresh status contracts to a dataframe."""

    return pd.DataFrame([status.model_dump(mode="json") for status in statuses])


def category_legend_frame() -> pd.DataFrame:
    """Return category legend rows for display and tests."""

    return pd.DataFrame(
        [{"category": category.value, "color": color} for category, color in LINEAGE_COLORS.items()]
    )

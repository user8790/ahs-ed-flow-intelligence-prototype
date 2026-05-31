"""Public adapter interfaces with synthetic fallback for local mode."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from ed_flow_intelligence.data_sources.synthetic_open_data import OPEN_DATA_DIR, load_public_open_data
from ed_flow_intelligence.lineage import LineageCategory, SourceDefinition, SourceRefreshStatus


@dataclass
class PublicDataset:
    """Loaded public dataset plus lineage metadata."""

    name: str
    frame: pd.DataFrame
    source: SourceDefinition | None
    fallback_reason: str = "Local prototype uses synthetic fallback cache."


class OpenDataHub:
    """Load public/open-data frames without requiring network access."""

    def __init__(self, registry: list[SourceDefinition], data_dir: Path = OPEN_DATA_DIR):
        self.registry = registry
        self.data_dir = Path(data_dir)
        self._frames = load_public_open_data(self.data_dir)

    def get(self, dataset_name: str) -> pd.DataFrame:
        """Return a cached open-data frame."""

        return self._frames.get(dataset_name, pd.DataFrame()).copy()

    def datasets(self) -> dict[str, pd.DataFrame]:
        """Return all cached frames."""

        return {name: frame.copy() for name, frame in self._frames.items()}

    def refresh_synthetic_cache(self) -> None:
        """Reload the local synthetic cache."""

        self._frames = load_public_open_data(self.data_dir)

    def status_rows(self) -> list[SourceRefreshStatus]:
        """Build refresh status rows for every configured source."""

        rows: list[SourceRefreshStatus] = []
        now = datetime.now()
        for source in self.registry:
            frame = self._frames.get(source.local_dataset or "", pd.DataFrame())
            max_time = _max_timestamp(frame)
            quality = _quality_score(frame, source.category)
            if source.category == LineageCategory.SECURE_INTERNAL_PLACEHOLDER:
                state = "secure placeholder"
                fallback = "Expected secure internal feed; local mode uses synthetic assumption data."
            elif source.category == LineageCategory.SECURE_INTERNAL_READY_SCHEMA:
                state = "internal-ready schema"
                fallback = "Snowflake-ready contract with synthetic local rows."
            elif frame.empty:
                state = "missing local cache"
                fallback = "No local cache frame available."
            else:
                state = "synthetic fallback current"
                fallback = "Official public source configured; local prototype displays synthetic fallback cache."
            rows.append(
                SourceRefreshStatus(
                    source_id=source.source_id,
                    display_name=source.display_name,
                    category=source.category,
                    owner=source.owner,
                    official_url=source.official_url,
                    local_dataset=source.local_dataset,
                    snowflake_target=source.snowflake_target,
                    last_refresh=now,
                    max_source_timestamp=max_time,
                    expected_refresh_minutes=source.expected_refresh_minutes,
                    row_count=int(len(frame)),
                    freshness_state=state,
                    quality_score=quality,
                    fallback_reason=fallback,
                    pii_risk=source.pii_risk,
                    notes=source.notes,
                )
            )
        return rows


def _max_timestamp(frame: pd.DataFrame) -> datetime | None:
    candidates = [column for column in ["timestamp", "posted_timestamp", "week_start", "date"] if column in frame.columns]
    values = []
    for column in candidates:
        series = pd.to_datetime(frame[column], errors="coerce").dropna()
        if not series.empty:
            values.append(series.max())
    if not values:
        return None
    return max(values).to_pydatetime()


def _quality_score(frame: pd.DataFrame, category: LineageCategory) -> float:
    if frame.empty:
        return 0.0
    completeness = 1.0 - float(frame.isna().mean().mean())
    category_penalty = 0.2 if category in {LineageCategory.SECURE_INTERNAL_PLACEHOLDER, LineageCategory.HYBRID_OPEN_SYNTHETIC} else 0.0
    return float(max(0.0, min(1.0, completeness - category_penalty)))


def adapter_registry() -> dict[str, Callable[[OpenDataHub], pd.DataFrame]]:
    """Return callable adapter hooks for Snowflake task parity."""

    return {
        "public_wait_times": lambda hub: hub.get("public_wait_times"),
        "respiratory_surveillance": lambda hub: hub.get("respiratory_surveillance"),
        "environmental_stress": lambda hub: hub.get("environmental_stress"),
        "travel_friction": lambda hub: hub.get("travel_friction"),
        "calendar_context": lambda hub: hub.get("calendar_context"),
        "population_context": lambda hub: hub.get("population_context"),
    }

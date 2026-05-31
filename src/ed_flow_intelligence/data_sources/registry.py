"""Data-source registry for public, synthetic, and Snowflake-ready feeds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
try:
    import yaml
except Exception:  # pragma: no cover - fallback is exercised when PyYAML is absent.
    yaml = None

from ed_flow_intelligence.lineage import LineageCategory, SourceDefinition


DEFAULT_REGISTRY_PATH = Path("config/data_sources.yml")


DEFAULT_SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "ahs_public_wait_times",
        "display_name": "AHS estimated ED wait times",
        "source_family": "public_ed_wait_times",
        "category": "OPEN_DATA",
        "official_url": "https://www.albertahealthservices.ca/waittimes/waittimes.aspx",
        "owner": "Alberta Health Services",
        "expected_refresh_minutes": 5,
        "local_dataset": "public_wait_times",
        "snowflake_target": "OPEN_DATA.AHS_ED_WAIT_TIMES",
        "pii_risk": "none",
        "notes": "Local prototype uses synthetic fallback shaped for AHS posted wait-time monitoring.",
    },
    {
        "source_id": "hqca_ed_metrics",
        "display_name": "HQCA ED historical flow metrics",
        "source_family": "public_historical_ed_metrics",
        "category": "OPEN_DATA",
        "official_url": "https://focus.hqca.ca/",
        "owner": "Health Quality Council of Alberta",
        "expected_refresh_minutes": 10080,
        "local_dataset": "historical_public_ed_metrics",
        "snowflake_target": "OPEN_DATA.HQCA_ED_METRICS",
        "pii_risk": "none",
        "notes": "Used as public validation context where available; not a row-level substitute for TB_ED_VISITS.",
    },
    {
        "source_id": "alberta_respiratory_dashboard",
        "display_name": "Alberta respiratory virus dashboard",
        "source_family": "respiratory_surveillance",
        "category": "OPEN_DATA",
        "official_url": "https://www.alberta.ca/stats/dashboard/respiratory-virus-dashboard.htm",
        "owner": "Government of Alberta",
        "expected_refresh_minutes": 4320,
        "local_dataset": "respiratory_surveillance",
        "snowflake_target": "OPEN_DATA.AB_RESPIRATORY_SURVEILLANCE",
        "pii_risk": "none",
        "notes": "Weekly/biweekly public context for pediatric surge risk.",
    },
    {
        "source_id": "eccc_geomet_weather_alerts",
        "display_name": "ECCC MSC GeoMet weather and alerts",
        "source_family": "weather_air_quality",
        "category": "OPEN_DATA",
        "official_url": "https://api.weather.gc.ca/",
        "owner": "Environment and Climate Change Canada",
        "expected_refresh_minutes": 15,
        "local_dataset": "environmental_stress",
        "snowflake_target": "OPEN_DATA.ECCC_WEATHER_ALERTS",
        "pii_risk": "none",
        "notes": "Prototype uses synthetic weather, heat, smoke, and AQHI features with official-source metadata.",
    },
    {
        "source_id": "alberta_aqhi",
        "display_name": "Alberta AQHI data",
        "source_family": "weather_air_quality",
        "category": "OPEN_DATA",
        "official_url": "https://open.alberta.ca/interact/aqhi",
        "owner": "Government of Alberta",
        "expected_refresh_minutes": 60,
        "local_dataset": "environmental_stress",
        "snowflake_target": "OPEN_DATA.AB_AQHI",
        "pii_risk": "none",
        "notes": "AQHI values are synthetic in local mode and clearly labelled.",
    },
    {
        "source_id": "alberta_wildfire",
        "display_name": "Alberta wildfire maps and data",
        "source_family": "wildfire_smoke",
        "category": "OPEN_DATA",
        "official_url": "https://www.alberta.ca/wildfire-maps-and-data",
        "owner": "Government of Alberta",
        "expected_refresh_minutes": 60,
        "local_dataset": "environmental_stress",
        "snowflake_target": "OPEN_DATA.AB_WILDFIRE_STATUS",
        "pii_risk": "none",
        "notes": "Smoke stress is simulated locally; future Snowflake job can ingest wildfire GIS services.",
    },
    {
        "source_id": "alberta_511_events",
        "display_name": "511 Alberta events and road conditions",
        "source_family": "travel_friction",
        "category": "OPEN_DATA",
        "official_url": "https://511.alberta.ca/developers/doc",
        "owner": "Government of Alberta",
        "expected_refresh_minutes": 15,
        "local_dataset": "travel_friction",
        "snowflake_target": "OPEN_DATA.AB_511_EVENTS",
        "pii_risk": "none",
        "notes": "Local travel disruption counts are synthetic.",
    },
    {
        "source_id": "municipal_open_data_traffic",
        "display_name": "Edmonton and Calgary open traffic data",
        "source_family": "travel_friction",
        "category": "OPEN_DATA",
        "official_url": "https://data.edmonton.ca/",
        "owner": "Municipal open-data programs",
        "expected_refresh_minutes": 60,
        "local_dataset": "travel_friction",
        "snowflake_target": "OPEN_DATA.MUNICIPAL_TRAFFIC_EVENTS",
        "pii_risk": "none",
        "notes": "Use city portals where licensing and reliability meet AHS requirements.",
    },
    {
        "source_id": "alberta_general_holidays",
        "display_name": "Alberta general holidays",
        "source_family": "calendar_context",
        "category": "OPEN_DATA",
        "official_url": "https://www.alberta.ca/alberta-general-holidays",
        "owner": "Government of Alberta",
        "expected_refresh_minutes": 525600,
        "local_dataset": "calendar_context",
        "snowflake_target": "OPEN_DATA.AB_HOLIDAYS",
        "pii_risk": "none",
        "notes": "Calendar features help distinguish predictable demand changes.",
    },
    {
        "source_id": "tb_ed_visits",
        "display_name": "TB_ED_VISITS curated internal visit table",
        "source_family": "secure_internal_ed_flow",
        "category": "SECURE_INTERNAL_READY_SCHEMA",
        "owner": "AHS internal governed Snowflake",
        "expected_refresh_minutes": 60,
        "local_dataset": "synthetic_ed_visits",
        "snowflake_target": "CURATED.TB_ED_VISITS",
        "pii_risk": "sensitive identifiers in source; constrained module excludes direct identifiers",
        "notes": "Local v2 uses synthetic rows shaped to the supplied data contract.",
    },
    {
        "source_id": "chart_review_semantic_views",
        "display_name": "MRN chart-review semantic views",
        "source_family": "secure_internal_chart_review",
        "category": "SECURE_INTERNAL_READY_SCHEMA",
        "owner": "AHS internal governed Snowflake",
        "expected_refresh_minutes": 60,
        "local_dataset": "synthetic_chart_notes",
        "snowflake_target": "DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS.MSB_CLINICAL_GENETICS",
        "pii_risk": "PHI and identifiers in source; mock local summaries only",
        "notes": "PATIENT_CHART to PAT_MRN_ID mapping must be validated before internal use.",
    },
    {
        "source_id": "expanded_operational_feeds",
        "display_name": "Expanded operational system feeds",
        "source_family": "secure_internal_placeholders",
        "category": "SECURE_INTERNAL_PLACEHOLDER",
        "owner": "Future AHS curated Snowflake feeds",
        "expected_refresh_minutes": 15,
        "local_dataset": "synthetic_beds_staffing_diagnostics",
        "snowflake_target": "OPERATIONS.*",
        "pii_risk": "operationally sensitive; may include PHI depending on grain",
        "notes": "Includes ADT bed board, staffing, consult queues, diagnostics, EMS, transfer, and EVS placeholders.",
    },
]


def _normalise_source(raw: dict[str, Any]) -> SourceDefinition:
    raw = dict(raw)
    raw["category"] = LineageCategory(raw["category"])
    return SourceDefinition(**raw)


def load_data_source_registry(path: Path | str | None = DEFAULT_REGISTRY_PATH) -> list[SourceDefinition]:
    """Load the registry from YAML, falling back to built-in definitions."""

    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if registry_path.exists() and yaml is not None:
        raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        sources = raw.get("sources", DEFAULT_SOURCES)
    else:
        sources = DEFAULT_SOURCES
    return [_normalise_source(source) for source in sources]


def registry_to_frame(registry: list[SourceDefinition]) -> pd.DataFrame:
    """Convert source definitions to dataframe rows."""

    return pd.DataFrame([item.model_dump(mode="json") for item in registry])


def sources_for_dataset(registry: list[SourceDefinition], dataset_name: str) -> list[SourceDefinition]:
    """Return sources mapped to a local dataset."""

    return [source for source in registry if source.local_dataset == dataset_name]

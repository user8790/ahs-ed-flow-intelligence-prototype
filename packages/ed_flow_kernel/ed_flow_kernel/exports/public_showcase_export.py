"""Export public-safe JSON artifacts for the Vercel showcase."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ed_flow.config import get_config
from ed_flow.data_contracts import ScenarioConfig, VisitFilters
from ed_flow.local_backend import LocalBackend
from ed_flow.synthetic_data import ensure_synthetic_data
from ed_flow_kernel.config import KernelConfig
from ed_flow_kernel.constants import CAPABILITY_TIERS, PUBLIC_SHOWCASE_TITLE, SOURCE_CATEGORIES
from ed_flow_kernel.contracts.public_artifacts import ActionInterpretation, PublicArtifact
from ed_flow_kernel.governance.privacy import public_payload_has_phi_like_values
from ed_flow_intelligence.advanced_scenarios import ScenarioShockConfig, run_combined_public_scenario
from ed_flow_intelligence.data_sources.public_adapters import OpenDataHub
from ed_flow_intelligence.data_sources.registry import load_data_source_registry, registry_to_frame
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data
from ed_flow_intelligence.lineage import statuses_to_frame
from ed_flow_intelligence.modeling import build_public_feature_matrix, forecast_external_pressure, forecast_internal_targets, rolling_origin_backtest
from ed_flow_intelligence.operational_intelligence import executive_pressure_cockpit, research_capability_map
from ed_flow_intelligence.simulation_vnext import run_enhanced_simulation_summary


ARTIFACT_NAMES = [
    "sites.json",
    "zones.json",
    "capability_map.json",
    "snowflake_portability_map.json",
    "open_data_registry.json",
    "open_data_refresh_status.json",
    "pressure_forecast.json",
    "pressure_drivers.json",
    "respiratory_surge.json",
    "smoke_weather_travel.json",
    "travel_access_friction.json",
    "scenario_catalog.json",
    "scenario_results_grid.json",
    "simulation_baseline.json",
    "simulation_scenario_examples.json",
    "synthetic_future_state.json",
    "synthetic_digital_twin_state.json",
    "model_validation_summary.json",
    "public_lineage_manifest.json",
    "executive_demo_copy.json",
    "governance_boundary.json",
    "research_to_capability_map.json",
]


def export_public_showcase_artifacts(out: str | Path, mode: str = "public_demo", seed: int = 20260601) -> list[Path]:
    """Generate all public-safe artifacts and return written paths."""

    np.random.seed(seed)
    config = KernelConfig(data_mode=mode)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_synthetic_data(config.synthetic_data_dir)
    ensure_public_open_data(config.open_data_dir)

    local_backend = LocalBackend(config.synthetic_data_dir)
    visits = local_backend.load_ed_visits(VisitFilters())
    active = local_backend.load_current_active_visits(VisitFilters())
    registry = load_data_source_registry()
    hub = OpenDataHub(registry, config.open_data_dir)
    public_data = hub.datasets()
    facility = config.default_facility

    forecast = forecast_external_pressure(public_data, facility, horizon_hours=96)
    feature_frame = build_public_feature_matrix(public_data, facility)
    scenario = run_combined_public_scenario(
        visits,
        public_data,
        facility,
        72,
        ScenarioShockConfig(respiratory_surge=1.45, smoke_event=0.35, traffic_disruption=0.25, synthetic_capacity_constraint=0.35),
    )
    simulation = run_enhanced_simulation_summary(
        visits,
        ScenarioConfig(facility=facility, arrival_surge_multiplier=1.18, fast_track_enabled=True, boarding_reduction=0.15, replications=20),
    )
    cockpit = executive_pressure_cockpit(visits, active, public_data, facility)
    refresh = statuses_to_frame(hub.status_rows())
    registry_frame = registry_to_frame(registry)
    facilities = public_data.get("facility_reference", pd.DataFrame()).copy()
    pressure = cockpit["site_ranking"] if isinstance(cockpit.get("site_ranking"), pd.DataFrame) else pd.DataFrame()
    sites = facilities.merge(pressure[["facility", "public_pressure_index", "estimated_wait_mins"]], on="facility", how="left") if not pressure.empty else facilities
    zones = sites.groupby("zone", as_index=False).agg(
        sites=("facility", "nunique"),
        public_pressure_index=("public_pressure_index", "mean"),
        pediatric_sites=("pediatric_site", "sum"),
    )

    artifacts: dict[str, Any] = {
        "sites.json": _records(sites),
        "zones.json": _records(zones),
        "capability_map.json": _capability_ladder(),
        "snowflake_portability_map.json": _snowflake_portability_map(),
        "open_data_registry.json": _records(registry_frame),
        "open_data_refresh_status.json": _records(refresh),
        "pressure_forecast.json": _records(forecast.hourly.head(96)),
        "pressure_drivers.json": _records(forecast.drivers),
        "respiratory_surge.json": _records(public_data.get("respiratory_surveillance", pd.DataFrame()).tail(72)),
        "smoke_weather_travel.json": _smoke_weather_travel(public_data),
        "travel_access_friction.json": _records(public_data.get("travel_friction", pd.DataFrame()).head(120)),
        "scenario_catalog.json": _scenario_catalog(),
        "scenario_results_grid.json": _scenario_payload(scenario),
        "simulation_baseline.json": _simulation_payload(simulation),
        "simulation_scenario_examples.json": _records(simulation["ranking"]) if isinstance(simulation.get("ranking"), pd.DataFrame) else [],
        "synthetic_future_state.json": _future_state_graph(),
        "synthetic_digital_twin_state.json": _digital_twin_state(cockpit, simulation),
        "model_validation_summary.json": _model_validation_payload(forecast, feature_frame),
        "public_lineage_manifest.json": _lineage_manifest(refresh),
        "executive_demo_copy.json": _executive_copy(cockpit),
        "governance_boundary.json": _governance_boundary(),
        "research_to_capability_map.json": _records(research_capability_map()),
    }

    written: list[Path] = []
    for name in ARTIFACT_NAMES:
        payload = _public_safe(artifacts[name])
        artifact = PublicArtifact(
            generated_at=datetime.now(timezone.utc).isoformat(),
            data_mode=mode,
            source_categories=_source_categories_for(name),
            lineage=_lineage_for_artifact(name, refresh),
            synthetic_flag=True,
            caveats=_artifact_caveats(name),
            payload=payload,
        )
        data = _public_safe(artifact.model_dump(mode="json"))
        if public_payload_has_phi_like_values(data):
            raise ValueError(f"Public artifact {name} appears to contain PHI-like content.")
        path = out_dir / name
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(path)
    return written


def _public_safe(value: Any) -> Any:
    """Redact internal identifier column names from public artifacts."""

    replacements = {
        "PATIENT_CHART": "secure chart identifier",
        "PATIENT_PHN": "secure provincial identifier",
        "PATIENT_ULI": "secure provincial identifier",
        "PATIENT_ID": "secure patient identifier",
        "PATIENT_BIRTHDATE": "secure date of birth",
        "PAT_MRN_ID": "secure chart identifier",
        "MRN": "secure chart identifier",
        "PHN": "secure provincial identifier",
        "ULI": "secure provincial identifier",
    }
    if isinstance(value, dict):
        return {str(_public_safe(key)): _public_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_public_safe(item) for item in value]
    if isinstance(value, str):
        out = value
        for old, new in replacements.items():
            out = out.replace(old, new)
        return out
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[column]):
            clean[column] = clean[column].dt.strftime("%Y-%m-%dT%H:%M:%S")
    clean = clean.replace({np.nan: None})
    return clean.to_dict(orient="records")


def _source_categories_for(name: str) -> list[str]:
    if "simulation" in name or "digital_twin" in name or "future_state" in name:
        return ["SYNTHETIC_DATA", "MODEL_OUTPUT"]
    if "scenario" in name or "forecast" in name or "driver" in name or "validation" in name:
        return ["HYBRID_OPEN_SYNTHETIC", "MODEL_OUTPUT"]
    if "snowflake" in name:
        return ["SECURE_INTERNAL_READY_SCHEMA", "SECURE_INTERNAL_PLACEHOLDER"]
    return ["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"]


def _lineage_for_artifact(name: str, refresh: pd.DataFrame) -> list[dict[str, Any]]:
    if refresh.empty:
        return []
    rows = refresh[["source_id", "category", "freshness_state", "quality_score", "activation_status"]].copy()
    if "respiratory" in name:
        rows = rows[rows["source_id"].str.contains("respiratory|wait_times", case=False, regex=True)]
    elif "travel" in name:
        rows = rows[rows["source_id"].str.contains("511|traffic|wait_times", case=False, regex=True)]
    elif "snowflake" in name:
        rows = rows[rows["category"].str.contains("SECURE_INTERNAL", regex=False)]
    return _records(rows.head(12))


def _artifact_caveats(name: str) -> list[str]:
    base = [
        "Public artifact: open-data-shaped and synthetic demonstration values only.",
        "No patient-level data, secure AHS data, or private endpoints are included.",
    ]
    if "simulation" in name or "digital_twin" in name or "future_state" in name:
        base.append("Synthetic future-state demonstration; not operational truth.")
    if "forecast" in name or "scenario" in name:
        base.append("Forecast/scenario output is explanatory decision support and requires internal validation.")
    return base


def _capability_ladder() -> list[dict[str, Any]]:
    return [
        {"tier": tier, "summary": summary, "public_boundary": boundary}
        for tier, summary, boundary in [
            ("public now", "Open/public pressure signals and synthetic fallback cache.", "safe for public showcase"),
            ("synthetic public demo", "Demonstration flow state and digital-twin concepts.", "clearly labelled synthetic"),
            ("Snowflake day-one ready", "TB_ED_VISITS constrained features and semantic-view contracts.", "requires governed AHS environment"),
            ("early feasible", "Bed board, staffing, diagnostics, consult, EMS, transfer feeds.", "requires source curation and RBAC"),
            ("aspirational future-state", "Near-real-time provincial digital twin and action orchestration.", "requires validation and governance"),
        ]
    ]


def _snowflake_portability_map() -> list[dict[str, str]]:
    return [
        {"component": "Capability kernel", "local_mode": "Python package over synthetic/open cache", "snowflake_mode": "Snowpark-compatible package behind Streamlit in Snowflake"},
        {"component": "TB_ED_VISITS", "local_mode": "synthetic contract-shaped CSV", "snowflake_mode": "curated internal table with default filters"},
        {"component": "Chart review", "local_mode": "mock synthetic summaries", "snowflake_mode": "semantic views with governed identifier mapping"},
        {"component": "Open data", "local_mode": "cached/synthetic public artifacts", "snowflake_mode": "OPEN_DATA schema with tasks and refresh log"},
        {"component": "Model layer", "local_mode": "interpretable Python only", "snowflake_mode": "Snowpark/Cortex/OpenAI interface only when approved"},
    ]


def _smoke_weather_travel(public_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    env = public_data.get("environmental_stress", pd.DataFrame())
    travel = public_data.get("travel_friction", pd.DataFrame())
    return {
        "environmental": _records(env.head(120)),
        "travel": _records(travel.head(120)),
        "story": "Smoke, heat/cold, weather alerts, road disruption, and event access friction can cluster front-door pressure.",
    }


def _scenario_catalog() -> list[dict[str, Any]]:
    levers = [
        "respiratory surge",
        "school reopening",
        "smoke event",
        "heat wave",
        "snowstorm",
        "traffic disruption",
        "large public event",
        "boarding reduction",
        "rapid assessment",
        "fast-track",
        "consult turnaround",
        "diagnostic turnaround",
    ]
    return [{"lever": lever, "data_lineage": "public/synthetic demo", "requires_internal_validation": True} for lever in levers]


def _scenario_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "forecast": _records(scenario.get("forecast", pd.DataFrame()).head(96) if isinstance(scenario.get("forecast"), pd.DataFrame) else pd.DataFrame()),
        "impact": _records(scenario.get("impact", pd.DataFrame()) if isinstance(scenario.get("impact"), pd.DataFrame) else pd.DataFrame()),
        "affected_stages": _records(scenario.get("affected_stages", pd.DataFrame()) if isinstance(scenario.get("affected_stages"), pd.DataFrame) else pd.DataFrame()),
        "ranking": _records(scenario.get("ranking", pd.DataFrame()) if isinstance(scenario.get("ranking"), pd.DataFrame) else pd.DataFrame()),
        "huddle": scenario.get("huddle", []),
    }


def _simulation_payload(simulation: dict[str, Any]) -> dict[str, Any]:
    return {
        "uncertainty": _records(simulation.get("uncertainty", pd.DataFrame()) if isinstance(simulation.get("uncertainty"), pd.DataFrame) else pd.DataFrame()),
        "utilization": _records(simulation.get("utilization", pd.DataFrame()) if isinstance(simulation.get("utilization"), pd.DataFrame) else pd.DataFrame()),
        "migration": _records(simulation.get("migration", pd.DataFrame()) if isinstance(simulation.get("migration"), pd.DataFrame) else pd.DataFrame()),
        "huddle": simulation.get("huddle", []),
    }


def _future_state_graph() -> dict[str, Any]:
    nodes = [
        "community demand",
        "arrival",
        "triage",
        "waiting room",
        "rooming",
        "physician assessment",
        "diagnostics",
        "consults",
        "disposition",
        "boarding",
        "inpatient bed",
        "discharge or transfer",
    ]
    edges = [{"from": nodes[i], "to": nodes[i + 1], "pressure_transfer": round(0.35 + i * 0.04, 2)} for i in range(len(nodes) - 1)]
    return {"title": "Synthetic future-state flow canvas", "nodes": nodes, "edges": edges, "label": "Synthetic future-state demonstration"}


def _digital_twin_state(cockpit: dict[str, Any], simulation: dict[str, Any]) -> dict[str, Any]:
    metrics = cockpit.get("metrics", pd.DataFrame())
    utilization = simulation.get("utilization", pd.DataFrame())
    return {
        "label": "Synthetic future-state demonstration",
        "pressure_cards": _records(metrics if isinstance(metrics, pd.DataFrame) else pd.DataFrame()),
        "resource_utilization": _records(utilization if isinstance(utilization, pd.DataFrame) else pd.DataFrame()),
    }


def _model_validation_payload(forecast: Any, feature_frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "holdout_validation": _records(forecast.validation),
        "model_registry": _records(forecast.registry),
        "rolling_origin": _records(rolling_origin_backtest(feature_frame).head(40)),
        "validation_required_in_snowflake": [
            "facility-level calibration",
            "holdout by date and season",
            "admission/LWBS calibration",
            "simulation replay against observed queues and LOS",
        ],
    }


def _lineage_manifest(refresh: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_categories": SOURCE_CATEGORIES,
        "refresh_status": _records(refresh),
        "capability_tiers": CAPABILITY_TIERS,
    }


def _executive_copy(cockpit: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": PUBLIC_SHOWCASE_TITLE,
        "subtitle": "From public pressure signals to secure operational intelligence",
        "watchpoints": cockpit.get("watchpoints", []),
        "levers": cockpit.get("levers", []),
        "why_pressure_moved": cockpit.get("why_pressure_moved", ""),
        "boundary": "Public showcase uses open-data-shaped and synthetic artifacts only.",
    }


def _governance_boundary() -> dict[str, Any]:
    interpretation = ActionInterpretation(
        what_changed="The public showcase separates open/synthetic demonstration from secure internal action intelligence.",
        why_it_changed="Colleague-portable AHS work needs a protected Streamlit/Snowflake path and a separate public narrative.",
        confidence="high on architecture boundary; model confidence requires internal validation",
        improved=["clearer public/internal boundary", "reusable kernel", "Snowflake activation map"],
        worsened=["public showcase cannot display real operational truth"],
        bottleneck_moved_to="governed internal data activation",
        watch_points=["lineage", "RBAC", "model validation", "identifier handling"],
        operational_levers=["activate TB_ED_VISITS features", "curate secure operational feeds", "validate before pilot"],
        validation_needed=["Snowflake holdout validation", "facility calibration", "privacy review"],
        limitations=["synthetic values", "no real-time internal feeds", "no clinical automation"],
        huddle_brief=[
            "Use the showcase for vision, not operations.",
            "Use Action Intelligence inside governed Snowflake for internal testing.",
            "Keep identifiers and chart context inside secure views.",
            "Validate models before workflow change.",
            "Human leaders remain accountable for decisions.",
        ],
    )
    return interpretation.model_dump(mode="json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export public-safe ED Flow showcase artifacts.")
    parser.add_argument("--out", required=True, help="Output directory for JSON artifacts.")
    parser.add_argument("--mode", default="public_demo", help="Artifact data mode label.")
    parser.add_argument("--seed", type=int, default=20260601, help="Deterministic export seed.")
    args = parser.parse_args()
    written = export_public_showcase_artifacts(args.out, args.mode, args.seed)
    print(f"Exported {len(written)} public-safe artifacts to {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()

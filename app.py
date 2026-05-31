"""Streamlit application for AHS ED Flow Intelligence Prototype vNext."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ed_flow.ai_layer import get_model_client
from ed_flow.chart_review import summarize_chart_context
from ed_flow.config import AppConfig, get_config
from ed_flow.data_contracts import (
    CONSTRAINED_ANALYSIS_COLUMNS,
    ScenarioConfig,
    VisitFilters,
    constrained_projection,
)
from ed_flow.event_log import construct_event_log, observed_concurrency, reconstruct_stage_intervals
from ed_flow.feature_engineering import (
    add_flow_features,
    arrival_patterns,
    estimate_baseline_parameters,
    route_probabilities,
    stage_duration_distributions,
)
from ed_flow.governance import governance_summary, holdout_split_by_date
from ed_flow.local_backend import LocalBackend
from ed_flow.metrics import (
    bottleneck_summary,
    calculate_data_quality,
    current_state_metrics,
    los_summary_by_facility,
    validation_metric_summary,
)
from ed_flow.optimization import greedy_bed_placement_optimizer, rank_interventions, staffing_sensitivity
from ed_flow.scenario_models import compare_scenarios, practical_interpretation
from ed_flow.simulation_engine import run_simulation, summarize_with_uncertainty
from ed_flow.snowflake_backend import (
    build_active_visits_sql,
    build_chart_context_sql,
    build_ed_visits_sql,
    build_recent_ed_visits_sql,
)
from ed_flow.synthetic_data import ensure_synthetic_data
from ed_flow.visualizations import duration_distribution, line_chart, metric_bar, uncertainty_interval_chart
from ed_flow_intelligence.constants import PEDIATRIC_AGE_GROUPS, SECURE_INTERNAL_DATASETS, V2_TAB_NAMES
from ed_flow_intelligence.advanced_scenarios import ScenarioShockConfig, run_combined_public_scenario
from ed_flow_intelligence.data_sources.public_adapters import OpenDataHub
from ed_flow_intelligence.data_sources.registry import load_data_source_registry, registry_to_frame
from ed_flow_intelligence.data_sources.synthetic_open_data import OPEN_DATA_DIR, ensure_public_open_data
from ed_flow_intelligence.forecasting import hybrid_arrival_forecast, likely_binding_constraints, public_pressure_index
from ed_flow_intelligence.lineage import category_legend_frame, lineage_badge, statuses_to_frame
from ed_flow_intelligence.modeling import build_public_feature_matrix, forecast_external_pressure, forecast_internal_targets, rolling_origin_backtest
from ed_flow_intelligence.operational_intelligence import executive_pressure_cockpit, research_capability_map
from ed_flow_intelligence.quality import constrained_boundary_check, public_data_quality_summary
from ed_flow_intelligence.simulation_vnext import lwbs_hazard, run_enhanced_simulation_summary
from ed_flow_intelligence.snowflake_sql import available_sql_templates, load_sql_template


LINEAGE_STATUS_DISPLAY_COLUMNS = [
    "source_id",
    "display_name",
    "category",
    "activation_status",
    "freshness_state",
    "row_count",
    "quality_score",
    "expected_refresh_minutes",
    "max_source_timestamp",
    "grain",
    "geography",
    "snowflake_target",
    "downstream_usage",
    "pii_risk",
    "internal_activation_need",
    "blocking_issue",
    "fallback_reason",
]


def configure_page() -> None:
    """Configure Streamlit and shared styling."""

    st.set_page_config(
        page_title="AHS ED Flow Intelligence Prototype vNext",
        page_icon="AHS",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
          --ed-teal: #2f6f73;
          --ed-blue: #335c81;
          --ed-coral: #c95746;
          --ed-amber: #d99b2b;
          --ed-ink: #1f2933;
          --ed-muted: #607080;
          --ed-band: #f5f7f8;
          --ed-line: #d8e1e5;
        }
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1500px;}
        h1, h2, h3 {letter-spacing: 0;}
        .metric-card {
            border: 1px solid var(--ed-line);
            border-left: 5px solid var(--ed-teal);
            border-radius: 8px;
            padding: 0.72rem 0.85rem;
            background: #ffffff;
            min-height: 90px;
        }
        .metric-label {font-size: 0.76rem; color: var(--ed-muted); text-transform: uppercase;}
        .metric-value {font-size: 1.42rem; font-weight: 720; color: var(--ed-ink);}
        .method-note {
            border: 1px solid var(--ed-line);
            border-radius: 8px;
            background: var(--ed-band);
            padding: 0.68rem 0.82rem;
            color: var(--ed-ink);
            font-size: 0.91rem;
        }
        .warning-note {
            border: 1px solid #efc36a;
            border-left: 5px solid var(--ed-amber);
            border-radius: 8px;
            background: #fff8e8;
            padding: 0.72rem 0.82rem;
            color: #4d3b13;
        }
        .patient-card {
            border: 1px solid var(--ed-line);
            border-left: 5px solid var(--ed-blue);
            border-radius: 8px;
            padding: 0.9rem;
            margin-bottom: 0.75rem;
            background: #ffffff;
        }
        .small-muted {color: var(--ed-muted); font-size: 0.85rem;}
        div[data-testid="stMetricValue"] {font-size: 1.35rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_backend(data_dir: str) -> LocalBackend:
    """Return the synthetic local backend."""

    ensure_synthetic_data(Path(data_dir))
    return LocalBackend(Path(data_dir))


@st.cache_data(show_spinner=False)
def load_core_data(data_dir: str) -> dict[str, pd.DataFrame]:
    """Load synthetic internal-ready data."""

    backend = LocalBackend(Path(data_dir))
    all_visits = backend.load_ed_visits(VisitFilters(include_invalid_los=True, include_scheduled=True))
    visits = backend.load_ed_visits(VisitFilters())
    return {
        "all_visits": all_visits,
        "visits": visits,
        "active": backend.load_current_active_visits(VisitFilters()),
        "expanded_events": backend.load_expanded_flow_events(),
        "capacity": backend.load_beds_staffing_diagnostics(),
    }


@st.cache_data(show_spinner=False)
def load_open_bundle() -> dict[str, object]:
    """Load public/open source metadata and synthetic fallback cache."""

    ensure_public_open_data(OPEN_DATA_DIR)
    registry = load_data_source_registry()
    hub = OpenDataHub(registry, OPEN_DATA_DIR)
    return {
        "registry": registry_to_frame(registry),
        "public_data": hub.datasets(),
        "refresh_status": statuses_to_frame(hub.status_rows()),
    }


def sidebar_controls(config: AppConfig, visits: pd.DataFrame) -> tuple[str, bool, int]:
    """Global controls."""

    st.sidebar.title("ED Flow Intelligence vNext")
    st.sidebar.caption("Synthetic local mode. Public sources use synthetic fallback cache. No PHI.")
    facilities = sorted(visits["INSTITUTION_NAME"].dropna().unique().tolist())
    default_index = facilities.index(config.default_facility) if config.default_facility in facilities else 0
    facility = st.sidebar.selectbox("Facility", facilities, index=default_index)
    pediatric_only = st.sidebar.toggle("Pediatric focus", value=config.default_pediatric_only)
    horizon_hours = st.sidebar.slider("Planning horizon", min_value=6, max_value=96, value=24, step=6)
    if st.sidebar.button("Refresh synthetic public cache"):
        ensure_public_open_data(OPEN_DATA_DIR, force=True)
        load_open_bundle.clear()
        st.rerun()
    st.sidebar.markdown(
        "<div class='method-note'>Decision support only. The app estimates operational effects; it does not automate clinical judgement.</div>",
        unsafe_allow_html=True,
    )
    return facility, pediatric_only, horizon_hours


def filtered_view(
    visits: pd.DataFrame,
    active: pd.DataFrame,
    facility: str,
    pediatric_only: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply shared facility and population filters."""

    visit_view = visits[visits["INSTITUTION_NAME"] == facility].copy()
    active_view = active[active["facility"] == facility].copy() if "facility" in active.columns else pd.DataFrame()
    if pediatric_only:
        visit_view = visit_view[visit_view["PATIENT_AGE_GROUP"].isin(PEDIATRIC_AGE_GROUPS)]
        if "age_group" in active_view.columns:
            active_view = active_view[active_view["age_group"].isin(PEDIATRIC_AGE_GROUPS)]
    return visit_view.reset_index(drop=True), active_view.reset_index(drop=True)


def pct(value: float | int) -> str:
    """Format a probability."""

    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return "n/a"


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    """Render a compact metric card."""

    tooltip = f" title='{help_text}'" if help_text else ""
    st.markdown(
        f"<div class='metric-card'{tooltip}><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def operational_metric_card(row: pd.Series) -> None:
    """Render an executive metric card with trend, confidence, lineage, and interpretation."""

    badge = lineage_badge(str(row.get("lineage", "SYNTHETIC_DATA")))
    trend = str(row.get("trend", "flat"))
    confidence = str(row.get("confidence", "moderate"))
    interpretation = str(row.get("interpretation", ""))
    st.markdown(
        f"""
        <div class='metric-card'>
          <div class='metric-label'>{row.get('label', '')}</div>
          <div class='metric-value'>{row.get('display_value', row.get('value', 'n/a'))}</div>
          <div class='small-muted'>Trend: <b>{trend}</b> | Confidence: <b>{confidence}</b></div>
          <div style='margin-top:0.35rem'>{badge}</div>
          <div class='small-muted' style='margin-top:0.35rem'>{interpretation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def huddle_brief_component(lines: list[str]) -> None:
    """Render a compact deterministic huddle brief."""

    if not lines:
        return
    st.markdown("**Capacity Huddle Brief**")
    for line in lines[:5]:
        st.write(f"- {line}")


def lineage_status_display_frame(statuses: object) -> pd.DataFrame:
    """Return a cache-tolerant lineage dataframe for display."""

    if not isinstance(statuses, pd.DataFrame):
        return pd.DataFrame(columns=LINEAGE_STATUS_DISPLAY_COLUMNS)
    return statuses.reindex(columns=LINEAGE_STATUS_DISPLAY_COLUMNS, fill_value="")


def lineage_strip(categories: list[str]) -> None:
    """Render lineage badges."""

    badges = " ".join(lineage_badge(category) for category in categories)
    st.markdown(badges, unsafe_allow_html=True)


def method_note(text: str) -> None:
    st.markdown(f"<div class='method-note'>{text}</div>", unsafe_allow_html=True)


def warning_note(text: str) -> None:
    st.markdown(f"<div class='warning-note'>{text}</div>", unsafe_allow_html=True)


def latest_open_frame(public_data: dict[str, pd.DataFrame], dataset: str, timestamp_col: str) -> pd.DataFrame:
    frame = public_data.get(dataset, pd.DataFrame())
    if frame.empty or timestamp_col not in frame or "facility" not in frame:
        return frame
    return frame.sort_values(timestamp_col).groupby("facility", as_index=False).tail(1)


def executive_tab(
    visits: pd.DataFrame,
    active: pd.DataFrame,
    all_visits: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
    pediatric_only: bool,
    horizon_hours: int,
) -> None:
    st.subheader("Executive Command Centre")
    lineage_strip(["SYNTHETIC_DATA", "HYBRID_OPEN_SYNTHETIC", "SECURE_INTERNAL_READY_SCHEMA"])
    visit_view, active_view = filtered_view(visits, active, facility, pediatric_only)
    quality = calculate_data_quality(all_visits[all_visits["INSTITUTION_NAME"] == facility])
    freshness = quality.max_row_update_datetime.isoformat(timespec="minutes") if quality.max_row_update_datetime else "unknown"
    warning_note(
        f"Data quality and freshness: {quality.row_count} synthetic TB_ED_VISITS-shaped rows loaded for {facility}; "
        f"latest synthetic row update {freshness}. {' '.join(quality.warnings[:2])}"
    )
    cockpit = executive_pressure_cockpit(visits, active, public_data, facility)
    st.markdown("**Alberta Pressure Cockpit**")
    cockpit_metrics = cockpit["metrics"]
    for idx in range(0, len(cockpit_metrics), 4):
        cols = st.columns(4)
        for col, (_, row) in zip(cols, cockpit_metrics.iloc[idx : idx + 4].iterrows()):
            with col:
                operational_metric_card(row)

    c_rank, c_changed, c_action = st.columns([1.05, 1, 1.05])
    with c_rank:
        st.markdown("**Site and zone pressure ranking**")
        site_cols = ["facility", "zone", "public_pressure_index", "pressure_band", "estimated_wait_mins"]
        st.dataframe(cockpit["site_ranking"][site_cols].head(7), width="stretch", hide_index=True)
        st.dataframe(cockpit["zone_ranking"], width="stretch", hide_index=True)
    with c_changed:
        st.markdown("**What changed since last refresh**")
        changed = cockpit["what_changed"]
        if isinstance(changed, pd.DataFrame) and not changed.empty:
            st.dataframe(changed, width="stretch", hide_index=True)
        else:
            st.write("No change signal available in the current fallback cache.")
        st.markdown("**Why pressure moved**")
        st.write(cockpit["why_pressure_moved"])
    with c_action:
        st.markdown("**Top watch-points**")
        for item in cockpit["watchpoints"]:
            st.write(f"- {item}")
        st.markdown("**Operational levers to consider**")
        for item in cockpit["levers"]:
            st.write(f"- {item}")
        method_note("These are operational questions and levers, not clinical orders or automated recommendations.")

    with st.expander("Research-to-Capability Map", expanded=False):
        st.dataframe(research_capability_map(), width="stretch", hide_index=True)

    pressure = public_pressure_index(public_data)
    site_pressure = pressure[pressure["facility"] == facility] if not pressure.empty else pd.DataFrame()
    pressure_value = float(site_pressure["public_pressure_index"].iloc[0]) if not site_pressure.empty else 0.0
    pressure_band = str(site_pressure["pressure_band"].iloc[0]) if not site_pressure.empty else "Unknown"

    metrics = current_state_metrics(active_view, visit_view)
    metric_items = [
        ("Arrivals", f"{metrics['arrivals']:,}", "Selected synthetic historical arrivals after default rules."),
        ("Waiting to triage", str(metrics["waiting_to_triage"]), None),
        ("Triaged waiting", str(metrics["triaged_waiting"]), None),
        ("Roomed not yet seen", str(metrics["roomed_not_seen"]), None),
        ("Waiting for PIA", str(metrics["waiting_for_physician_initial_assessment"]), "PIA means physician initial assessment."),
        ("Consult delay", str(metrics["consult_delay"]), None),
        ("DTA boarders", str(metrics["decision_to_admit_boarders"]), "Decision-to-admit patients still occupying ED capacity."),
        ("EMS offload delay", str(metrics["ems_offload_delay"]), None),
        ("Admitted within 8h", pct(metrics["admitted_within_8_hours"]), None),
        ("Discharged within 4h", pct(metrics["discharged_within_4_hours"]), None),
        ("LWBS risk", pct(metrics["lwbs_risk"]), "Mean synthetic waiting-room LWBS risk."),
        ("Median / p90 LOS", f"{metrics['median_ed_los']:.1f} / {metrics['p90_ed_los']:.1f}h", None),
        ("Public pressure", f"{pressure_value:.2f}", pressure_band),
    ]
    for idx in range(0, len(metric_items), 4):
        cols = st.columns(4)
        for col, item in zip(cols, metric_items[idx : idx + 4]):
            with col:
                metric_card(*item)

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("**Current Simulated ED State**")
        if active_view.empty:
            st.info("No active synthetic patients match this filter.")
        else:
            stage_counts = active_view["current_stage"].value_counts().rename_axis("stage").reset_index(name="patients")
            st.plotly_chart(metric_bar(stage_counts, "stage", "patients", title="Active patients by stage"), width="stretch")
    with right:
        st.markdown("**Bottleneck Summary**")
        st.dataframe(bottleneck_summary(active_view, visit_view), width="stretch", hide_index=True)

    forecast = hybrid_arrival_forecast(visit_view, public_data, facility, horizon_hours)
    st.plotly_chart(line_chart(forecast, "hour_ahead", "expected_arrivals", title="Hybrid empirical + public pressure arrival forecast"), width="stretch")
    method_note("Current-state counts come from the synthetic waiting-room registry. Public pressure combines synthetic fallback wait-time, respiratory, weather/AQHI, wildfire/smoke, travel, and calendar features.")


def public_pressure_tab(public_data: dict[str, pd.DataFrame], facility: str) -> None:
    st.subheader("Alberta Public Pressure Map & Site Explorer")
    lineage_strip(["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"])
    pressure = public_pressure_index(public_data)
    if pressure.empty:
        st.info("No synthetic public pressure data loaded.")
        return
    map_kwargs = {
        "data_frame": pressure,
        "lat": "latitude",
        "lon": "longitude",
        "color": "pressure_band",
        "size": "public_pressure_index",
        "hover_name": "facility",
        "hover_data": ["zone", "estimated_wait_mins", "aqhi", "travel_friction_index", "pediatric_pressure_index"],
        "zoom": 4.2,
        "height": 430,
        "title": "Synthetic public pressure by ED/UCC/AACC site",
    }
    if hasattr(px, "scatter_map"):
        map_fig = px.scatter_map(**map_kwargs, map_style="open-street-map")
    else:
        map_fig = px.scatter_mapbox(**map_kwargs, mapbox_style="open-street-map")
    st.plotly_chart(map_fig, width="stretch")
    selected = pressure[pressure["facility"] == facility]
    cols = st.columns(4)
    if not selected.empty:
        row = selected.iloc[0]
        cols[0].metric("Public pressure index", f"{row['public_pressure_index']:.2f}", row["pressure_band"])
        cols[1].metric("Posted wait fallback", f"{row['estimated_wait_mins']:.0f} min")
        cols[2].metric("AQHI fallback", f"{row['aqhi']:.0f}")
        cols[3].metric("Travel friction", f"{row['travel_friction_index']:.2f}")
    st.dataframe(pressure, width="stretch", hide_index=True)
    method_note("The public map is site-level and non-identifying. It is suitable for public-context pressure modelling, not patient-level clinical decision-making.")


def public_wait_times_tab(public_data: dict[str, pd.DataFrame]) -> None:
    st.subheader("Public ED Wait Times Monitor")
    lineage_strip(["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"])
    wait = public_data.get("public_wait_times", pd.DataFrame())
    historical = public_data.get("historical_public_ed_metrics", pd.DataFrame())
    latest = latest_open_frame(public_data, "public_wait_times", "posted_timestamp")
    if latest.empty:
        st.info("No public wait-time fallback cache available.")
        return
    cols = st.columns(3)
    cols[0].metric("Tracked public sites", latest["facility"].nunique())
    cols[1].metric("Median posted wait fallback", f"{latest['estimated_wait_mins'].median():.0f} min")
    cols[2].metric("Max posted wait fallback", f"{latest['estimated_wait_mins'].max():.0f} min")
    st.dataframe(latest.sort_values("estimated_wait_mins", ascending=False), width="stretch", hide_index=True)
    st.plotly_chart(line_chart(wait, "posted_timestamp", "estimated_wait_mins", color="facility", title="48-hour posted wait-time fallback trend"), width="stretch")
    if not historical.empty:
        st.plotly_chart(
            line_chart(historical, "week_start", "discharged_within_4h_pct", color="facility", title="Public aggregate discharged-within-4h fallback"),
            width="stretch",
        )
    method_note("Future Snowflake jobs should retain official-source timestamps, scrape/API method, refresh status, and licensing metadata. Local numbers are synthetic fallback values.")


def respiratory_tab(public_data: dict[str, pd.DataFrame], facility: str) -> None:
    st.subheader("Pediatric Respiratory Surge")
    lineage_strip(["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"])
    respiratory = public_data.get("respiratory_surveillance", pd.DataFrame())
    facilities = public_data.get("facility_reference", pd.DataFrame())
    zone = facilities.loc[facilities["facility"] == facility, "zone"].iloc[0] if not facilities.empty and facility in facilities["facility"].values else "Edmonton"
    zone_view = respiratory[respiratory["zone"] == zone].copy()
    latest = zone_view.sort_values("week_start").groupby("pathogen", as_index=False).tail(1)
    cols = st.columns(4)
    for col, pathogen in zip(cols, ["RSV", "Influenza", "COVID-19", "Other respiratory"]):
        row = latest[latest["pathogen"] == pathogen]
        value = float(row["test_positivity"].iloc[0]) if not row.empty else 0
        col.metric(pathogen, pct(value), "synthetic positivity")
    st.plotly_chart(line_chart(zone_view, "week_start", "test_positivity", color="pathogen", title=f"{zone} respiratory positivity fallback"), width="stretch")
    st.dataframe(latest, width="stretch", hide_index=True)
    st.markdown("**Respiratory Scenario Controls**")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    rsv_accel = c1.slider("RSV acceleration", 0.0, 2.0, 0.4, 0.1, key="resp_rsv_accel")
    flu_accel = c2.slider("Influenza acceleration", 0.0, 2.0, 0.3, 0.1, key="resp_flu_accel")
    covid_wave = c3.slider("COVID wave", 0.0, 2.0, 0.2, 0.1, key="resp_covid_wave")
    school_reopen = c4.toggle("School reopening", value=False, key="resp_school_reopen")
    measles_cluster = c5.toggle("Measles exposure cluster", value=False, key="resp_measles_cluster")
    smoke_overlay = c6.toggle("Smoke overlay", value=False, key="resp_smoke_overlay")
    cold_snap = st.toggle("Cold snap overlay", value=False, key="resp_cold_snap_overlay")
    base_index = float(zone_view.sort_values("week_start").tail(8)["pediatric_pressure_index"].mean()) if not zone_view.empty else 0.0
    scenario_index = min(
        1.0,
        base_index
        + 0.09 * rsv_accel
        + 0.07 * flu_accel
        + 0.05 * covid_wave
        + 0.08 * school_reopen
        + 0.06 * measles_cluster
        + 0.07 * smoke_overlay
        + 0.05 * cold_snap,
    )
    wastewater_proxy = min(1.0, base_index * 1.15 + 0.06 * covid_wave + 0.04 * flu_accel)
    impact = pd.DataFrame(
        [
            ("respiratory_composite_index", base_index, scenario_index, "HYBRID_OPEN_SYNTHETIC"),
            ("wastewater_trend_proxy", base_index * 0.9, wastewater_proxy, "HYBRID_OPEN_SYNTHETIC"),
            ("expected_pediatric_arrival_lift", 0.0, (scenario_index - base_index) * 0.42, "MODEL_OUTPUT"),
            ("expected_acuity_shift_ctas_2_3", 0.0, (scenario_index - base_index) * 0.18, "MODEL_OUTPUT"),
        ],
        columns=["signal", "baseline", "scenario", "lineage"],
    )
    impact["change"] = impact["scenario"] - impact["baseline"]
    st.dataframe(impact, width="stretch", hide_index=True)
    huddle_brief_component(
        [
            f"Respiratory composite changes from {base_index:.2f} to {scenario_index:.2f}.",
            "Likely arrival pressure rises first at pediatric sites and respiratory complaint streams.",
            "Watch CTAS mix, rooming, isolation/cohort capacity, and reassessment intervals.",
            "Consider respiratory cohort pathway, fast-track eligibility, and diagnostic/consult pre-brief.",
            "Internal data needed: real respiratory complaint volumes, CTAS mix, diagnostics, staffing, and room isolation flags.",
        ]
    )
    method_note("Respiratory features are public aggregate context. They can inform pediatric surge preparation but cannot identify individual patients or replace local clinical surveillance.")


def environmental_tab(public_data: dict[str, pd.DataFrame], facility: str) -> None:
    st.subheader("Smoke, Heat, Weather & Air Quality Stress")
    lineage_strip(["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"])
    env = public_data.get("environmental_stress", pd.DataFrame())
    site = env[env["facility"] == facility].copy()
    if site.empty:
        st.info("No environmental stress fallback data available.")
        return
    latest = site.sort_values("timestamp").tail(1).iloc[0]
    cols = st.columns(5)
    cols[0].metric("Temperature", f"{latest['temperature_c']:.1f} C")
    cols[1].metric("Humidex", f"{latest['humidex']:.1f}")
    cols[2].metric("AQHI", f"{latest['aqhi']:.0f}")
    cols[3].metric("Smoke risk", f"{latest['wildfire_smoke_risk']:.2f}")
    cols[4].metric("Stress index", f"{latest['environmental_stress_index']:.2f}")
    st.plotly_chart(line_chart(site, "timestamp", "environmental_stress_index", title=f"{facility} environmental stress index"), width="stretch")
    st.dataframe(site.head(96), width="stretch", hide_index=True, height=320)
    st.markdown("**Scenario Injection**")
    e1, e2, e3, e4, e5 = st.columns(5)
    aqhi_worsens = e1.slider("AQHI worsens", 0, 5, 2, 1, key="env_aqhi_worsens")
    smoke_days = e2.slider("Smoke persists", 0, 5, 3, 1, key="env_smoke_days")
    heat_wave = e3.toggle("Heat wave", value=False, key="env_heat_wave")
    extreme_cold = e4.toggle("Extreme cold", value=False, key="env_extreme_cold")
    snowstorm = e5.toggle("Freezing rain/snowstorm", value=False, key="env_snowstorm")
    scenario_stress = min(
        1.0,
        float(latest["environmental_stress_index"])
        + 0.035 * aqhi_worsens
        + 0.04 * smoke_days
        + 0.09 * heat_wave
        + 0.06 * extreme_cold
        + 0.08 * snowstorm,
    )
    station_map = pd.DataFrame(
        [
            {"facility": facility, "weather_station_mapping": f"{latest['city']} reference station", "mapping_status": "synthetic local placeholder", "confidence": "moderate"},
        ]
    )
    st.dataframe(station_map, width="stretch", hide_index=True)
    st.metric("Scenario environmental stress", f"{scenario_stress:.2f}", f"{scenario_stress - float(latest['environmental_stress_index']):+.2f}")
    huddle_brief_component(
        [
            "Environmental stress may increase respiratory/asthma, heat/cold exposure, and access-friction pressure.",
            f"Scenario stress index is {scenario_stress:.2f}; confidence is moderate-to-wide in public mode.",
            "Watch AQHI, smoke duration, weather alerts, EMS offload, respiratory presentations, and staff access.",
            "Consider respiratory cohorting, hydration/cooling or cold exposure readiness, and transport/access briefings.",
            "Internal data needed: complaint mix, EMS/offload, location events, staffing access, diagnostic TAT, and bed state.",
        ]
    )
    method_note("Future source adapters should separate weather observations, forecast alerts, AQHI, wildfire status, and smoke-model features with independent freshness checks.")


def travel_tab(public_data: dict[str, pd.DataFrame], facility: str) -> None:
    st.subheader("Travel Friction & Access Disruption")
    lineage_strip(["OPEN_DATA", "HYBRID_OPEN_SYNTHETIC"])
    travel = public_data.get("travel_friction", pd.DataFrame())
    site = travel[travel["facility"] == facility].copy()
    if site.empty:
        st.info("No travel friction fallback data available.")
        return
    latest = site.sort_values("timestamp").tail(1).iloc[0]
    cols = st.columns(4)
    cols[0].metric("Travel friction", f"{latest['travel_friction_index']:.2f}")
    cols[1].metric("Road incidents", f"{latest['road_incidents']:.0f}")
    cols[2].metric("Road closures", f"{latest['road_closures']:.0f}")
    cols[3].metric("Transit disruption", f"{latest['transit_disruption_index']:.2f}")
    st.plotly_chart(line_chart(site, "timestamp", "travel_friction_index", title=f"{facility} access disruption forecast"), width="stretch")
    st.dataframe(site.head(96), width="stretch", hide_index=True, height=320)
    st.markdown("**Access Friction Scenario**")
    t1, t2, t3, t4 = st.columns(4)
    road_disruption = t1.slider("Major road disruption", 0.0, 1.0, 0.25, 0.05, key="travel_road_disruption")
    downtown_event = t2.slider("Large public event", 0.0, 1.0, 0.20, 0.05, key="travel_downtown_event")
    transit_disruption = t3.slider("Transit disruption", 0.0, 1.0, 0.15, 0.05, key="travel_transit_disruption")
    severe_weather = t4.slider("Severe weather access", 0.0, 1.0, 0.20, 0.05, key="travel_severe_weather")
    scenario_friction = min(1.0, float(latest["travel_friction_index"]) + 0.22 * road_disruption + 0.16 * downtown_event + 0.14 * transit_disruption + 0.18 * severe_weather)
    access_rows = pd.DataFrame(
        [
            ("baseline travel friction", float(latest["travel_friction_index"]), "HYBRID_OPEN_SYNTHETIC", "access context only"),
            ("scenario travel friction", scenario_friction, "MODEL_OUTPUT", "may shift ambulance/patient/staff arrival timing"),
            ("estimated arrival clustering lift", (scenario_friction - float(latest["travel_friction_index"])) * 0.32, "MODEL_OUTPUT", "not a direct EMS feed"),
        ],
        columns=["signal", "value", "lineage", "interpretation"],
    )
    st.dataframe(access_rows, width="stretch", hide_index=True)
    huddle_brief_component(
        [
            f"Travel friction scenario increases access index to {scenario_friction:.2f}.",
            "Access may be impaired and arrival timing may cluster; this is not a direct EMS feed.",
            "Watch EMS offload, front-door arrivals, staff access, and transfer/transport delays.",
            "Consider access briefings, EMS/offload process attention, and arrival pulse readiness.",
            "Internal data needed: EMS arrival estimates, offload timestamps, staff rosters, transport requests, and transfer centre feeds.",
        ]
    )
    method_note("Travel context is operational planning context: it can explain timing, EMS access, and staff/patient arrival friction, but local mode remains synthetic.")


def public_scenario_tab(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str, horizon_hours: int) -> None:
    st.subheader("Public Scenario Workbench")
    lineage_strip(["USER_INPUT", "HYBRID_OPEN_SYNTHETIC", "MODEL_OUTPUT"])
    controls, output = st.columns([0.9, 1.5])
    with controls:
        respiratory_surge = st.slider("Respiratory surge", 0.0, 3.0, 1.2, 0.1, key="scenario_respiratory_surge")
        school_reopening = st.toggle("School reopening", value=False, key="scenario_school_reopening")
        long_weekend = st.toggle("Long weekend", value=False, key="scenario_long_weekend")
        large_public_event = st.slider("Large public event", 0.0, 1.0, 0.15, 0.05, key="scenario_large_public_event")
        smoke_event = st.slider("Smoke event", 0.0, 1.0, 0.15, 0.05, key="scenario_smoke_event")
        heat_wave = st.slider("Heat wave", 0.0, 1.0, 0.10, 0.05, key="scenario_heat_wave")
        cold_snap_snowstorm = st.slider("Cold snap/snowstorm", 0.0, 1.0, 0.10, 0.05, key="scenario_cold_snap_snowstorm")
        traffic_disruption = st.slider("Traffic disruption", 0.0, 1.0, 0.15, 0.05, key="scenario_traffic_disruption")
        wildfire_evacuation_access = st.slider("Wildfire evacuation/access issue", 0.0, 1.0, 0.05, 0.05, key="scenario_wildfire_access")
        wait_deterioration = st.number_input("Public wait-time deterioration", 0, 300, 60, 5, key="scenario_wait_deterioration")
        capacity_constraint = st.slider("Synthetic internal capacity constraint", 0.0, 1.0, 0.25, 0.05, key="scenario_capacity_constraint")
        shocks = ScenarioShockConfig(
            respiratory_surge=respiratory_surge,
            school_reopening=school_reopening,
            long_weekend=long_weekend,
            large_public_event=large_public_event,
            smoke_event=smoke_event,
            heat_wave=heat_wave,
            cold_snap_snowstorm=cold_snap_snowstorm,
            traffic_disruption=traffic_disruption,
            wildfire_evacuation_access=wildfire_evacuation_access,
            public_wait_deterioration_mins=int(wait_deterioration),
            synthetic_capacity_constraint=capacity_constraint,
        )
        if st.button("Run combined public scenario"):
            st.session_state.public_scenario_bundle = run_combined_public_scenario(visits, public_data, facility, horizon_hours, shocks)
    if "public_scenario_bundle" not in st.session_state:
        st.session_state.public_scenario_bundle = run_combined_public_scenario(
            visits, public_data, facility, horizon_hours, ScenarioShockConfig(respiratory_surge=1.2, public_wait_deterioration_mins=60, synthetic_capacity_constraint=0.25)
        )
    scenario_bundle = st.session_state.public_scenario_bundle
    with output:
        forecast = scenario_bundle["forecast"]
        impact = scenario_bundle["impact"]
        affected = scenario_bundle["affected_stages"]
        ranking = scenario_bundle["ranking"]
        st.plotly_chart(px.line(forecast, x="timestamp", y="p50_pressure", color="scenario", title="Baseline vs combined public-stress forecast"), width="stretch")
        st.dataframe(impact, width="stretch", hide_index=True)
        st.markdown("**Top affected stages**")
        st.dataframe(affected, width="stretch", hide_index=True)
    st.markdown("**Scenario Ranking**")
    st.dataframe(scenario_bundle["ranking"], width="stretch", hide_index=True)
    huddle_brief_component(scenario_bundle["huddle"])
    method_note("The huddle brief is generated deterministically from coded scenario outputs. Optional model providers may improve narrative wording, but numeric results come from code.")


def constrained_internal_tab(visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("TB_ED_VISITS Internal-Ready Flow Analytics")
    lineage_strip(["SECURE_INTERNAL_READY_SCHEMA", "SYNTHETIC_DATA"])
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    constrained = constrained_projection(visit_view)
    if constrained.empty:
        st.info("No constrained synthetic visits match this filter.")
        return
    st.dataframe(constrained_boundary_check(constrained, CONSTRAINED_ANALYSIS_COLUMNS), width="stretch", hide_index=True)
    quality_flags = pd.DataFrame(
        [
            {"flag": "invalid_los_flagged", "count": int(visit_view.get("INVALID_LOS_CALC_FLAG", pd.Series(dtype=str)).fillna("N").eq("Y").sum())},
            {"flag": "scheduled_ed_visits", "count": int(visit_view.get("SCHEDULED_ED_VISIT_FLAG", pd.Series(dtype=str)).fillna("N").eq("Y").sum())},
            {"flag": "missing_first_contact", "count": int(constrained.get("FIRST_CONTACT_DATETIME", pd.Series(dtype="datetime64[ns]")).isna().sum())},
            {"flag": "negative_los_or_duration", "count": int((pd.to_numeric(constrained.get("ED_LOS_HRS", pd.Series(dtype=float)), errors="coerce") < 0).sum())},
            {"flag": "los_outlier_over_48h", "count": int((pd.to_numeric(constrained.get("ED_LOS_HRS", pd.Series(dtype=float)), errors="coerce") > 48).sum())},
        ]
    )
    tabs = st.tabs(["Explorer", "Event Log", "Patterns", "Parameters", "Replay Validation", "Quality & Quantiles"])
    with tabs[0]:
        cols = ["DATA_RECORD_ID", "DEPARTMENT_TYPE", "TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "PRESENTING_COMPLAINT", "DISPOSITION_GROUP", "ED_LOS_HRS"]
        st.dataframe(constrained[[c for c in cols if c in constrained.columns]].head(300), width="stretch", hide_index=True, height=310)
        st.plotly_chart(duration_distribution(add_flow_features(constrained), "ED_LOS_HRS", color="DISPOSITION_GROUP", title="ED LOS distribution"), width="stretch")
    with tabs[1]:
        event_log = construct_event_log(constrained)
        intervals = reconstruct_stage_intervals(constrained)
        concurrency = observed_concurrency(intervals)
        c1, c2 = st.columns(2)
        c1.dataframe(event_log.head(400), width="stretch", hide_index=True, height=350)
        c2.dataframe(intervals.head(400), width="stretch", hide_index=True, height=350)
        if not concurrency.empty:
            stage_hour = concurrency.groupby(["stage", "timestamp"], as_index=False)["concurrency"].sum()
            st.plotly_chart(line_chart(stage_hour, "timestamp", "concurrency", color="stage", title="Observed concurrency by reconstructed stage"), width="stretch")
    with tabs[2]:
        arrivals = arrival_patterns(constrained)
        hour_summary = arrivals.groupby("arrival_hour", as_index=False)["arrivals"].sum()
        st.plotly_chart(metric_bar(hour_summary, "arrival_hour", "arrivals", title="Arrival patterns by hour"), width="stretch")
        c1, c2 = st.columns(2)
        c1.dataframe(route_probabilities(constrained).head(80), width="stretch", hide_index=True)
        c2.dataframe(stage_duration_distributions(constrained), width="stretch", hide_index=True)
    with tabs[3]:
        st.json(estimate_baseline_parameters(constrained), expanded=False)
        method_note("Baseline simulation parameters are inferred from constrained timestamps, route probabilities, consult probability, boarding delay, and observed concurrency assumptions.")
    with tabs[4]:
        scenario = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=10)
        output = run_simulation(constrained, scenario)
        st.dataframe(validation_metric_summary(constrained, output.patients), width="stretch", hide_index=True)
        st.plotly_chart(uncertainty_interval_chart(summarize_with_uncertainty(output.summary)), width="stretch")
    with tabs[5]:
        st.markdown("**Data-quality flags**")
        st.dataframe(quality_flags, width="stretch", hide_index=True)
        quantile_cols = {
            "ED_LOS_HRS": "ED LOS all",
            "ED_LOS_ADMITTED_HRS": "ED LOS admitted",
            "ED_LOS_DISCHARGED_HRS": "ED LOS discharged",
            "ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS": "time to PIA",
            "ED_LOS_FIRST_CONTACT_TO_INITIAL_ROOMED_IN_ED_HRS": "time to roomed",
            "ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS": "boarding measure",
            "ED_LOS_FIRST_CONTACT_TO_EMS_HANDOFF_MINS": "EMS handoff minutes",
        }
        rows = []
        for column, label in quantile_cols.items():
            if column in constrained:
                values = pd.to_numeric(constrained[column], errors="coerce").dropna()
                if not values.empty:
                    rows.append(
                        {
                            "measure": label,
                            "p50": float(values.quantile(0.50)),
                            "p75": float(values.quantile(0.75)),
                            "p90": float(values.quantile(0.90)),
                            "p95": float(values.quantile(0.95)),
                            "n": int(len(values)),
                        }
                    )
        st.markdown("**P50/P75/P90/P95 constrained measures**")
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        method_note("Clinical-event timestamps come from the supplied TB_ED_VISITS fields. ROW_CREATE_DATETIME and ROW_UPDATE_DATETIME are not used as event timestamps.")


def waiting_room_tab(backend: LocalBackend, active: pd.DataFrame, facility: str, pediatric_only: bool, config: AppConfig) -> None:
    st.subheader("Waiting Room MRN Chart Summaries")
    lineage_strip(["SYNTHETIC_DATA", "SECURE_INTERNAL_READY_SCHEMA", "MODEL_OUTPUT"])
    warning_note("Synthetic chart summarization aid only. It is not a substitute for chart review, clinical assessment, or source-system verification.")
    active_view = active[active["facility"] == facility].copy()
    if pediatric_only:
        active_view = active_view[active_view["age_group"].isin(PEDIATRIC_AGE_GROUPS)]
    if "selected_mrns" not in st.session_state:
        st.session_state.selected_mrns = active_view["mrn"].head(4).astype(str).tolist()

    with st.form("manual_mrn_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        entered = col1.text_input("Manual synthetic MRN entry", placeholder="SYN-MRN-100000")
        add = col2.form_submit_button("Add MRN")
        if add and entered:
            mrn = entered.strip()
            if mrn and mrn not in st.session_state.selected_mrns:
                st.session_state.selected_mrns.append(mrn)

    remove_options = st.session_state.selected_mrns.copy()
    col_remove, col_button = st.columns([2, 1])
    remove_mrn = col_remove.selectbox("Remove MRN", remove_options or ["No selected MRNs"], disabled=not remove_options)
    if col_button.button("Remove selected", disabled=not remove_options):
        st.session_state.selected_mrns = [m for m in st.session_state.selected_mrns if m != remove_mrn]
        st.rerun()

    left, right = st.columns([0.86, 1.6])
    with left:
        st.markdown("**Scrollable waiting-room list**")
        list_cols = ["mrn", "triage_level", "age_group", "presenting_complaint", "current_stage", "lwbs_risk"]
        st.dataframe(active_view[list_cols].sort_values(["triage_level", "mrn"]), width="stretch", hide_index=True, height=560)
    with right:
        model_client = get_model_client(config)
        if not st.session_state.selected_mrns:
            st.info("Add a synthetic MRN to view chart context.")
        for mrn in st.session_state.selected_mrns:
            context = backend.load_chart_context_by_mrn(mrn)
            summary = summarize_chart_context(context, model_client)
            demographics = context.demographics
            st.markdown("<div class='patient-card'>", unsafe_allow_html=True)
            top_cols = st.columns([1.35, 1, 0.8])
            top_cols[0].markdown(f"**{mrn}**")
            top_cols[0].caption(
                f"{demographics.get('age_group', 'Unknown age group')} | CTAS {demographics.get('triage_level', 'unknown')} | {demographics.get('presenting_complaint', 'No complaint')}"
            )
            top_cols[1].caption(f"Freshness: {summary['source_freshness']}")
            if top_cols[2].button("Refresh summary", key=f"refresh_{mrn}"):
                st.toast(f"Summary refreshed for {mrn}")
            st.markdown("**Latest summary**")
            st.write(summary["one_line_clinical_context"])
            with st.expander("Structured summary sections", expanded=False):
                for label, key in [
                    ("Recent ED/provider note highlights", "recent_ed_provider_note_highlights"),
                    ("Active problem list", "active_problem_list"),
                    ("Relevant medical history", "relevant_medical_history"),
                    ("Recent consult/referral context", "recent_consult_referral_context"),
                    ("Imaging highlights", "imaging_highlights"),
                    ("Lab/result-comment highlights", "lab_result_comment_highlights"),
                    ("Open questions / missing information", "open_questions_missing_information"),
                ]:
                    st.markdown(f"**{label}**")
                    st.write(summary[key])
            st.markdown("**Source sections**")
            for label, source_key in [
                ("ED provider notes", "ed_provider_notes"),
                ("Encounter notes", "encounter_notes"),
                ("Consult notes", "consult_notes"),
                ("Admission H&P notes", "admission_hp_notes"),
                ("Imaging", "imaging"),
                ("Labs", "labs"),
                ("Problem list", "problem_list"),
                ("Medical history", "medical_history"),
                ("Referrals", "referrals"),
            ]:
                with st.expander(label, expanded=False):
                    section = context.sections.get(source_key)
                    if section is None:
                        st.write("No synthetic source data available for this section.")
                    else:
                        st.write(section.content)
                        fresh = section.freshness.isoformat(timespec="minutes") if section.freshness else "unknown"
                        st.caption(f"{section.source_count} synthetic source row(s), freshness {fresh}")
            st.caption(f"Sources: {summary['source_list']} | Mapping: {context.mapped_source_field}")
            st.markdown("</div>", unsafe_allow_html=True)


def hybrid_forecasting_tab(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str, horizon_hours: int) -> None:
    st.subheader("Hybrid Forecasting Lab")
    lineage_strip(["HYBRID_OPEN_SYNTHETIC", "HYBRID_OPEN_INTERNAL_READY", "MODEL_OUTPUT"])
    bundle = forecast_external_pressure(public_data, facility, horizon_hours=max(horizon_hours, 72), horizon_days=14)
    simple_arrivals = hybrid_arrival_forecast(visits, public_data, facility, horizon_hours)
    internal_targets = forecast_internal_targets(visits, public_data, facility)
    if bundle.hourly.empty:
        st.info("No public feature matrix is available for this facility.")
        return
    feature_frame = build_public_feature_matrix(public_data, facility)
    backtest = rolling_origin_backtest(feature_frame)
    tabs = st.tabs(["Hourly Forecast", "Daily Forecast", "Model Validation", "Drivers & Registry", "Internal-Ready Targets"])
    with tabs[0]:
        st.plotly_chart(
            px.line(bundle.hourly, x="timestamp", y=["p10_pressure", "p50_pressure", "p90_pressure"], title="External pressure forecast P10/P50/P90"),
            width="stretch",
        )
        st.plotly_chart(line_chart(simple_arrivals, "hour_ahead", "expected_arrivals", title="Forecast-to-arrival pressure pipeline"), width="stretch")
        st.dataframe(bundle.hourly.head(96), width="stretch", hide_index=True)
    with tabs[1]:
        st.plotly_chart(
            px.line(bundle.daily, x="forecast_date", y=["p10_pressure", "p50_pressure", "p90_pressure", "peak_p50_pressure"], title="Daily external pressure forecast"),
            width="stretch",
        )
        st.dataframe(bundle.daily, width="stretch", hide_index=True)
    with tabs[2]:
        c1, c2 = st.columns(2)
        c1.markdown("**Holdout model comparison**")
        c1.dataframe(bundle.validation, width="stretch", hide_index=True)
        c2.markdown("**Rolling-origin backtest**")
        c2.dataframe(backtest, width="stretch", hide_index=True)
        method_note("Validation uses synthetic/public fallback history locally. In Snowflake, this framework should run by site, zone, pediatric flag, hour/day, and holdout period against real TB_ED_VISITS-linked outcomes.")
    with tabs[3]:
        st.markdown("**Feature drivers**")
        st.dataframe(bundle.drivers, width="stretch", hide_index=True)
        st.markdown("**Model registry**")
        st.dataframe(bundle.registry, width="stretch", hide_index=True)
    with tabs[4]:
        st.dataframe(internal_targets, width="stretch", hide_index=True)
        method_note("Public mode predicts external pressure and synthetic internal-ready targets. Snowflake mode should join public context to real TB_ED_VISITS by site/hour/day for arrivals, CTAS mix, admission probability, LWBS risk, LOS, PIA, and boarding risk.")


def simulation_tab(visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int, config: AppConfig) -> None:
    st.subheader("Simulation Lab")
    lineage_strip(["SYNTHETIC_DATA", "USER_INPUT", "MODEL_OUTPUT"])
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    if visit_view.empty:
        st.info("No visits match this simulation filter.")
        return
    controls, results = st.columns([0.9, 1.7])
    with controls:
        arrival_multiplier = st.slider("Arrival surge multiplier", 0.5, 2.5, 1.0, 0.1)
        triage_delta = st.number_input("Triage capacity change", -3, 8, 0, 1)
        physician_delta = st.number_input("Physician capacity change", -3, 12, 0, 1)
        room_delta = st.number_input("Rooming capacity change", -10, 25, 0, 1)
        fast_track = st.toggle("Fast-track CTAS 4/5", value=False)
        consult_improve = st.slider("Consult turnaround improvement", 0.0, 0.75, 0.15, 0.05)
        diagnostic_improve = st.slider("Diagnostic turnaround improvement", 0.0, 0.75, 0.10, 0.05)
        bed_improve = st.slider("Admission bed availability improvement", 0.0, 0.75, 0.10, 0.05)
        boarding_reduce = st.slider("Boarding reduction", 0.0, 0.80, 0.10, 0.05)
        discharge_accel = st.slider("Discharge acceleration", 0.0, 0.50, 0.05, 0.05)
        ems_improve = st.slider("EMS offload process improvement", 0.0, 0.75, 0.10, 0.05)
        reps = st.number_input("Monte Carlo replications", 10, 500, 50, 10)
        seed = st.number_input("Random seed", 1, 9999, 42, 1)
    scenario = ScenarioConfig(
        facility=facility,
        horizon_hours=horizon_hours,
        replications=int(reps),
        random_seed=int(seed),
        arrival_surge_multiplier=float(arrival_multiplier),
        triage_capacity_delta=int(triage_delta),
        physician_capacity_delta=int(physician_delta),
        rooming_capacity_delta=int(room_delta),
        fast_track_enabled=bool(fast_track),
        consult_turnaround_improvement=float(consult_improve),
        diagnostic_turnaround_improvement=float(diagnostic_improve),
        admission_bed_improvement=float(bed_improve),
        boarding_reduction=float(boarding_reduce),
        discharge_acceleration=float(discharge_accel),
        ems_offload_improvement=float(ems_improve),
    )
    enhanced = run_enhanced_simulation_summary(visit_view, scenario)
    uncertainty = enhanced["uncertainty"]
    with results:
        st.plotly_chart(uncertainty_interval_chart(uncertainty), width="stretch")
        st.dataframe(uncertainty, width="stretch", hide_index=True)
        queue_avg = enhanced["queue_lengths"].groupby("hour", as_index=False)[["waiting_for_physician", "boarding", "total_active_pressure"]].mean()
        st.plotly_chart(line_chart(queue_avg, "hour", "total_active_pressure", title="Expected active pressure over time"), width="stretch")
    st.markdown("**Resource utilization and stage occupancy**")
    u1, u2 = st.columns(2)
    u1.dataframe(enhanced["utilization"], width="stretch", hide_index=True)
    u2.plotly_chart(px.line(enhanced["occupancy"], x="hour", y=["waiting_room", "roomed_not_seen", "diagnostics_consults", "boarding"], title="Stage occupancy over time"), width="stretch")

    baseline = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=min(int(reps), 20), random_seed=int(seed))
    comparison = compare_scenarios(
        visit_view,
        [
            baseline,
            scenario.model_copy(update={"replications": min(int(reps), 20)}),
            baseline.model_copy(update={"fast_track_enabled": True}),
            baseline.model_copy(update={"boarding_reduction": 0.25, "admission_bed_improvement": 0.2}),
            baseline.model_copy(update={"physician_capacity_delta": 1, "triage_capacity_delta": 1}),
        ],
    )
    c1, c2 = st.columns(2)
    c1.markdown("**Scenario comparison table**")
    c1.dataframe(comparison, width="stretch", hide_index=True)
    c2.markdown("**Bottleneck shift analysis**")
    c2.dataframe(enhanced["migration"], width="stretch", hide_index=True)
    st.markdown("**Scenario Ranking and Pressure-to-Action Translator**")
    r1, r2 = st.columns([1.35, 1])
    r1.dataframe(enhanced["ranking"], width="stretch", hide_index=True)
    with r2:
        huddle_brief_component(enhanced["huddle"])
        for action in enhanced["actions"]:
            st.write(f"- {action}")
    st.markdown("**Prioritized interventions from scenario comparison**")
    st.dataframe(rank_interventions(comparison), width="stretch", hide_index=True)
    st.markdown("**LWBS hazard sensitivity check**")
    hazard_rows = pd.DataFrame(
        [
            {"triage_level": triage, "wait_hours": wait, "crowding_index": crowd, "lwbs_hazard": lwbs_hazard(wait, crowd, triage)}
            for triage in [2, 3, 4, 5]
            for wait, crowd in [(1.0, 0.25), (3.0, 0.55), (5.0, 0.85)]
        ]
    )
    st.dataframe(hazard_rows, width="stretch", hide_index=True)
    explanation = get_model_client(config).explain_scenario(comparison)
    method_note(f"Practical interpretation: {practical_interpretation(comparison)} {explanation}")


def bed_boarding_tab(data: dict[str, pd.DataFrame], public_data: dict[str, pd.DataFrame], facility: str, pediatric_only: bool) -> None:
    st.subheader("Bed, Boarding, Discharge & Transfer Intelligence")
    lineage_strip(["SECURE_INTERNAL_PLACEHOLDER", "SYNTHETIC_DATA", "HYBRID_OPEN_SYNTHETIC"])
    warning_note("Expanded bed/boarding/transfer intelligence is synthetic and assumption-based in local mode.")
    active = data["active"][data["active"]["facility"] == facility].copy()
    if pediatric_only:
        active = active[active["age_group"].isin(PEDIATRIC_AGE_GROUPS)]
    capacity = data["capacity"][data["capacity"]["facility"] == facility].copy()
    events = data["expanded_events"][data["expanded_events"]["facility"] == facility].copy()
    latest = capacity.sort_values("snapshot_datetime").tail(1)
    cols = st.columns(4)
    cols[0].metric("DTA boarders", int(active["current_stage"].eq("decision_to_admit_boarder").sum()))
    cols[1].metric("Available inpatient beds", int(latest["inpatient_available_beds"].iloc[0]) if not latest.empty else 0)
    cols[2].metric("Pending discharges", int(latest["pending_discharges"].iloc[0]) if not latest.empty else 0)
    cols[3].metric("Transfer requests", int(latest["transfer_requests_waiting"].iloc[0]) if not latest.empty else 0)
    tabs = st.tabs(["Digital Twin", "Bed Placement Optimizer", "Discharge Cascade", "Transfer Scenario"])
    with tabs[0]:
        st.dataframe(active.sort_values(["triage_level", "arrival_datetime"]), width="stretch", hide_index=True, height=320)
        st.plotly_chart(metric_bar(events["event_type"].value_counts().rename_axis("event_type").reset_index(name="events"), "event_type", "events", title="Synthetic operational event mix"), width="stretch")
    with tabs[1]:
        st.dataframe(greedy_bed_placement_optimizer(active, capacity), width="stretch", hide_index=True)
        method_note("Greedy objective: reduce ED boarding hours while respecting synthetic bed availability and priority signals. Future pilot requires specialty, isolation, age, team, and unit-level constraints.")
    with tabs[2]:
        cascade_cols = ["snapshot_datetime", "pending_discharges", "beds_cleaning", "inpatient_available_beds", "transfer_requests_waiting"]
        st.dataframe(capacity[cascade_cols].head(48), width="stretch", hide_index=True)
        st.plotly_chart(line_chart(capacity, "snapshot_datetime", "inpatient_available_beds", title="Discharge-to-bed availability cascade"), width="stretch")
    with tabs[3]:
        constraints = likely_binding_constraints(active, capacity, public_data, facility)
        st.dataframe(constraints, width="stretch", hide_index=True)
        method_note("Transfer scenarios are framed as operational what-if analysis. They should be calibrated with transfer-centre, transport, receiving-unit, and bed-board feeds.")


def staffing_tab(data: dict[str, pd.DataFrame], facility: str) -> None:
    st.subheader("Staffing & Resource Sensitivity")
    lineage_strip(["SECURE_INTERNAL_PLACEHOLDER", "SYNTHETIC_DATA"])
    active = data["active"][data["active"]["facility"] == facility].copy()
    capacity = data["capacity"][data["capacity"]["facility"] == facility].copy()
    st.dataframe(staffing_sensitivity(active, capacity), width="stretch", hide_index=True)
    c1, c2 = st.columns(2)
    c1.plotly_chart(line_chart(capacity, "snapshot_datetime", "physicians_on_shift", title="Physicians on shift fallback"), width="stretch")
    c2.plotly_chart(line_chart(capacity, "snapshot_datetime", "nurses_on_shift", title="Nurses on shift fallback"), width="stretch")
    st.plotly_chart(line_chart(capacity, "snapshot_datetime", "consult_queue", title="Consult queue sensitivity context"), width="stretch")
    method_note("Staffing sensitivity is directional in local mode. Snowflake pilot should validate shift roster coverage, role grouping, breaks, surge teams, and task-specific capacity assumptions.")


def validation_governance_tab(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("Model Validation, Calibration & Governance")
    lineage_strip(["SECURE_INTERNAL_READY_SCHEMA", "HYBRID_OPEN_SYNTHETIC", "MODEL_OUTPUT"])
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    if visit_view.empty:
        st.info("No visits match this validation filter.")
        return
    summary = governance_summary(visit_view)
    train, holdout = holdout_split_by_date(visit_view)
    simulation = run_simulation(holdout if not holdout.empty else visit_view, ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=10))
    c1, c2 = st.columns(2)
    c1.markdown("**Holdout validation by date**")
    c1.write(f"Training rows: **{len(train):,}** | Holdout rows: **{len(holdout):,}**")
    c1.dataframe(validation_metric_summary(holdout if not holdout.empty else visit_view, simulation.patients), width="stretch", hide_index=True)
    c2.markdown("**Open-data cache quality**")
    c2.dataframe(public_data_quality_summary(public_data), width="stretch", hide_index=True)
    tabs = st.tabs(["Calibration", "Durations", "Data Quality", "Drift", "Controls"])
    with tabs[0]:
        st.dataframe(summary["facility_calibration"], width="stretch", hide_index=True)
        st.dataframe(summary["admission_calibration"], width="stretch", hide_index=True)
    with tabs[1]:
        st.dataframe(stage_duration_distributions(visit_view), width="stretch", hide_index=True)
        st.plotly_chart(duration_distribution(add_flow_features(visit_view), "ED_LOS_HRS", color="DISPOSITION_GROUP", title="Observed LOS by disposition"), width="stretch")
    with tabs[2]:
        st.dataframe(summary["missing_timestamps"], width="stretch", hide_index=True)
        st.write(summary["data_quality"].warnings)
    with tabs[3]:
        st.dataframe(summary["drift"], width="stretch", hide_index=True)
    with tabs[4]:
        st.markdown("**Explainability summaries**")
        for item in summary["explainability"]:
            st.write(f"- {item}")
        st.markdown("**Audit log design**")
        for item in summary["audit_log_design"]:
            st.write(f"- {item}")
        method_note("Human-in-the-loop review, privacy/security controls, drift monitoring, calibration by facility, and scenario-audit logging are required before any internal pilot.")


def snowflake_porting_tab(config: AppConfig) -> None:
    st.subheader("Snowflake Porting & Day-One Internal Setup")
    lineage_strip(["SECURE_INTERNAL_READY_SCHEMA", "SECURE_INTERNAL_PLACEHOLDER", "HYBRID_OPEN_INTERNAL_READY"])
    st.markdown(
        """
        **Local v2 architecture**

        `Synthetic CSVs + public fallback cache -> LocalBackend/OpenDataHub -> pandas analytics -> Streamlit app`

        **Snowflake target architecture**

        `TB_ED_VISITS + semantic views + open-data landing tables + governed operational feeds -> Snowpark adapters -> same app contracts -> Streamlit in Snowflake`

        **Model layer**

        `MockModelClient by default -> optional approved OpenAI/Snowflake-native provider -> explanations and summaries only`
        """
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Configuration targets**")
        st.json(
            {
                "database": config.snowflake_database,
                "schema": config.snowflake_schema,
                "warehouse": config.snowflake_warehouse,
                "active_session": "snowflake.snowpark.context.get_active_session() inside Streamlit in Snowflake",
                "local_fallback": "Environment variables for account/user/role/warehouse/database/schema",
            }
        )
        st.markdown("**Expected secure internal datasets**")
        st.write(", ".join(SECURE_INTERNAL_DATASETS))
    with c2:
        checklist = pd.DataFrame(
            [
                ("Create OPEN_DATA, CURATED, OPERATIONS, GOVERNANCE schemas", "Day one"),
                ("Load TB_ED_VISITS secure constrained view", "Required"),
                ("Validate PATIENT_CHART to PAT_MRN_ID mapping", "Required before chart-review pilot"),
                ("Deploy lineage and refresh audit tables", "Required"),
                ("Replace local CSV loaders with SnowflakeBackend", "No UI contract change expected"),
                ("Calibrate facility and pediatric strata", "Required for operations use"),
                ("Approve model provider and PHI boundary", "Required before real note summarization"),
            ],
            columns=["Step", "Readiness note"],
        )
        st.dataframe(checklist, width="stretch", hide_index=True)
    st.markdown("**TB_ED_VISITS extraction SQL template**")
    st.code(build_ed_visits_sql(), language="sql")
    st.markdown("**Recent and active visit SQL templates**")
    st.code(build_recent_ed_visits_sql(), language="sql")
    st.code(build_active_visits_sql(), language="sql")
    st.markdown("**Chart-review semantic view SQL templates**")
    templates = build_chart_context_sql(config.snowflake_database, config.snowflake_schema)
    selected = st.selectbox("Semantic view template", sorted(templates))
    st.code(templates[selected], language="sql")
    st.markdown("**SQL file templates**")
    sql_files = available_sql_templates()
    selected_file = st.selectbox("Snowflake SQL file", sql_files)
    st.code(load_sql_template(selected_file), language="sql")
    warning_note("Snowflake mode must keep PHI and identifiers inside approved governed views. External model calls should remain disabled unless explicitly approved for the data class and audited.")


def lineage_refresh_tab(open_bundle: dict[str, object]) -> None:
    st.subheader("Data Linkages & Refresh Status")
    lineage_strip(["OPEN_DATA", "SYNTHETIC_DATA", "SECURE_INTERNAL_PLACEHOLDER", "SECURE_INTERNAL_READY_SCHEMA", "HYBRID_OPEN_SYNTHETIC", "HYBRID_OPEN_INTERNAL_READY", "MODEL_OUTPUT", "USER_INPUT"])
    registry = open_bundle["registry"]
    statuses = open_bundle["refresh_status"]
    st.markdown("**Lineage category legend**")
    st.dataframe(category_legend_frame(), width="stretch", hide_index=True)
    st.markdown("**Configured source registry**")
    st.dataframe(registry, width="stretch", hide_index=True, height=300)
    st.markdown("**Refresh, quality, and Snowflake target status**")
    status_df = lineage_status_display_frame(statuses)
    st.dataframe(status_df, width="stretch", hide_index=True, height=420)
    method_note("This tab is intentionally last. It is the control panel for source provenance, refresh cadence, fallback status, Snowflake target mapping, and PHI/identifier risk.")


def main() -> None:
    configure_page()
    config = get_config()
    backend = get_backend(str(config.data_dir))
    data = load_core_data(str(config.data_dir))
    open_bundle = load_open_bundle()
    public_data = open_bundle["public_data"]
    visits = data["visits"]
    all_visits = data["all_visits"]
    active = data["active"]
    facility, pediatric_only, horizon_hours = sidebar_controls(config, visits)

    st.title("AHS ED Flow Intelligence Prototype vNext")
    st.caption("Snowflake-portable ED flow simulation, public pressure intelligence, internal-ready analytics, and governed AI-support layer. Synthetic local mode only.")

    tabs = st.tabs(V2_TAB_NAMES)
    with tabs[0]:
        executive_tab(visits, active, all_visits, public_data, facility, pediatric_only, horizon_hours)
    with tabs[1]:
        public_pressure_tab(public_data, facility)
    with tabs[2]:
        public_wait_times_tab(public_data)
    with tabs[3]:
        respiratory_tab(public_data, facility)
    with tabs[4]:
        environmental_tab(public_data, facility)
    with tabs[5]:
        travel_tab(public_data, facility)
    with tabs[6]:
        public_scenario_tab(visits, public_data, facility, horizon_hours)
    with tabs[7]:
        constrained_internal_tab(visits, facility, pediatric_only, horizon_hours)
    with tabs[8]:
        waiting_room_tab(backend, active, facility, pediatric_only, config)
    with tabs[9]:
        hybrid_forecasting_tab(visits, public_data, facility, horizon_hours)
    with tabs[10]:
        simulation_tab(visits, facility, pediatric_only, horizon_hours, config)
    with tabs[11]:
        bed_boarding_tab(data, public_data, facility, pediatric_only)
    with tabs[12]:
        staffing_tab(data, facility)
    with tabs[13]:
        validation_governance_tab(visits, public_data, facility, pediatric_only, horizon_hours)
    with tabs[14]:
        snowflake_porting_tab(config)
    with tabs[15]:
        lineage_refresh_tab(open_bundle)


if __name__ == "__main__":
    main()

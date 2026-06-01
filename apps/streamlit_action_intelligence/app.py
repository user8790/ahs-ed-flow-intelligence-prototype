"""AHS ED Flow Action Intelligence Streamlit app."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
KERNEL = ROOT / "packages" / "ed_flow_kernel"
for path in [ROOT, SRC, KERNEL]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pandas as pd
import plotly.express as px
import streamlit as st

from ed_flow.data_contracts import ScenarioConfig, VisitFilters
from ed_flow.config import AppConfig
from ed_flow_kernel.backends.local_backend import create_local_backend
from ed_flow_kernel.config import KernelConfig
from ed_flow_kernel.constants import ACTION_APP_NAME
from ed_flow_kernel.contracts.tb_ed_visits import TbEdVisitsContract
from ed_flow_kernel.features.open_data_features import site_hour_public_features
from ed_flow_kernel.features.hybrid_features import internal_ready_targets
from ed_flow_kernel.forecasting.ensembles import external_pressure_forecast
from ed_flow_kernel.simulation.scenarios import ScenarioShockConfig, combined_public_scenario, enhanced_simulation, lwbs_hazard
from ed_flow_intelligence.data_sources.public_adapters import OpenDataHub
from ed_flow_intelligence.data_sources.registry import load_data_source_registry, registry_to_frame
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data
from ed_flow_intelligence.lineage import statuses_to_frame
from ed_flow_intelligence.operational_intelligence import executive_pressure_cockpit, research_capability_map


@st.cache_data(show_spinner=False)
def load_bundle() -> dict[str, object]:
    """Load synthetic/internal-ready rows and public fallback context."""

    config = KernelConfig()
    backend = create_local_backend(config.synthetic_data_dir)
    ensure_public_open_data(config.open_data_dir)
    registry = load_data_source_registry()
    hub = OpenDataHub(registry, config.open_data_dir)
    visits = backend.load_ed_visits(VisitFilters())
    active = backend.load_current_active_visits(VisitFilters())
    return {
        "config": config,
        "backend": backend,
        "visits": visits,
        "active": active,
        "public_data": hub.datasets(),
        "registry": registry_to_frame(registry),
        "refresh": statuses_to_frame(hub.status_rows()),
    }


def metric_card(label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style() -> None:
    st.markdown(
        """
        <style>
          .block-container {max-width: 1480px; padding-top: 1.1rem;}
          h1, h2, h3 {letter-spacing: 0;}
          .metric-card {border:1px solid #d7e2e5; border-left:5px solid #2f6f73; border-radius:8px; padding:.75rem .85rem; min-height:112px; background:white;}
          .metric-label {font-size:.76rem; color:#586875; text-transform:uppercase; font-weight:700;}
          .metric-value {font-size:1.45rem; color:#1f2933; font-weight:760;}
          .metric-caption {font-size:.86rem; color:#607080; margin-top:.35rem;}
          .boundary {border:1px solid #efc36a; border-left:5px solid #d99b2b; border-radius:8px; padding:.8rem; background:#fff9e8;}
          .method {border:1px solid #d7e2e5; border-radius:8px; padding:.8rem; background:#f5f7f8;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar(visits: pd.DataFrame) -> tuple[str, int, int]:
    st.sidebar.title("Action Intelligence")
    st.sidebar.caption("Separate branch/app. Synthetic local mode. No PHI.")
    facilities = sorted(visits["INSTITUTION_NAME"].dropna().unique().tolist())
    default = facilities.index("Stollery Children's Hospital") if "Stollery Children's Hospital" in facilities else 0
    facility = st.sidebar.selectbox("Facility", facilities, index=default)
    horizon = st.sidebar.slider("Planning horizon", 12, 96, 48, step=6)
    replications = st.sidebar.slider("Simulation replications", 10, 120, 40, step=10)
    st.sidebar.markdown("<div class='boundary'>Decision support only. This app does not automate clinical judgement.</div>", unsafe_allow_html=True)
    return facility, horizon, replications


def command_huddle_tab(bundle: dict[str, object], facility: str, horizon: int) -> None:
    visits = bundle["visits"]
    active = bundle["active"]
    public_data = bundle["public_data"]
    cockpit = executive_pressure_cockpit(visits, active, public_data, facility)
    metrics = cockpit["metrics"]
    cols = st.columns(4)
    for idx, row in metrics.head(8).iterrows():
        with cols[idx % 4]:
            metric_card(str(row["label"]), str(row["display_value"]), str(row["interpretation"]))
    st.subheader("Action Watchpoints")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**Watch first**")
        for item in cockpit["watchpoints"]:
            st.write(f"- {item}")
    with c2:
        st.markdown("**Operational levers to consider**")
        for item in cockpit["levers"]:
            st.write(f"- {item}")
    st.markdown(f"<div class='method'>{cockpit['why_pressure_moved']}</div>", unsafe_allow_html=True)
    forecast = external_pressure_forecast(public_data, facility, horizon_hours=horizon)
    if not forecast.hourly.empty:
        st.plotly_chart(
            px.line(forecast.hourly, x="timestamp", y=["p10_pressure", "p50_pressure", "p90_pressure"], title="External Pressure Forecast With Uncertainty"),
            width="stretch",
        )


def scenario_tab(bundle: dict[str, object], facility: str, horizon: int) -> None:
    st.subheader("Scenario-to-Action Huddle")
    c1, c2, c3 = st.columns(3)
    shocks = ScenarioShockConfig(
        respiratory_surge=c1.slider("Respiratory surge multiplier", 0.5, 3.0, 1.35, 0.05),
        smoke_event=c1.slider("Smoke/AQHI stress", 0.0, 1.0, 0.25, 0.05),
        traffic_disruption=c2.slider("Travel disruption", 0.0, 1.0, 0.2, 0.05),
        public_wait_deterioration_mins=c2.slider("Public wait deterioration", 0, 240, 45, 5),
        synthetic_capacity_constraint=c3.slider("Synthetic capacity constraint", 0.0, 1.0, 0.35, 0.05),
        school_reopening=c3.toggle("School reopening overlay", value=True),
    )
    result = combined_public_scenario(bundle["visits"], bundle["public_data"], facility, horizon, shocks)
    st.markdown("**Five-line capacity huddle brief**")
    for line in result["huddle"]:
        st.write(f"- {line}")
    st.dataframe(result["impact"], width="stretch", hide_index=True)
    st.dataframe(result["affected_stages"], width="stretch", hide_index=True)
    if not result["forecast"].empty:
        st.plotly_chart(px.line(result["forecast"], x="timestamp", y="p50_pressure", color="scenario", title="Baseline vs Combined Public Stress"), width="stretch")


def simulation_tab(bundle: dict[str, object], facility: str, horizon: int, replications: int) -> None:
    st.subheader("Simulation and Bottleneck Migration")
    c1, c2, c3 = st.columns(3)
    scenario = ScenarioConfig(
        facility=facility,
        horizon_hours=horizon,
        replications=replications,
        arrival_surge_multiplier=c1.slider("Arrival surge multiplier", 0.75, 2.25, 1.15, 0.05),
        triage_capacity_delta=c1.number_input("Triage capacity delta", -3, 6, 0),
        physician_capacity_delta=c2.number_input("Physician capacity delta", -3, 6, 1),
        rooming_capacity_delta=c2.number_input("Rooming capacity delta", -8, 12, 2),
        fast_track_enabled=c3.toggle("Fast-track CTAS 4/5", value=True),
        consult_turnaround_improvement=c3.slider("Consult turnaround improvement", 0.0, 0.75, 0.15, 0.05),
        diagnostic_turnaround_improvement=c3.slider("Diagnostic turnaround improvement", 0.0, 0.75, 0.1, 0.05),
        boarding_reduction=c3.slider("Boarding reduction", 0.0, 0.8, 0.15, 0.05),
    )
    result = enhanced_simulation(bundle["visits"], scenario)
    st.markdown("**Simulation huddle brief**")
    for line in result["huddle"]:
        st.write(f"- {line}")
    st.dataframe(result["uncertainty"], width="stretch", hide_index=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(result["utilization"], x="resource_pool", y="utilization_index", color="status", title="Resource Utilization Index"), width="stretch")
    with right:
        st.plotly_chart(px.line(result["occupancy"], x="hour", y=["waiting_room", "roomed_not_seen", "diagnostics_consults", "boarding"], title="Stage Occupancy Over Time"), width="stretch")
    st.dataframe(result["migration"], width="stretch", hide_index=True)
    st.caption(f"Example LWBS hazard, CTAS 4 after 3h wait and 0.7 crowding: {lwbs_hazard(3, 0.7, 4):.1%}")


def snowflake_tab(bundle: dict[str, object]) -> None:
    st.subheader("Snowflake Activation Workbench")
    contract = TbEdVisitsContract()
    st.markdown("**Day-one constrained table**")
    st.json(
        {
            "table": contract.table_name,
            "grain": contract.grain,
            "primary_key": contract.primary_key,
            "primary_timestamp": contract.primary_start_timestamp,
            "default_rules": contract.default_rules,
            "sensitive_fields_excluded_from_public_artifacts": contract.sensitive_columns,
        }
    )
    targets = internal_ready_targets(bundle["visits"], bundle["public_data"], "Stollery Children's Hospital")
    st.dataframe(targets, width="stretch", hide_index=True)
    st.markdown("**Activation sequence**")
    st.write("1. Confirm governed access to TB_ED_VISITS and semantic chart-review views.")
    st.write("2. Build OPEN_DATA ingestion and refresh logs in Snowflake.")
    st.write("3. Calibrate forecast/simulation models by facility and date holdout.")
    st.write("4. Validate identifier mapping in secure runtime before chart-review workflows.")
    st.write("5. Pilot with human-in-the-loop operational huddles and audit logging.")


def lineage_tab(bundle: dict[str, object]) -> None:
    st.subheader("Lineage, Trust, and Research Traceability")
    st.dataframe(bundle["refresh"], width="stretch", hide_index=True, height=340)
    st.dataframe(research_capability_map(), width="stretch", hide_index=True)
    features = site_hour_public_features(bundle["public_data"], "Stollery Children's Hospital")
    st.markdown("**Model validation preview**")
    forecast = external_pressure_forecast(bundle["public_data"], "Stollery Children's Hospital")
    st.dataframe(forecast.validation, width="stretch", hide_index=True)
    st.caption(f"Feature rows available for local public/synthetic validation: {len(features)}")


def main() -> None:
    st.set_page_config(page_title=ACTION_APP_NAME, page_icon="AHS", layout="wide")
    style()
    bundle = load_bundle()
    facility, horizon, replications = sidebar(bundle["visits"])
    st.title(ACTION_APP_NAME)
    st.caption("A separate Snowflake-portable operational huddle app powered by the shared ED Flow capability kernel. Synthetic local mode only.")
    tabs = st.tabs(["Command Huddle", "Scenario Actions", "Simulation", "Snowflake Activation", "Lineage & Validation"])
    with tabs[0]:
        command_huddle_tab(bundle, facility, horizon)
    with tabs[1]:
        scenario_tab(bundle, facility, horizon)
    with tabs[2]:
        simulation_tab(bundle, facility, horizon, replications)
    with tabs[3]:
        snowflake_tab(bundle)
    with tabs[4]:
        lineage_tab(bundle)


if __name__ == "__main__":
    main()

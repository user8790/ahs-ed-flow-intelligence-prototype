"""Streamlit application for the AHS ED flow intelligence prototype."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from ed_flow.ai_layer import get_model_client
from ed_flow.chart_review import summarize_chart_context
from ed_flow.config import AppConfig, get_config
from ed_flow.data_contracts import VisitFilters, ScenarioConfig, constrained_projection
from ed_flow.event_log import construct_event_log, observed_concurrency, reconstruct_stage_intervals
from ed_flow.feature_engineering import (
    add_flow_features,
    arrival_patterns,
    estimate_baseline_parameters,
    route_probabilities,
    stage_duration_distributions,
)
from ed_flow.forecasting import hourly_arrival_forecast, next_constraint_forecast
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


PEDIATRIC_AGE_GROUPS = ["Newborn", "Neonate", "Paediatric"]


def configure_page() -> None:
    st.set_page_config(
        page_title="AHS ED Flow Intelligence Prototype",
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
        .block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
        h1, h2, h3 {letter-spacing: 0;}
        .metric-card {
            border: 1px solid var(--ed-line);
            border-left: 5px solid var(--ed-teal);
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
            background: #ffffff;
            min-height: 94px;
        }
        .metric-label {font-size: 0.78rem; color: var(--ed-muted); text-transform: uppercase;}
        .metric-value {font-size: 1.55rem; font-weight: 720; color: var(--ed-ink);}
        .method-note {
            border: 1px solid var(--ed-line);
            border-radius: 8px;
            background: var(--ed-band);
            padding: 0.7rem 0.85rem;
            color: var(--ed-ink);
            font-size: 0.92rem;
        }
        .warning-note {
            border: 1px solid #efc36a;
            border-left: 5px solid var(--ed-amber);
            border-radius: 8px;
            background: #fff8e8;
            padding: 0.75rem 0.85rem;
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
        div[data-testid="stMetricValue"] {font-size: 1.45rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_backend(data_dir: str) -> LocalBackend:
    ensure_synthetic_data(Path(data_dir))
    return LocalBackend(Path(data_dir))


@st.cache_data(show_spinner=False)
def load_data(data_dir: str) -> dict[str, pd.DataFrame]:
    backend = LocalBackend(Path(data_dir))
    all_visits = backend.load_ed_visits(VisitFilters(include_invalid_los=True, include_scheduled=True))
    filtered_visits = backend.load_ed_visits(VisitFilters())
    active = backend.load_current_active_visits(VisitFilters())
    expanded_events = backend.load_expanded_flow_events()
    capacity = backend.load_beds_staffing_diagnostics()
    return {
        "all_visits": all_visits,
        "visits": filtered_visits,
        "active": active,
        "expanded_events": expanded_events,
        "capacity": capacity,
    }


def sidebar_controls(config: AppConfig, visits: pd.DataFrame) -> tuple[str, bool, int]:
    st.sidebar.title("ED Flow Prototype")
    st.sidebar.caption("Synthetic local mode. No PHI. Snowflake-ready adapter design.")
    facilities = sorted(visits["INSTITUTION_NAME"].dropna().unique().tolist())
    default_index = facilities.index(config.default_facility) if config.default_facility in facilities else 0
    facility = st.sidebar.selectbox(
        "Facility",
        facilities,
        index=default_index,
        help="Filters the synthetic operational and constrained-data views.",
    )
    pediatric_only = st.sidebar.toggle(
        "Pediatric focus",
        value=config.default_pediatric_only,
        help="Uses Newborn, Neonate, and Paediatric age groups where supported by synthetic data.",
    )
    horizon_hours = st.sidebar.slider(
        "Default horizon (hours)",
        min_value=6,
        max_value=72,
        value=24,
        step=6,
        help="Used for arrival forecasts and simulation defaults.",
    )
    st.sidebar.markdown(
        "<div class='method-note'>This prototype supports operational decision-making. It does not automate clinical judgement.</div>",
        unsafe_allow_html=True,
    )
    return facility, pediatric_only, horizon_hours


def filtered_view(visits: pd.DataFrame, active: pd.DataFrame, facility: str, pediatric_only: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    visit_view = visits[visits["INSTITUTION_NAME"] == facility].copy()
    active_view = active[active["facility"] == facility].copy() if "facility" in active.columns else pd.DataFrame()
    if pediatric_only:
        visit_view = visit_view[visit_view["PATIENT_AGE_GROUP"].isin(PEDIATRIC_AGE_GROUPS)]
        if "age_group" in active_view.columns:
            active_view = active_view[active_view["age_group"].isin(PEDIATRIC_AGE_GROUPS)]
    return visit_view.reset_index(drop=True), active_view.reset_index(drop=True)


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    tooltip = f" title='{help_text}'" if help_text else ""
    st.markdown(
        f"<div class='metric-card'{tooltip}><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def pct(value: float | int) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return "n/a"


def executive_tab(visits: pd.DataFrame, active: pd.DataFrame, all_visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("Executive Command Centre")
    visit_view, active_view = filtered_view(visits, active, facility, pediatric_only)
    quality = calculate_data_quality(all_visits[all_visits["INSTITUTION_NAME"] == facility])
    freshness = quality.max_row_update_datetime.isoformat(timespec="minutes") if quality.max_row_update_datetime else "unknown"
    st.markdown(
        f"<div class='warning-note'><b>Data quality and freshness:</b> {quality.row_count} synthetic rows loaded; latest row update {freshness}. "
        f"{' '.join(quality.warnings[:2])}</div>",
        unsafe_allow_html=True,
    )

    start = visit_view["FIRST_CONTACT_DATETIME"].min() if not visit_view.empty else None
    end = visit_view["FIRST_CONTACT_DATETIME"].max() if not visit_view.empty else None
    col_a, col_b, col_c = st.columns([1.5, 1, 1])
    col_a.write(f"Facility: **{facility}**")
    col_b.write(f"Population: **{'Pediatric' if pediatric_only else 'All ages'}**")
    col_c.write(f"Horizon: **{horizon_hours}h**")
    if start is not None and end is not None:
        st.caption(f"Historical synthetic window for selected view: {start:%Y-%m-%d} to {end:%Y-%m-%d}")

    metrics = current_state_metrics(active_view, visit_view)
    metric_items = [
        ("Arrivals", f"{metrics['arrivals']:,}", "Selected historical synthetic arrivals after default rules."),
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
    ]
    for idx in range(0, len(metric_items), 4):
        cols = st.columns(4)
        for col, item in zip(cols, metric_items[idx : idx + 4]):
            with col:
                metric_card(*item)

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("**Current Simulated ED State**")
        if active_view.empty:
            st.info("No active synthetic patients match this filter.")
        else:
            stage_counts = active_view["current_stage"].value_counts().rename_axis("stage").reset_index(name="patients")
            st.plotly_chart(metric_bar(stage_counts, "stage", "patients", title="Active patients by stage"), use_container_width=True)
    with right:
        st.markdown("**Bottleneck Summary**")
        st.dataframe(bottleneck_summary(active_view, visit_view), use_container_width=True, hide_index=True)

    forecast = hourly_arrival_forecast(visit_view, horizon_hours=horizon_hours)
    st.plotly_chart(line_chart(forecast, "hour_ahead", "expected_arrivals", title="Empirical arrival forecast"), use_container_width=True)
    st.markdown(
        "<div class='method-note'>Method note: current-state counts come from the synthetic waiting-room registry; historical metrics apply default business rules excluding invalid LOS and scheduled visits.</div>",
        unsafe_allow_html=True,
    )


def waiting_room_tab(backend: LocalBackend, active: pd.DataFrame, facility: str, pediatric_only: bool, config: AppConfig) -> None:
    st.subheader("Waiting Room MRN Chart Summaries")
    st.markdown(
        "<div class='warning-note'>Synthetic chart summarization aid only. It is not a substitute for chart review, clinical assessment, or source-system verification.</div>",
        unsafe_allow_html=True,
    )
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
            if mrn not in st.session_state.selected_mrns:
                st.session_state.selected_mrns.append(mrn)

    remove_options = st.session_state.selected_mrns.copy()
    col_remove, col_button = st.columns([2, 1])
    remove_mrn = col_remove.selectbox("Remove MRN", remove_options or ["No selected MRNs"], disabled=not remove_options)
    if col_button.button("Remove selected", disabled=not remove_options):
        st.session_state.selected_mrns = [m for m in st.session_state.selected_mrns if m != remove_mrn]
        st.rerun()

    left, right = st.columns([0.85, 1.6])
    with left:
        st.markdown("**Scrollable waiting-room list**")
        list_cols = ["mrn", "triage_level", "age_group", "presenting_complaint", "current_stage", "lwbs_risk"]
        sorted_active = active_view.sort_values(["triage_level", "arrival_datetime"]) if "arrival_datetime" in active_view else active_view
        st.dataframe(sorted_active[list_cols], use_container_width=True, hide_index=True, height=520)
    with right:
        model_client = get_model_client(config)
        if not st.session_state.selected_mrns:
            st.info("Add a synthetic MRN to view chart context.")
        for mrn in st.session_state.selected_mrns:
            context = backend.load_chart_context_by_mrn(mrn)
            summary = summarize_chart_context(context, model_client)
            demographics = context.demographics
            st.markdown("<div class='patient-card'>", unsafe_allow_html=True)
            top_cols = st.columns([1.4, 1, 0.8])
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


def constrained_tab(visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("Constrained ED Curated Data Module")
    st.caption("This module uses only fields available in the `TB_ED_VISITS` data contract.")
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    constrained = constrained_projection(visit_view)
    featured = add_flow_features(constrained)
    if constrained.empty:
        st.info("No visits match this constrained filter.")
        return

    tabs = st.tabs(["Explorer", "Event Log", "Patterns", "Parameters", "Replay Validation"])
    with tabs[0]:
        st.markdown("**Historical flow explorer**")
        cols = ["DATA_RECORD_ID", "DEPARTMENT_TYPE", "TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "PRESENTING_COMPLAINT", "DISPOSITION_GROUP", "ED_LOS_HRS"]
        st.dataframe(constrained[[c for c in cols if c in constrained]].head(300), use_container_width=True, hide_index=True, height=320)
        st.plotly_chart(duration_distribution(featured, "ED_LOS_HRS", color="DISPOSITION_GROUP", title="ED LOS distribution"), use_container_width=True)
    with tabs[1]:
        event_log = construct_event_log(constrained)
        intervals = reconstruct_stage_intervals(constrained)
        concurrency = observed_concurrency(intervals)
        col1, col2 = st.columns(2)
        col1.dataframe(event_log.head(400), use_container_width=True, hide_index=True, height=350)
        col2.dataframe(intervals.head(400), use_container_width=True, hide_index=True, height=350)
        if not concurrency.empty:
            stage_hour = concurrency.groupby(["stage", "timestamp"], as_index=False)["concurrency"].sum()
            st.plotly_chart(line_chart(stage_hour, "timestamp", "concurrency", color="stage", title="Observed concurrency by reconstructed stage"), use_container_width=True)
    with tabs[2]:
        st.markdown("**Arrival, route, consult, and boarding patterns**")
        arrivals = arrival_patterns(constrained)
        top_arrivals = arrivals.groupby(["arrival_hour"], as_index=False)["arrivals"].sum()
        st.plotly_chart(metric_bar(top_arrivals, "arrival_hour", "arrivals", title="Arrivals by hour"), use_container_width=True)
        left, right = st.columns(2)
        left.dataframe(route_probabilities(constrained).head(80), use_container_width=True, hide_index=True)
        duration_summary = stage_duration_distributions(constrained)
        right.dataframe(duration_summary, use_container_width=True, hide_index=True)
        consult_rate = (pd.to_numeric(constrained["CONSULT_COUNT"], errors="coerce").fillna(0) > 0).mean()
        boarding = pd.to_numeric(constrained["ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS"], errors="coerce").dropna()
        st.write(f"Consult probability: **{consult_rate:.1%}** | Median boarding delay when present: **{boarding.median() if not boarding.empty else 0:.1f}h**")
    with tabs[3]:
        params = estimate_baseline_parameters(constrained)
        st.json(params, expanded=False)
        st.markdown(
            "<div class='method-note'>Capacity defaults are inferred from observed flow rates and duration distributions, then made explicit so they can be replaced by validated staffing, room, and bed feeds in Snowflake.</div>",
            unsafe_allow_html=True,
        )
    with tabs[4]:
        scenario = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=10)
        output = run_simulation(constrained, scenario)
        comparison = validation_metric_summary(constrained, output.patients)
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        st.plotly_chart(uncertainty_interval_chart(summarize_with_uncertainty(output.summary)), use_container_width=True)


def simulation_tab(visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int, config: AppConfig) -> None:
    st.subheader("Simulation Lab")
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    if visit_view.empty:
        st.info("No visits match this simulation filter.")
        return

    controls, results = st.columns([0.9, 1.7])
    with controls:
        st.markdown("**Scenario Controls**")
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
        reps = st.number_input("Monte Carlo replications", 10, 100, 10, 5)
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
    output = run_simulation(visit_view, scenario)
    uncertainty = summarize_with_uncertainty(output.summary)
    with results:
        st.markdown("**Scenario Results with Uncertainty**")
        st.plotly_chart(uncertainty_interval_chart(uncertainty), use_container_width=True)
        st.dataframe(uncertainty, use_container_width=True, hide_index=True)
        queue_avg = output.queue_lengths.groupby("hour", as_index=False)[["waiting_for_physician", "boarding", "total_active_pressure"]].mean()
        st.plotly_chart(line_chart(queue_avg, "hour", "total_active_pressure", title="Expected active pressure over time"), use_container_width=True)

    baseline = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=int(reps), random_seed=int(seed))
    fast = baseline.model_copy(update={"fast_track_enabled": True})
    bed = baseline.model_copy(update={"boarding_reduction": 0.25, "admission_bed_improvement": 0.2})
    staffing = baseline.model_copy(update={"physician_capacity_delta": 1, "triage_capacity_delta": 1})
    comparison = compare_scenarios(visit_view, [baseline, scenario, fast, bed, staffing])
    ranked = rank_interventions(comparison)
    left, right = st.columns(2)
    left.markdown("**Scenario comparison table**")
    left.dataframe(comparison, use_container_width=True, hide_index=True)
    right.markdown("**Bottleneck shift analysis**")
    right.dataframe(output.bottlenecks, use_container_width=True, hide_index=True)
    st.markdown("**Prioritized interventions**")
    st.dataframe(ranked, use_container_width=True, hide_index=True)
    explanation = get_model_client(config).explain_scenario(comparison)
    st.markdown(
        f"<div class='method-note'><b>Practical interpretation:</b> {practical_interpretation(comparison)} {explanation}</div>",
        unsafe_allow_html=True,
    )


def expanded_tab(data: dict[str, pd.DataFrame], visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("Expanded System Intelligence Module")
    st.markdown(
        "<div class='warning-note'>Expanded module is assumption-based and synthetic. It demonstrates future AHS-curated Snowflake feeds, not current operational truth.</div>",
        unsafe_allow_html=True,
    )
    active = data["active"][data["active"]["facility"] == facility].copy()
    if pediatric_only:
        active = active[active["age_group"].isin(PEDIATRIC_AGE_GROUPS)]
    events = data["expanded_events"][data["expanded_events"]["facility"] == facility].copy()
    capacity = data["capacity"][data["capacity"]["facility"] == facility].copy()
    visit_view, _ = filtered_view(visits, active, facility, pediatric_only)

    top = st.columns(4)
    latest_capacity = capacity.sort_values("snapshot_datetime").tail(1)
    top[0].metric("Active synthetic patients", len(active))
    top[1].metric("Inpatient beds available", int(latest_capacity["inpatient_available_beds"].iloc[0]) if not latest_capacity.empty else 0)
    top[2].metric("Pending discharges", int(latest_capacity["pending_discharges"].iloc[0]) if not latest_capacity.empty else 0)
    top[3].metric("Consult queue", int(latest_capacity["consult_queue"].iloc[0]) if not latest_capacity.empty else 0)

    tabs = st.tabs(["Digital Twin", "Bed Placement", "Staffing", "Cascades & Transfers", "Next Constraint"])
    with tabs[0]:
        st.dataframe(active.sort_values(["triage_level", "arrival_datetime"]), use_container_width=True, hide_index=True, height=320)
        event_counts = events["event_type"].value_counts().rename_axis("event_type").reset_index(name="events")
        st.plotly_chart(metric_bar(event_counts, "event_type", "events", title="Synthetic real-time operational events"), use_container_width=True)
    with tabs[1]:
        st.dataframe(greedy_bed_placement_optimizer(active, capacity), use_container_width=True, hide_index=True)
        st.markdown("<div class='method-note'>Optimizer objective: reduce ED boarding hours while respecting synthetic bed availability and priority signals. Future pilot should add isolation, specialty, team, age, and unit constraints.</div>", unsafe_allow_html=True)
    with tabs[2]:
        st.dataframe(staffing_sensitivity(active, capacity), use_container_width=True, hide_index=True)
        st.plotly_chart(line_chart(capacity, "snapshot_datetime", "physicians_on_shift", title="Synthetic physician staffing forecast"), use_container_width=True)
    with tabs[3]:
        cascade_cols = ["snapshot_datetime", "pending_discharges", "beds_cleaning", "inpatient_available_beds", "transfer_requests_waiting"]
        st.dataframe(capacity[cascade_cols].head(48), use_container_width=True, hide_index=True)
        transfer_events = events[events["event_type"].str.contains("transport|bed", case=False, regex=True)]
        st.plotly_chart(metric_bar(transfer_events.groupby("event_type").size().reset_index(name="events"), "event_type", "events", title="Bed/transport event mix"), use_container_width=True)
    with tabs[4]:
        next_constraints = next_constraint_forecast(active, visit_view)
        st.dataframe(next_constraints, use_container_width=True, hide_index=True)
        baseline = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=10)
        interventions = compare_scenarios(
            visit_view,
            [
                baseline,
                baseline.model_copy(update={"boarding_reduction": 0.25}),
                baseline.model_copy(update={"physician_capacity_delta": 1}),
                baseline.model_copy(update={"fast_track_enabled": True}),
            ],
        )
        st.dataframe(rank_interventions(interventions), use_container_width=True, hide_index=True)


def validation_tab(visits: pd.DataFrame, facility: str, pediatric_only: bool, horizon_hours: int) -> None:
    st.subheader("Validation & Governance")
    visit_view, _ = filtered_view(visits, pd.DataFrame(), facility, pediatric_only)
    if visit_view.empty:
        st.info("No visits match this validation filter.")
        return
    summary = governance_summary(visit_view)
    quality = summary["data_quality"]
    st.markdown(
        f"<div class='warning-note'><b>Governance frame:</b> {quality.row_count} rows in selected validation view. "
        "Human-in-the-loop review is required before operational use.</div>",
        unsafe_allow_html=True,
    )
    train, holdout = holdout_split_by_date(visit_view)
    scenario = ScenarioConfig(facility=facility, horizon_hours=horizon_hours, replications=10)
    simulation = run_simulation(holdout if not holdout.empty else visit_view, scenario)
    st.markdown("**Holdout validation by date**")
    st.write(f"Training rows: **{len(train):,}** | Holdout rows: **{len(holdout):,}**")
    st.dataframe(validation_metric_summary(holdout if not holdout.empty else visit_view, simulation.patients), use_container_width=True, hide_index=True)

    tabs = st.tabs(["Calibration", "Durations", "Data Quality", "Drift", "Controls"])
    with tabs[0]:
        st.dataframe(summary["facility_calibration"], use_container_width=True, hide_index=True)
        st.dataframe(summary["admission_calibration"], use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(stage_duration_distributions(visit_view), use_container_width=True, hide_index=True)
        st.plotly_chart(duration_distribution(add_flow_features(visit_view), "ED_LOS_HRS", color="DISPOSITION_GROUP", title="Observed LOS by disposition"), use_container_width=True)
    with tabs[2]:
        st.dataframe(summary["missing_timestamps"], use_container_width=True, hide_index=True)
        st.write(quality.warnings)
    with tabs[3]:
        st.dataframe(summary["drift"], use_container_width=True, hide_index=True)
    with tabs[4]:
        st.markdown("**Explainability summaries**")
        for item in summary["explainability"]:
            st.write(f"- {item}")
        st.markdown("**Audit log design**")
        for item in summary["audit_log_design"]:
            st.write(f"- {item}")
        st.markdown(
            "<div class='method-note'>Privacy/security note: local prototype uses synthetic identifiers only. Snowflake pilot must enforce role-based access, PHI minimization, model-call controls, and audit logging.</div>",
            unsafe_allow_html=True,
        )


def snowflake_transfer_tab(config: AppConfig) -> None:
    st.subheader("Snowflake Transfer Readiness")
    st.markdown(
        """
        **Local to Snowflake architecture**

        `Synthetic CSVs -> LocalBackend -> pandas analytics -> Streamlit app`

        `TB_ED_VISITS / semantic views -> Snowpark Session -> SnowflakeBackend -> same contracts -> Streamlit in Snowflake`

        `Mock/OpenAI/Snowflake model clients -> controlled AI layer -> chart summaries and scenario explanations only`
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Snowflake config targets**")
        st.json(
            {
                "database": config.snowflake_database,
                "schema": config.snowflake_schema,
                "warehouse": config.snowflake_warehouse,
                "active_session": "snowflake.snowpark.context.get_active_session() inside Streamlit in Snowflake",
                "local_fallback": "Environment variables for account/user/role/warehouse/database/schema",
            }
        )
        st.markdown("**Package compatibility notes**")
        st.write(
            "Core code uses pandas, numpy, scipy/scikit-learn for interpretable models, pydantic for contracts, "
            "plotly/Streamlit for display, and an isolated Snowpark adapter. SimPy is optional because the local "
            "simulation engine has a portable fallback."
        )
    with col2:
        checklist = pd.DataFrame(
            [
                ("Validate PATIENT_CHART to PAT_MRN_ID mapping", "Required before chart-review pilot"),
                ("Create governed secure views", "Minimize columns and enforce row-level access"),
                ("Replace CSV backend with SnowflakeBackend", "No app contract changes expected"),
                ("Calibrate facility parameters", "Use holdout by date and facility-level review"),
                ("Approve model provider", "Mock, no model, Snowflake-native, or approved OpenAI path"),
                ("Implement audit table", "Persist scenario inputs, data versions, seeds, prompts, outputs"),
                ("Run privacy/security review", "PHI handling, identifiers, retention, access, logging"),
            ],
            columns=["Step", "Readiness note"],
        )
        st.markdown("**Prototype to governed pilot checklist**")
        st.dataframe(checklist, use_container_width=True, hide_index=True)

    st.markdown("**`TB_ED_VISITS` extraction SQL template**")
    st.code(build_ed_visits_sql(), language="sql")
    st.markdown("**Recent and active-visit SQL templates**")
    st.code(build_recent_ed_visits_sql(), language="sql")
    st.code(build_active_visits_sql(), language="sql")
    st.markdown("**Chart-review semantic view SQL templates**")
    templates = build_chart_context_sql(config.snowflake_database, config.snowflake_schema)
    selected = st.selectbox("Semantic view template", sorted(templates))
    st.code(templates[selected], language="sql")
    st.markdown(
        """
        **Secure handling of PHI and identifiers**

        The local prototype contains only synthetic identifiers. In Snowflake, PATIENT_CHART, PAT_MRN_ID, PHN, ULI,
        birthdate, postal code, note text, and patient ID fields must remain in governed views with least-privilege
        role grants. External model calls should be disabled unless approved for the exact data class and audited.
        """
    )


def main() -> None:
    configure_page()
    config = get_config()
    backend = get_backend(str(config.data_dir))
    data = load_data(str(config.data_dir))
    visits = data["visits"]
    all_visits = data["all_visits"]
    active = data["active"]
    facility, pediatric_only, horizon_hours = sidebar_controls(config, visits)

    st.title("AHS ED Flow Intelligence Prototype")
    st.caption("Synthetic, Snowflake-portable pediatric and provincial ED operations simulation and intelligence prototype.")

    tabs = st.tabs(
        [
            "Executive Command Centre",
            "Waiting Room MRN Chart Summaries",
            "Constrained ED Curated Data Module",
            "Simulation Lab",
            "Expanded System Intelligence Module",
            "Validation & Governance",
            "Snowflake Transfer Readiness",
        ]
    )
    with tabs[0]:
        executive_tab(visits, active, all_visits, facility, pediatric_only, horizon_hours)
    with tabs[1]:
        waiting_room_tab(backend, active, facility, pediatric_only, config)
    with tabs[2]:
        constrained_tab(visits, facility, pediatric_only, horizon_hours)
    with tabs[3]:
        simulation_tab(visits, facility, pediatric_only, horizon_hours, config)
    with tabs[4]:
        expanded_tab(data, visits, facility, pediatric_only, horizon_hours)
    with tabs[5]:
        validation_tab(visits, facility, pediatric_only, horizon_hours)
    with tabs[6]:
        snowflake_transfer_tab(config)


if __name__ == "__main__":
    main()

"""Operational interpretation helpers for cockpit, scenarios, and research traceability."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ed_flow.metrics import current_state_metrics
from ed_flow_intelligence.forecasting import public_pressure_index


def executive_pressure_cockpit(
    visits: pd.DataFrame,
    active: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
) -> dict[str, pd.DataFrame | list[str] | str]:
    """Build executive-facing pressure metrics, rankings, drivers, watch-points, and levers."""

    pressure = public_pressure_index(public_data)
    site = pressure[pressure["facility"] == facility].copy() if not pressure.empty else pd.DataFrame()
    active_view = active[active.get("facility", pd.Series(dtype=str)) == facility].copy() if not active.empty else active
    visit_view = visits[visits.get("INSTITUTION_NAME", pd.Series(dtype=str)) == facility].copy() if not visits.empty else visits
    state = current_state_metrics(active_view, visit_view)
    province_score = float(pressure["public_pressure_index"].mean()) if not pressure.empty else 0.0
    site_score = float(site["public_pressure_index"].iloc[0]) if not site.empty else province_score
    pediatric_score = _pediatric_pressure(public_data, facility)
    respiratory_score = _respiratory_score(public_data, facility)
    environmental_score = float(site["environmental_stress_index"].iloc[0]) if not site.empty and "environmental_stress_index" in site else 0.0
    travel_score = float(site["travel_friction_index"].iloc[0]) if not site.empty and "travel_friction_index" in site else 0.0
    posted_wait = float(site["estimated_wait_mins"].iloc[0]) if not site.empty and "estimated_wait_mins" in site else 0.0
    metrics = pd.DataFrame(
        [
            _metric("Alberta-wide pressure", province_score, "+", "moderate", "HYBRID_OPEN_SYNTHETIC", "Province-level external stress context; not internal wait-time truth."),
            _metric("Selected site pressure", site_score, "+", "moderate", "HYBRID_OPEN_SYNTHETIC", "Best current public/synthetic site pressure signal."),
            _metric("Pediatric pressure", pediatric_score, "+", "moderate", "HYBRID_OPEN_SYNTHETIC", "Pediatric site and respiratory context weighted pressure."),
            _metric("Respiratory surge", respiratory_score, "+", "moderate", "OPEN_DATA", "RSV/influenza/COVID/syndromic synthetic-public composite."),
            _metric("Smoke/heat/weather stress", environmental_score, "flat", "moderate", "HYBRID_OPEN_SYNTHETIC", "AQHI, smoke, heat/cold, wildfire and weather-alert fallback signal."),
            _metric("Travel/access friction", travel_score, "flat", "moderate", "HYBRID_OPEN_SYNTHETIC", "Road, traffic, transit, event and weather access friction proxy."),
            _metric("Public wait-time signal", posted_wait, "+", "moderate", "HYBRID_OPEN_SYNTHETIC", "Synthetic fallback shaped like public posted wait-time signal."),
            _metric("Internal/synthetic flow state", float(state["median_ed_los"]), "flat", "wide", "SYNTHETIC_DATA", "Synthetic TB_ED_VISITS-shaped operational preview."),
        ]
    )
    metrics["display_value"] = metrics.apply(_display_value, axis=1)
    zone_rank = (
        pressure.groupby("zone", as_index=False)
        .agg(public_pressure_index=("public_pressure_index", "mean"), sites=("facility", "nunique"))
        .sort_values("public_pressure_index", ascending=False)
        if not pressure.empty
        else pd.DataFrame()
    )
    changed = what_changed_panel(public_data, facility)
    watchpoints = top_watchpoints(metrics, state)
    levers = top_operational_levers(metrics, state)
    why = why_pressure_moved(metrics)
    return {
        "metrics": metrics,
        "site_ranking": pressure,
        "zone_ranking": zone_rank,
        "what_changed": changed,
        "watchpoints": watchpoints,
        "levers": levers,
        "why_pressure_moved": why,
    }


def research_capability_map() -> pd.DataFrame:
    """Map research insights to implemented app capabilities and assets."""

    rows = [
        ("Public-data external-pressure forecasting", "Hybrid Forecasting Lab", "modeling.forecast_external_pressure", "data/open/*.csv", "Public prototype"),
        ("Pediatric respiratory surge modelling", "Pediatric Respiratory Surge", "respiratory scenario controls", "respiratory_surveillance.csv", "Public prototype"),
        ("Weather, smoke, AQHI, wildfire, and heat stress", "Smoke, Heat, Weather & Air Quality Stress", "environmental stress scenario", "environmental_stress.csv", "Public prototype"),
        ("Travel-friction proxy", "Travel Friction & Access Disruption", "travel scenario controls", "travel_friction.csv", "Public prototype"),
        ("Scenario workbench combining shocks", "Public Scenario Workbench", "run_combined_public_scenario", "public + synthetic capacity", "Public prototype"),
        ("Probabilistic forecasting intervals", "Hybrid Forecasting Lab", "P10/P50/P90 ensemble forecast", "model validation holdout", "Public prototype"),
        ("Forecast-to-simulation pipeline", "Simulation Lab", "external pressure multiplier into ScenarioConfig", "synthetic TB_ED_VISITS", "Day-one Snowflake ready"),
        ("Lightweight queue simulation", "Simulation Lab", "run_enhanced_simulation_summary", "simulation_feature_tables.sql", "Day-one Snowflake ready"),
        ("Internal-state boundary", "Snowflake Porting", "lineage and activation status", "TB_ED_VISITS + semantic views", "Snowflake"),
        ("Validation discipline", "Model Validation", "rolling_origin_backtest and validation metrics", "holdout synthetic/public data", "Day-one Snowflake ready"),
        ("Operational interpretation", "Executive/Scenario/Simulation tabs", "watchpoints, levers, huddle brief", "computed outputs", "Public and Snowflake"),
    ]
    return pd.DataFrame(rows, columns=["research_insight", "implemented_capability", "module_or_component", "data_asset_or_chart", "capability_tier"])


def deterministic_huddle_brief(
    title: str,
    impact: pd.DataFrame,
    watchpoints: list[str],
    levers: list[str],
    confidence: str = "moderate",
) -> list[str]:
    """Create a deterministic five-line operational huddle brief."""

    if impact.empty:
        delta = "No numeric scenario delta was computed."
    else:
        top = impact.iloc[0]
        delta = f"{top.get('metric', top.get('target', 'primary metric'))}: {top.get('change_label', top.get('scenario_delta', 'changed'))}."
    return [
        f"{title}: expected operational pressure is {confidence} confidence.",
        delta,
        f"Watch first: {watchpoints[0] if watchpoints else 'front-end queue and boarding signals'}.",
        f"Consider lever: {levers[0] if levers else 'match added capacity to the first binding constraint'}.",
        "Check internal data, staffing state, bed board, and clinical context before acting.",
    ]


def scenario_impact_cards(baseline: pd.DataFrame, scenario: pd.DataFrame) -> pd.DataFrame:
    """Return baseline-versus-scenario impact rows."""

    common = [c for c in ["expected_arrivals", "public_pressure_index", "expected_pia_wait_mins", "expected_lwbs_risk"] if c in baseline and c in scenario]
    rows = []
    for metric in common:
        base = float(baseline[metric].iloc[0])
        scen = float(scenario[metric].iloc[0])
        rows.append(
            {
                "metric": metric,
                "baseline": base,
                "scenario": scen,
                "scenario_delta": scen - base,
                "change_label": f"{scen - base:+.2f}",
                "operational_interpretation": _impact_interpretation(metric, scen - base),
            }
        )
    return pd.DataFrame(rows).sort_values("scenario_delta", ascending=False)


def pressure_to_action_translator(bottleneck: str, pressure_context: str) -> list[str]:
    """Translate pressure and bottleneck outputs into operational questions."""

    mapping = {
        "Rooming wait": "If rooming is binding, check room turnover, fast-track eligibility, cohorting options, and inpatient boarding spillback.",
        "Physician initial assessment": "If physician utilization is high, added triage capacity may move queues downstream unless PIA capacity shifts too.",
        "Boarding": "If boarding dominates, front-end changes may have limited LOS effect unless inpatient bed release improves.",
        "Consult delay": "If consult delay binds, check specialty queue age, decision thresholds, and escalation pathways.",
        "Diagnostics": "If diagnostics bind, check imaging/lab turnaround and whether rapid pathway criteria are clear.",
    }
    return [
        mapping.get(bottleneck, "Check whether the proposed lever addresses the first binding constraint."),
        f"Pressure context: {pressure_context}.",
        "Validate with internal current-state feeds before changing workflow.",
    ]


def _metric(label: str, value: float, trend: str, confidence: str, lineage: str, interpretation: str) -> dict[str, object]:
    return {
        "label": label,
        "value": float(value) if pd.notna(value) else 0.0,
        "trend": trend,
        "confidence": confidence,
        "lineage": lineage,
        "interpretation": interpretation,
    }


def _display_value(row: pd.Series) -> str:
    if "wait" in str(row["label"]).lower():
        return f"{row['value']:.0f} min"
    if "state" in str(row["label"]).lower():
        return f"{row['value']:.1f}h LOS"
    return f"{row['value']:.2f}"


def _pediatric_pressure(public_data: dict[str, pd.DataFrame], facility: str) -> float:
    pressure = public_pressure_index(public_data)
    if pressure.empty:
        return 0.0
    row = pressure[pressure["facility"] == facility]
    if row.empty:
        return float(pressure["public_pressure_index"].mean())
    pediatric_weight = 1.15 if bool(row["pediatric_site"].iloc[0]) else 0.85
    return float(np.clip(row["public_pressure_index"].iloc[0] * pediatric_weight, 0, 1))


def _respiratory_score(public_data: dict[str, pd.DataFrame], facility: str) -> float:
    facilities = public_data.get("facility_reference", pd.DataFrame())
    zone = facilities.loc[facilities["facility"] == facility, "zone"].iloc[0] if not facilities.empty and facility in facilities["facility"].values else "Edmonton"
    resp = public_data.get("respiratory_surveillance", pd.DataFrame()).copy()
    if resp.empty:
        return 0.0
    recent = resp[resp["zone"] == zone].sort_values("week_start").tail(8)
    return float(recent["pediatric_pressure_index"].mean()) if not recent.empty else 0.0


def what_changed_panel(public_data: dict[str, pd.DataFrame], facility: str) -> pd.DataFrame:
    """Compare latest and prior public-context readings."""

    rows = []
    for dataset, time_col, value_col, label in [
        ("public_wait_times", "posted_timestamp", "estimated_wait_mins", "Posted wait fallback"),
        ("environmental_stress", "timestamp", "environmental_stress_index", "Environmental stress"),
        ("travel_friction", "timestamp", "travel_friction_index", "Travel friction"),
    ]:
        frame = public_data.get(dataset, pd.DataFrame()).copy()
        frame = frame[frame.get("facility", pd.Series(dtype=str)) == facility] if not frame.empty else frame
        if len(frame) < 2:
            continue
        frame = frame.sort_values(time_col)
        latest = float(frame[value_col].iloc[-1])
        prior = float(frame[value_col].iloc[-2])
        rows.append({"signal": label, "latest": latest, "previous": prior, "change": latest - prior, "direction": "up" if latest > prior else "down/flat"})
    return pd.DataFrame(rows)


def why_pressure_moved(metrics: pd.DataFrame) -> str:
    ranked = metrics[~metrics["label"].str.contains("wait-time|state", case=False, regex=True)].sort_values("value", ascending=False)
    if ranked.empty:
        return "No pressure movement explanation is available."
    top = ranked.head(3)["label"].tolist()
    return "Pressure is primarily explained by " + ", ".join(top) + "."


def top_watchpoints(metrics: pd.DataFrame, state: dict[str, object]) -> list[str]:
    watch = []
    if float(metrics.loc[metrics["label"].eq("Respiratory surge"), "value"].max() if metrics["label"].eq("Respiratory surge").any() else 0) > 0.25:
        watch.append("pediatric respiratory arrivals, CTAS mix, and respiratory cohort capacity")
    if int(state.get("decision_to_admit_boarders", 0)) > 0:
        watch.append("decision-to-admit boarding and inpatient bed release timing")
    if int(state.get("triaged_waiting", 0)) + int(state.get("waiting_to_triage", 0)) > 5:
        watch.append("waiting-room queue, LWBS risk, and room turnover")
    watch.extend(["EMS offload and first-contact-to-triage delay", "consult queue age and diagnostic turnaround"])
    return watch[:3]


def top_operational_levers(metrics: pd.DataFrame, state: dict[str, object]) -> list[str]:
    levers = []
    if int(state.get("decision_to_admit_boarders", 0)) > 0:
        levers.append("accelerate bed assignment, pending discharges, and bed cleaning handoffs")
    if int(state.get("waiting_for_physician_initial_assessment", 0)) + int(state.get("roomed_not_seen", 0)) > 2:
        levers.append("shift physician/rapid-assessment capacity toward initial assessment")
    levers.extend(
        [
            "activate CTAS 4/5 fast-track or respiratory cohort stream if staffing supports it",
            "pre-brief diagnostics and consult services for likely surge-sensitive delays",
            "monitor access friction and EMS offload process if weather/traffic worsen",
        ]
    )
    return levers[:3]


def _impact_interpretation(metric: str, delta: float) -> str:
    if metric == "expected_arrivals":
        return "Higher arrivals increase front-end and rooming pressure." if delta > 0 else "Arrival pressure improves."
    if metric == "expected_pia_wait_mins":
        return "PIA delay may move downstream bottlenecks unless physician capacity shifts." if delta > 0 else "PIA delay improves."
    if metric == "expected_lwbs_risk":
        return "LWBS risk rises with waiting time and crowding." if delta > 0 else "LWBS risk improves."
    return "Scenario changes this operational signal."

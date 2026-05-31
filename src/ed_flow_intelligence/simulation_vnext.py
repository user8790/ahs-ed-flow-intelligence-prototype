"""Enhanced simulation interpretation and scenario ranking wrappers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ed_flow.data_contracts import ScenarioConfig
from ed_flow.simulation_engine import run_simulation, summarize_with_uncertainty
from ed_flow_intelligence.operational_intelligence import deterministic_huddle_brief, pressure_to_action_translator


def lwbs_hazard(wait_hours: float, crowding_index: float, triage_level: int) -> float:
    """State-dependent LWBS hazard responding to wait, crowding, and acuity."""

    low_acuity = max(int(triage_level) - 2, 0) * 0.018
    wait_component = 0.012 * max(wait_hours, 0) ** 1.25
    crowding_component = 0.09 * max(crowding_index, 0)
    return float(np.clip(0.01 + low_acuity + wait_component + crowding_component, 0.0, 0.78))


def run_enhanced_simulation_summary(
    visits: pd.DataFrame,
    scenario: ScenarioConfig,
    implementation_friction: float = 0.45,
) -> dict[str, pd.DataFrame | list[str]]:
    """Run simulation and add utilization, occupancy, action interpretation, and huddle outputs."""

    output = run_simulation(visits, scenario)
    uncertainty = summarize_with_uncertainty(output.summary)
    utilization = resource_utilization(output.patients, scenario)
    occupancy = stage_occupancy(output.patients, scenario.horizon_hours)
    migration = bottleneck_migration(output.bottlenecks)
    ranking = rank_simulation_scenarios(visits, scenario)
    top_bottleneck = migration.iloc[0]["bottleneck"] if not migration.empty else "Physician initial assessment"
    actions = pressure_to_action_translator(str(top_bottleneck), f"arrival multiplier {scenario.arrival_surge_multiplier:.2f}")
    impact = uncertainty.rename(columns={"metric": "target", "mean": "scenario", "p10": "p10", "p90": "p90"}).head(4)
    impact["baseline"] = np.nan
    impact["scenario_delta"] = np.nan
    impact["change_label"] = impact.apply(lambda row: f"p50 {row['scenario']:.2f}; P10-P90 {row['p10']:.2f}-{row['p90']:.2f}", axis=1)
    huddle = deterministic_huddle_brief("Simulation scenario", impact.rename(columns={"target": "metric"}), actions, ranking.head(3)["scenario"].tolist(), confidence="moderate")
    return {
        "uncertainty": uncertainty,
        "patients": output.patients,
        "queue_lengths": output.queue_lengths,
        "bottlenecks": output.bottlenecks,
        "utilization": utilization,
        "occupancy": occupancy,
        "migration": migration,
        "ranking": ranking,
        "actions": actions,
        "huddle": huddle,
    }


def resource_utilization(patients: pd.DataFrame, scenario: ScenarioConfig) -> pd.DataFrame:
    """Approximate utilization for resource pools from patient-level simulated durations."""

    visits_per_rep = patients.groupby("replication").size().mean()
    horizon = max(float(scenario.horizon_hours), 1.0)
    triage_cap = max(1, 2 + scenario.triage_capacity_delta)
    room_cap = max(1, 18 + scenario.rooming_capacity_delta)
    physician_cap = max(1, 5 + scenario.physician_capacity_delta)
    rows = [
        ("triage nurses", float(patients["triage_wait_hrs"].mean() + 0.18) * visits_per_rep / (horizon * triage_cap), "front-end triage capacity"),
        ("ED rooms", float((patients["rooming_wait_hrs"] + patients["ed_los_hrs"]).mean()) * visits_per_rep / (horizon * room_cap), "treatment-space occupancy"),
        ("physician capacity", float((patients["wait_to_physician_hrs"] + 0.45).mean()) * visits_per_rep / (horizon * physician_cap), "initial assessment capacity"),
        ("diagnostics", float(patients["diagnostic_delay_hrs"].mean()) * visits_per_rep / max(horizon * 6, 1), "diagnostic turnaround"),
        ("consult capacity", float(patients["consult_delay_hrs"].mean()) * visits_per_rep / max(horizon * 4, 1), "consult turnaround"),
        ("inpatient bed release", float(patients["boarding_hours"].mean()) * visits_per_rep / max(horizon * 5, 1), "boarding and bed assignment"),
        ("EMS offload", float(patients["ems_offload_delay_hrs"].mean()) * visits_per_rep / max(horizon * 3, 1), "EMS offload process"),
    ]
    out = pd.DataFrame(rows, columns=["resource_pool", "utilization_index", "interpretation"])
    out["utilization_index"] = out["utilization_index"].clip(0, 1.5)
    out["status"] = pd.cut(out["utilization_index"], [-0.01, 0.65, 0.9, 2.0], labels=["available", "tight", "binding"]).astype(str)
    return out.sort_values("utilization_index", ascending=False).reset_index(drop=True)


def stage_occupancy(patients: pd.DataFrame, horizon_hours: int) -> pd.DataFrame:
    """Approximate stage occupancy over time."""

    rows = []
    for rep, group in patients.groupby("replication"):
        for hour in range(horizon_hours + 1):
            active = group["arrival_time_hr"] <= hour
            rows.append(
                {
                    "replication": rep,
                    "hour": hour,
                    "waiting_room": int((active & (group["arrival_time_hr"] + group["wait_to_physician_hrs"] > hour)).sum()),
                    "roomed_not_seen": int((active & (group["rooming_wait_hrs"] > 0.5) & (group["arrival_time_hr"] + group["wait_to_physician_hrs"] > hour)).sum()),
                    "diagnostics_consults": int((active & ((group["diagnostic_delay_hrs"] > 1) | (group["consult_delay_hrs"] > 1))).sum()),
                    "boarding": int((active & (group["boarding_hours"] > 0) & (group["arrival_time_hr"] + group["ed_los_hrs"] > hour)).sum()),
                }
            )
    return pd.DataFrame(rows).groupby("hour", as_index=False).mean(numeric_only=True)


def bottleneck_migration(bottlenecks: pd.DataFrame) -> pd.DataFrame:
    """Add migration interpretation to bottleneck rows."""

    if bottlenecks.empty:
        return bottlenecks
    out = bottlenecks.copy()
    top_share = float(out["share_of_delay"].max()) if "share_of_delay" in out else 0
    out["migration_signal"] = np.where(
        out["share_of_delay"] >= top_share * 0.85,
        "primary binding or near-binding stage",
        "secondary stage that may bind after intervention",
    )
    out["operational_question"] = out["bottleneck"].map(
        {
            "Boarding": "Will inpatient bed release improve enough for front-end changes to matter?",
            "Physician initial assessment": "Can PIA capacity shift without starving downstream treatment?",
            "Rooming wait": "Can room turnover or fast-track reduce pre-rooming queues?",
            "Consult delay": "Can specialty response time be shortened for admission-likely routes?",
            "Diagnostics": "Can lab/imaging TAT support faster disposition?",
            "EMS offload": "Can offload process capacity match arrival pulses?",
        }
    ).fillna("Which internal feed validates this bottleneck?")
    return out


def rank_simulation_scenarios(visits: pd.DataFrame, base_scenario: ScenarioConfig) -> pd.DataFrame:
    """Rank candidate simulation levers by outcome, uncertainty, and friction."""

    candidates = {
        "baseline": base_scenario,
        "triage nurse +1": base_scenario.model_copy(update={"triage_capacity_delta": base_scenario.triage_capacity_delta + 1}),
        "physician +1": base_scenario.model_copy(update={"physician_capacity_delta": base_scenario.physician_capacity_delta + 1}),
        "fast-track CTAS 4/5": base_scenario.model_copy(update={"fast_track_enabled": True}),
        "boarding reduction": base_scenario.model_copy(update={"boarding_reduction": min(base_scenario.boarding_reduction + 0.25, 0.8)}),
        "diagnostic turnaround": base_scenario.model_copy(update={"diagnostic_turnaround_improvement": min(base_scenario.diagnostic_turnaround_improvement + 0.2, 0.75)}),
        "consult turnaround": base_scenario.model_copy(update={"consult_turnaround_improvement": min(base_scenario.consult_turnaround_improvement + 0.2, 0.75)}),
    }
    rows = []
    baseline_los = None
    for name, scenario in candidates.items():
        quick = scenario.model_copy(update={"replications": max(5, min(12, scenario.replications))})
        output = run_simulation(visits, quick)
        summary = output.summary
        p50_los = float(summary["median_ed_los_hrs"].mean())
        p90_wait = float(summary["p90_wait_hrs"].mean())
        boarding = float(summary["boarding_hours"].mean())
        if baseline_los is None:
            baseline_los = p50_los
        improvement = baseline_los - p50_los
        friction = _friction(name)
        uncertainty = float(summary["median_ed_los_hrs"].std() or 0)
        rows.append(
            {
                "scenario": name,
                "median_los_hrs": p50_los,
                "p90_wait_hrs": p90_wait,
                "boarding_hours": boarding,
                "expected_los_improvement_hrs": improvement,
                "uncertainty_penalty": uncertainty,
                "implementation_friction": friction,
                "impact_adjusted_score": improvement - 0.2 * uncertainty - 0.35 * friction,
                "meaningful": "yes" if improvement > 0.15 else "watch/limited",
            }
        )
    return pd.DataFrame(rows).sort_values("impact_adjusted_score", ascending=False).reset_index(drop=True)


def _friction(name: str) -> float:
    return {
        "baseline": 0.0,
        "triage nurse +1": 0.35,
        "physician +1": 0.55,
        "fast-track CTAS 4/5": 0.5,
        "boarding reduction": 0.7,
        "diagnostic turnaround": 0.45,
        "consult turnaround": 0.5,
    }[name]

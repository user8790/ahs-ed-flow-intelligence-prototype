"""Combined public shock scenarios and action interpretation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ed_flow_intelligence.modeling import forecast_external_pressure
from ed_flow_intelligence.operational_intelligence import deterministic_huddle_brief, scenario_impact_cards


class ScenarioShockConfig(BaseModel):
    """Combined public and synthetic capacity shocks."""

    respiratory_surge: float = Field(default=1.0, ge=0.0, le=3.0)
    school_reopening: bool = False
    long_weekend: bool = False
    large_public_event: float = Field(default=0.0, ge=0.0, le=1.0)
    smoke_event: float = Field(default=0.0, ge=0.0, le=1.0)
    heat_wave: float = Field(default=0.0, ge=0.0, le=1.0)
    cold_snap_snowstorm: float = Field(default=0.0, ge=0.0, le=1.0)
    traffic_disruption: float = Field(default=0.0, ge=0.0, le=1.0)
    wildfire_evacuation_access: float = Field(default=0.0, ge=0.0, le=1.0)
    public_wait_deterioration_mins: int = Field(default=0, ge=0, le=300)
    synthetic_capacity_constraint: float = Field(default=0.0, ge=0.0, le=1.0)


def run_combined_public_scenario(
    visits: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
    horizon_hours: int,
    shocks: ScenarioShockConfig,
) -> dict[str, pd.DataFrame | list[str]]:
    """Run a combined public scenario and return app-ready outputs."""

    bundle = forecast_external_pressure(public_data, facility, horizon_hours=horizon_hours)
    hourly = bundle.hourly.copy()
    if hourly.empty:
        return {"forecast": hourly, "impact": pd.DataFrame(), "affected_stages": pd.DataFrame(), "ranking": pd.DataFrame(), "huddle": []}
    shock_multiplier = _shock_multiplier(shocks)
    baseline = hourly[["timestamp", "p10_pressure", "p50_pressure", "p90_pressure"]].copy()
    scenario = baseline.copy()
    scenario[["p10_pressure", "p50_pressure", "p90_pressure"]] = (
        scenario[["p10_pressure", "p50_pressure", "p90_pressure"]] * shock_multiplier
        + _wait_effect(shocks.public_wait_deterioration_mins)
    ).clip(0, 1)
    scenario["scenario"] = "combined public stress"
    baseline["scenario"] = "baseline"
    combined = pd.concat([baseline, scenario], ignore_index=True)
    baseline_summary = pd.DataFrame(
        [
            {
                "expected_arrivals": _expected_arrivals(visits, facility, horizon_hours, float(baseline["p50_pressure"].mean())),
                "public_pressure_index": float(baseline["p50_pressure"].mean()),
                "expected_pia_wait_mins": 55 + float(baseline["p50_pressure"].mean()) * 75,
                "expected_lwbs_risk": 0.04 + float(baseline["p50_pressure"].mean()) * 0.08,
            }
        ]
    )
    scenario_summary = pd.DataFrame(
        [
            {
                "expected_arrivals": _expected_arrivals(visits, facility, horizon_hours, float(scenario["p50_pressure"].mean())),
                "public_pressure_index": float(scenario["p50_pressure"].mean()),
                "expected_pia_wait_mins": 55 + float(scenario["p50_pressure"].mean()) * 95 + shocks.synthetic_capacity_constraint * 20,
                "expected_lwbs_risk": min(0.42, 0.04 + float(scenario["p50_pressure"].mean()) * 0.12 + shocks.synthetic_capacity_constraint * 0.05),
            }
        ]
    )
    impact = scenario_impact_cards(baseline_summary, scenario_summary)
    affected = affected_stage_table(shocks, float(scenario["p50_pressure"].mean()))
    ranking = rank_public_scenarios(visits, public_data, facility, horizon_hours, shocks)
    watchpoints = affected.head(3)["watch_point"].tolist()
    levers = affected.head(3)["operational_lever"].tolist()
    huddle = deterministic_huddle_brief("Combined public pressure scenario", impact, watchpoints, levers, confidence=_confidence_from_pressure(float(scenario["p50_pressure"].mean())))
    return {"forecast": combined, "impact": impact, "affected_stages": affected, "ranking": ranking, "huddle": huddle}


def affected_stage_table(shocks: ScenarioShockConfig, scenario_pressure: float) -> pd.DataFrame:
    """Translate shocks into likely affected ED stages."""

    rows = [
        ("arrival / first contact", scenario_pressure + 0.15 * shocks.respiratory_surge, "external arrivals may rise or cluster", "front-door triage pace and EMS offload", "match triage/front-door staffing to arrival pulses"),
        ("waiting room", scenario_pressure + shocks.synthetic_capacity_constraint * 0.3, "wait-room crowding increases LWBS hazard", "LWBS risk and reassessment intervals", "fast-track CTAS 4/5 and reassessment cadence"),
        ("rooming", scenario_pressure + 0.25 * shocks.smoke_event + 0.18 * shocks.heat_wave, "respiratory/heat patients may need spaces for longer", "room turnover and respiratory cohort capacity", "cohort respiratory pathway and room turnover focus"),
        ("physician initial assessment", scenario_pressure + shocks.synthetic_capacity_constraint * 0.4, "PIA becomes sensitive when roomed-not-seen grows", "PIA queue and physician utilization", "rapid assessment zone or shifted physician schedule"),
        ("diagnostics / consult", scenario_pressure + 0.2 * shocks.respiratory_surge, "higher acuity mix can increase diagnostic and consult load", "diagnostic TAT and consult queue age", "pre-brief diagnostics/consult service constraints"),
        ("boarding", scenario_pressure + shocks.synthetic_capacity_constraint * 0.55, "front-end gains may stall if bed release is binding", "DTA boarders and bed assignment age", "pending discharge and bed-cleaning acceleration"),
    ]
    out = pd.DataFrame(rows, columns=["stage", "risk_score", "why_it_matters", "watch_point", "operational_lever"])
    out["risk_score"] = out["risk_score"].clip(0, 1)
    out["confidence"] = np.where(out["risk_score"] > 0.68, "wide", "moderate")
    return out.sort_values("risk_score", ascending=False).reset_index(drop=True)


def rank_public_scenarios(
    visits: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
    horizon_hours: int,
    base_shocks: ScenarioShockConfig,
) -> pd.DataFrame:
    """Rank candidate scenarios by impact, uncertainty, and implementation friction."""

    candidates = {
        "respiratory pathway": base_shocks.model_copy(update={"respiratory_surge": min(base_shocks.respiratory_surge + 0.4, 3.0)}),
        "fast-track capacity": base_shocks.model_copy(update={"synthetic_capacity_constraint": max(base_shocks.synthetic_capacity_constraint - 0.25, 0)}),
        "access disruption response": base_shocks.model_copy(update={"traffic_disruption": min(base_shocks.traffic_disruption + 0.25, 1)}),
        "bed release acceleration": base_shocks.model_copy(update={"synthetic_capacity_constraint": max(base_shocks.synthetic_capacity_constraint - 0.35, 0)}),
    }
    rows = []
    for name, shocks in candidates.items():
        multiplier = _shock_multiplier(shocks)
        impact = multiplier - _shock_multiplier(base_shocks)
        friction = {"respiratory pathway": 0.45, "fast-track capacity": 0.55, "access disruption response": 0.25, "bed release acceleration": 0.72}[name]
        uncertainty = min(0.35, 0.08 + abs(impact) * 0.22 + shocks.synthetic_capacity_constraint * 0.1)
        expected_impact = -impact if "capacity" in name or "release" in name else impact
        rows.append(
            {
                "scenario": name,
                "expected_pressure_effect": expected_impact,
                "uncertainty_penalty": uncertainty,
                "implementation_friction": friction,
                "impact_adjusted_score": expected_impact - uncertainty - friction * 0.15,
                "interpretation": _scenario_rank_interpretation(name),
            }
        )
    return pd.DataFrame(rows).sort_values("impact_adjusted_score", ascending=False).reset_index(drop=True)


def _shock_multiplier(shocks: ScenarioShockConfig) -> float:
    return float(
        1.0
        + 0.12 * max(shocks.respiratory_surge - 1.0, 0)
        + 0.08 * shocks.school_reopening
        + 0.06 * shocks.long_weekend
        + 0.08 * shocks.large_public_event
        + 0.10 * shocks.smoke_event
        + 0.08 * shocks.heat_wave
        + 0.09 * shocks.cold_snap_snowstorm
        + 0.07 * shocks.traffic_disruption
        + 0.11 * shocks.wildfire_evacuation_access
        + 0.14 * shocks.synthetic_capacity_constraint
    )


def _wait_effect(minutes: int) -> float:
    return float(np.clip(max(minutes - 90, 0) / 500, 0, 0.32))


def _expected_arrivals(visits: pd.DataFrame, facility: str, horizon_hours: int, pressure: float) -> float:
    site = visits[visits["INSTITUTION_NAME"] == facility] if "INSTITUTION_NAME" in visits else visits
    rate = max(len(site) / max(site["FIRST_CONTACT_DATETIME"].dt.date.nunique() * 24 if "FIRST_CONTACT_DATETIME" in site and pd.api.types.is_datetime64_any_dtype(site["FIRST_CONTACT_DATETIME"]) else 24, 1), 0.5)
    return float(rate * horizon_hours * (1 + pressure * 0.38))


def _confidence_from_pressure(pressure: float) -> str:
    if pressure < 0.45:
        return "moderate"
    if pressure < 0.7:
        return "moderate-to-wide"
    return "wide"


def _scenario_rank_interpretation(name: str) -> str:
    mapping = {
        "respiratory pathway": "Best when pediatric respiratory pressure is the dominant public driver.",
        "fast-track capacity": "Best when CTAS 4/5 rooming and PIA queues are binding before boarding.",
        "access disruption response": "Best when weather, traffic, or events may alter arrivals and staffing access.",
        "bed release acceleration": "Best when boarding dominates total delay and front-end gains would otherwise stall.",
    }
    return mapping[name]

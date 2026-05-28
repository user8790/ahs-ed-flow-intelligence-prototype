"""Scenario comparison helpers."""

from __future__ import annotations

import pandas as pd

from ed_flow.data_contracts import ScenarioConfig
from ed_flow.simulation_engine import run_simulation, summarize_with_uncertainty


def scenario_label(scenario: ScenarioConfig) -> str:
    """Create a readable scenario label."""

    labels = []
    if scenario.arrival_surge_multiplier != 1.0:
        labels.append(f"{scenario.arrival_surge_multiplier:.1f}x arrivals")
    if scenario.triage_capacity_delta:
        labels.append(f"triage {scenario.triage_capacity_delta:+d}")
    if scenario.rooming_capacity_delta:
        labels.append(f"rooms {scenario.rooming_capacity_delta:+d}")
    if scenario.physician_capacity_delta:
        labels.append(f"physicians {scenario.physician_capacity_delta:+d}")
    if scenario.fast_track_enabled:
        labels.append("fast track")
    if scenario.boarding_reduction:
        labels.append(f"{scenario.boarding_reduction:.0%} boarding reduction")
    return ", ".join(labels) if labels else "Baseline"


def compare_scenarios(visits: pd.DataFrame, scenarios: list[ScenarioConfig]) -> pd.DataFrame:
    """Run and summarize multiple scenarios."""

    rows = []
    for scenario in scenarios:
        output = run_simulation(visits, scenario)
        uncertainty = summarize_with_uncertainty(output.summary)
        row = {"scenario": scenario_label(scenario)}
        for _, metric in uncertainty.iterrows():
            row[f"{metric['metric']}_mean"] = metric["mean"]
            row[f"{metric['metric']}_p10"] = metric["p10"]
            row[f"{metric['metric']}_p90"] = metric["p90"]
        rows.append(row)
    return pd.DataFrame(rows)


def practical_interpretation(comparison: pd.DataFrame) -> str:
    """Draft an operational interpretation from scenario comparison metrics."""

    if comparison.empty:
        return "No scenario output is available."
    baseline = comparison.iloc[0]
    best_wait = comparison.sort_values("p90_wait_hrs_mean", ascending=True).iloc[0]
    best_boarding = comparison.sort_values("boarding_hours_mean", ascending=True).iloc[0]
    parts = [
        f"The lowest simulated p90 wait is under '{best_wait['scenario']}'.",
        f"The lowest total boarding burden is under '{best_boarding['scenario']}'.",
    ]
    if len(comparison) > 1:
        delta = float(baseline.get("p90_wait_hrs_mean", 0) - best_wait.get("p90_wait_hrs_mean", 0))
        parts.append(f"Compared with baseline, the best wait scenario changes p90 wait by about {delta:.1f} hours.")
    parts.append("Interpretation is generated from simulation outputs and should support, not replace, operational judgement.")
    return " ".join(parts)


from __future__ import annotations

from ed_flow.data_contracts import ScenarioConfig
from ed_flow.feature_engineering import apply_default_business_rules
from ed_flow.simulation_engine import run_simulation, summarize_with_uncertainty
from ed_flow.synthetic_data import generate_synthetic_ed_visits


def _visits():
    df = apply_default_business_rules(generate_synthetic_ed_visits(n_visits=500, seed=301))
    facility = df["INSTITUTION_NAME"].iloc[0]
    return df[df["INSTITUTION_NAME"] == facility].reset_index(drop=True), facility


def test_simulation_runs_with_reproducible_seed() -> None:
    visits, facility = _visits()
    scenario = ScenarioConfig(facility=facility, replications=10, random_seed=7)

    first = run_simulation(visits, scenario)
    second = run_simulation(visits, scenario)

    assert len(first.summary) == 10
    assert first.summary.round(6).equals(second.summary.round(6))
    assert not summarize_with_uncertainty(first.summary).empty


def test_scenario_changes_alter_outputs() -> None:
    visits, facility = _visits()
    baseline = ScenarioConfig(facility=facility, replications=10, random_seed=8)
    surge = ScenarioConfig(facility=facility, replications=10, random_seed=8, arrival_surge_multiplier=1.7)

    base_output = run_simulation(visits, baseline)
    surge_output = run_simulation(visits, surge)

    assert surge_output.summary["visits"].mean() > base_output.summary["visits"].mean()
    assert not surge_output.summary["p90_wait_hrs"].equals(base_output.summary["p90_wait_hrs"])


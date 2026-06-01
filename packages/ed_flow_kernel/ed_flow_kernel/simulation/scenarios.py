"""Scenario and simulation wrappers."""

from __future__ import annotations

import pandas as pd

from ed_flow.data_contracts import ScenarioConfig
from ed_flow_intelligence.advanced_scenarios import ScenarioShockConfig, run_combined_public_scenario
from ed_flow_intelligence.simulation_vnext import lwbs_hazard, run_enhanced_simulation_summary


def combined_public_scenario(visits: pd.DataFrame, public_data: dict[str, pd.DataFrame], facility: str, horizon_hours: int, shocks: ScenarioShockConfig):
    """Run public pressure shock scenario."""

    return run_combined_public_scenario(visits, public_data, facility, horizon_hours, shocks)


def enhanced_simulation(visits: pd.DataFrame, scenario: ScenarioConfig):
    """Run discrete-event simulation and operational interpretation."""

    return run_enhanced_simulation_summary(visits, scenario)


__all__ = ["ScenarioConfig", "ScenarioShockConfig", "combined_public_scenario", "enhanced_simulation", "lwbs_hazard"]

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ed_flow.data_contracts import ScenarioConfig, VisitFilters
from ed_flow.local_backend import LocalBackend
from ed_flow.synthetic_data import write_synthetic_data
from ed_flow_intelligence.advanced_scenarios import ScenarioShockConfig, run_combined_public_scenario
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data, load_public_open_data
from ed_flow_intelligence.modeling import build_public_feature_matrix, forecast_external_pressure, forecast_internal_targets, rolling_origin_backtest
from ed_flow_intelligence.operational_intelligence import executive_pressure_cockpit, research_capability_map
from ed_flow_intelligence.simulation_vnext import lwbs_hazard, run_enhanced_simulation_summary


def _fixtures(tmp_path):
    internal_dir = tmp_path / "synthetic"
    open_dir = tmp_path / "open"
    write_synthetic_data(Path(internal_dir), force=True)
    ensure_public_open_data(open_dir, force=True)
    backend = LocalBackend(internal_dir)
    visits = backend.load_ed_visits(VisitFilters())
    active = backend.load_current_active_visits()
    public_data = load_public_open_data(open_dir)
    return backend, visits, active, public_data


def test_ensemble_forecast_returns_intervals_validation_and_registry(tmp_path) -> None:
    _, visits, _, public_data = _fixtures(tmp_path)
    facility = "Stollery Children's Hospital"
    features = build_public_feature_matrix(public_data, facility)
    bundle = forecast_external_pressure(public_data, facility, horizon_hours=24)
    backtest = rolling_origin_backtest(features)
    internal_targets = forecast_internal_targets(visits, public_data, facility)
    assert {"p10_pressure", "p50_pressure", "p90_pressure", "model_random_forest"}.issubset(bundle.hourly.columns)
    assert bundle.hourly["p50_pressure"].between(0, 1).all()
    assert {"mae", "rmse", "wape", "interval_coverage", "top_decile_surge_recall"}.issubset(bundle.validation.columns)
    assert "ensemble" in set(bundle.validation["model"])
    assert not bundle.registry.empty
    assert not backtest.empty
    assert {"target", "pressure_adjusted_prediction", "validation_status"}.issubset(internal_targets.columns)


def test_combined_public_scenario_outputs_huddle_and_ranking(tmp_path) -> None:
    _, visits, _, public_data = _fixtures(tmp_path)
    bundle = run_combined_public_scenario(
        visits,
        public_data,
        "Stollery Children's Hospital",
        24,
        ScenarioShockConfig(respiratory_surge=1.6, school_reopening=True, smoke_event=0.5, traffic_disruption=0.4),
    )
    assert {"forecast", "impact", "affected_stages", "ranking", "huddle"}.issubset(bundle.keys())
    assert not bundle["impact"].empty
    assert not bundle["affected_stages"].empty
    assert len(bundle["huddle"]) == 5
    assert bundle["ranking"]["impact_adjusted_score"].is_monotonic_decreasing


def test_lwbs_hazard_and_enhanced_simulation_outputs(tmp_path) -> None:
    _, visits, _, _ = _fixtures(tmp_path)
    facility = "Stollery Children's Hospital"
    site = visits[visits["INSTITUTION_NAME"] == facility].copy()
    scenario = ScenarioConfig(facility=facility, replications=10, random_seed=11)
    enhanced = run_enhanced_simulation_summary(site, scenario)
    assert lwbs_hazard(5.0, 0.8, 5) > lwbs_hazard(1.0, 0.1, 2)
    assert {"resource_pool", "utilization_index", "status"}.issubset(enhanced["utilization"].columns)
    assert {"waiting_room", "boarding"}.issubset(enhanced["occupancy"].columns)
    assert not enhanced["ranking"].empty
    assert len(enhanced["huddle"]) == 5


def test_executive_cockpit_and_research_map_are_computed(tmp_path) -> None:
    _, visits, active, public_data = _fixtures(tmp_path)
    cockpit = executive_pressure_cockpit(visits, active, public_data, "Stollery Children's Hospital")
    research = research_capability_map()
    assert {"metrics", "site_ranking", "zone_ranking", "watchpoints", "levers"}.issubset(cockpit.keys())
    assert len(cockpit["metrics"]) >= 8
    assert not research.empty
    assert "Forecast-to-simulation pipeline" in set(research["research_insight"])

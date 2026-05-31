from __future__ import annotations

from pathlib import Path

from ed_flow.data_contracts import VisitFilters
from ed_flow.local_backend import LocalBackend
from ed_flow.synthetic_data import write_synthetic_data
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data, load_public_open_data
from ed_flow_intelligence.forecasting import hybrid_arrival_forecast, likely_binding_constraints
from ed_flow_intelligence.scenarios import run_public_scenario


def test_hybrid_forecast_and_public_scenario_run(tmp_path) -> None:
    internal_dir = tmp_path / "synthetic"
    open_dir = tmp_path / "open"
    write_synthetic_data(Path(internal_dir), force=True)
    ensure_public_open_data(open_dir, force=True)
    backend = LocalBackend(internal_dir)
    visits = backend.load_ed_visits(VisitFilters())
    public_data = load_public_open_data(open_dir)
    facility = "Stollery Children's Hospital"
    forecast = hybrid_arrival_forecast(visits, public_data, facility, horizon_hours=12)
    scenario = run_public_scenario(visits, public_data, facility, 12, 1.4, 1.2, 1.1, 150)
    assert len(forecast) == 12
    assert forecast["expected_arrivals"].gt(0).all()
    assert list(scenario["scenario"]) == ["baseline public context", "public stress scenario"]
    assert scenario.loc[1, "expected_arrivals"] >= scenario.loc[0, "expected_arrivals"]


def test_likely_binding_constraints_return_ranked_rows(tmp_path) -> None:
    internal_dir = tmp_path / "synthetic"
    open_dir = tmp_path / "open"
    write_synthetic_data(Path(internal_dir), force=True)
    ensure_public_open_data(open_dir, force=True)
    backend = LocalBackend(internal_dir)
    constraints = likely_binding_constraints(
        backend.load_current_active_visits(),
        backend.load_beds_staffing_diagnostics(),
        load_public_open_data(open_dir),
        "Stollery Children's Hospital",
    )
    assert {"constraint", "risk_score", "interpretation", "uncertainty_band"}.issubset(constraints.columns)
    assert constraints["risk_score"].is_monotonic_decreasing

from __future__ import annotations

import json
from pathlib import Path

from ed_flow_kernel.exports.stollery_public_showcase_export import (
    ARTIFACT_NAMES,
    FOCUS_SITE,
    export_stollery_public_showcase_artifacts,
)
from ed_flow_kernel.governance.privacy import public_payload_has_phi_like_values


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_stollery_export_creates_required_artifacts(tmp_path: Path) -> None:
    written = export_stollery_public_showcase_artifacts(tmp_path, seed=20260601)
    assert {path.name for path in written} == set(ARTIFACT_NAMES)
    for path in written:
        data = load(path)
        assert data["schema_version"] == "2.0"
        assert data["focus_site"] == FOCUS_SITE
        assert data["synthetic_flag"] is True
        assert "data" in data
        assert data["caveats"]
        assert not public_payload_has_phi_like_values(data)


def test_static_stollery_artifacts_are_present() -> None:
    public_data_dir = Path("apps/public_showcase/public/data")
    missing = [name for name in ARTIFACT_NAMES if not (public_data_dir / name).exists()]
    assert missing == []


def test_stollery_baseline_forecast_shape_and_intervals() -> None:
    data = load(Path("apps/public_showcase/public/data/stollery_forecast_baseline.json"))["data"]
    assert len(data["hourly_72h"]) == 72
    assert len(data["daily_28d"]) == 28
    assert data["baseline_locked"] is True
    for row in data["hourly_72h"]:
        assert row["arrivals_p10"] <= row["arrivals_p50"] <= row["arrivals_p90"]
        assert row["physician_wait_mins_p10"] <= row["physician_wait_mins_p50"] <= row["physician_wait_mins_p90"]
        assert row["lwbs_risk_p50"] >= 0


def test_stollery_unit_capacity_is_coherent() -> None:
    data = load(Path("apps/public_showcase/public/data/stollery_synthetic_unit_capacity.json"))["data"]
    units = data["units"]
    assert sum(row["total_beds_or_planning_capacity"] for row in units) == data["public_capacity_context"]["public_total_beds_context"]
    assert data["totals"]["total_capacity_rows"] == data["public_capacity_context"]["public_total_beds_context"]
    for row in units:
        assert row["staffed_beds"] <= row["total_beds_or_planning_capacity"]
        assert row["occupied_beds"] <= row["staffed_beds"] + 2
        assert 0 <= row["receiving_capacity_risk"] <= 1.25
        assert row["classification"] in {
            "Synthetic planning assumption",
            "Public fact anchored; operating state synthetic",
        }


def test_scenario_presets_and_coefficients_are_valid() -> None:
    catalog = load(Path("apps/public_showcase/public/data/stollery_scenario_catalog.json"))["data"]
    coefficients = load(Path("apps/public_showcase/public/data/stollery_scenario_coefficients.json"))["data"]
    presets = load(Path("apps/public_showcase/public/data/stollery_scenario_presets.json"))["data"]
    control_ids = {row["id"] for row in catalog["controls"]}
    coefficient_ids = set(coefficients["controls"])
    assert len(presets) >= 10
    for preset in presets:
        assert preset["controls"]
        for control_id, value in preset["controls"].items():
            assert control_id in control_ids
            assert control_id in coefficient_ids
            assert isinstance(value, (int, float))


def test_synthetic_history_has_realistic_range() -> None:
    history = load(Path("apps/public_showcase/public/data/stollery_synthetic_ed_history.json"))["data"]
    daily = history["daily"]
    assert len(daily) >= 365
    assert daily[0]["date"] < daily[-1]["date"]
    assert 80 <= min(row["arrivals"] for row in daily) <= 180
    assert max(row["arrivals"] for row in daily) <= 260
    assert set(row["respiratory_season_flag"] for row in daily) == {False, True}

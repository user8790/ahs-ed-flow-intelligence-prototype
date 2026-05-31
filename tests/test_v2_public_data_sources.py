from __future__ import annotations

from ed_flow_intelligence.data_sources.registry import load_data_source_registry, registry_to_frame
from ed_flow_intelligence.data_sources.synthetic_open_data import ensure_public_open_data, load_public_open_data
from ed_flow_intelligence.forecasting import public_pressure_index
from ed_flow_intelligence.lineage import LineageCategory


def test_registry_contains_required_lineage_categories() -> None:
    registry = load_data_source_registry()
    frame = registry_to_frame(registry)
    categories = set(frame["category"])
    assert LineageCategory.OPEN_DATA.value in categories
    assert LineageCategory.SECURE_INTERNAL_READY_SCHEMA.value in categories
    assert LineageCategory.SECURE_INTERNAL_PLACEHOLDER.value in categories
    assert {"ahs_public_wait_times", "tb_ed_visits", "chart_review_semantic_views"}.issubset(set(frame["source_id"]))


def test_public_open_data_cache_has_expected_frames(tmp_path) -> None:
    ensure_public_open_data(tmp_path, force=True)
    data = load_public_open_data(tmp_path)
    expected = {
        "facility_reference",
        "public_wait_times",
        "historical_public_ed_metrics",
        "respiratory_surveillance",
        "environmental_stress",
        "travel_friction",
        "calendar_context",
        "population_context",
    }
    assert expected.issubset(data.keys())
    assert all(not data[name].empty for name in expected)


def test_public_pressure_index_is_site_level_and_non_identifying(tmp_path) -> None:
    ensure_public_open_data(tmp_path, force=True)
    pressure = public_pressure_index(load_public_open_data(tmp_path))
    assert {"facility", "zone", "latitude", "longitude", "public_pressure_index", "pressure_band"}.issubset(pressure.columns)
    assert pressure["public_pressure_index"].between(0, 1).all()
    assert "PATIENT_CHART" not in pressure.columns

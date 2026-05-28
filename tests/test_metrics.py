from __future__ import annotations

from ed_flow.local_backend import LocalBackend
from ed_flow.metrics import bottleneck_summary, calculate_data_quality, current_state_metrics
from ed_flow.synthetic_data import write_synthetic_data


def test_metrics_calculations_work(tmp_path) -> None:
    write_synthetic_data(tmp_path, force=True)
    backend = LocalBackend(tmp_path)
    visits = backend.load_ed_visits()
    active = backend.load_current_active_visits()

    quality = calculate_data_quality(backend.load_ed_visits(filters=None))
    metrics = current_state_metrics(active, visits)
    bottlenecks = bottleneck_summary(active, visits)

    assert quality.row_count > 0
    assert metrics["arrivals"] == len(visits)
    assert "median_ed_los" in metrics
    assert not bottlenecks.empty


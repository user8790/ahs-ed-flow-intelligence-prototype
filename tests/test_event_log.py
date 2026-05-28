from __future__ import annotations

from ed_flow.event_log import construct_event_log, observed_concurrency, reconstruct_stage_intervals
from ed_flow.feature_engineering import apply_default_business_rules
from ed_flow.synthetic_data import generate_synthetic_ed_visits


def test_event_log_construction_works() -> None:
    visits = apply_default_business_rules(generate_synthetic_ed_visits(n_visits=120, seed=201))

    event_log = construct_event_log(visits)

    assert not event_log.empty
    assert {"DATA_RECORD_ID", "event_type", "event_datetime"}.issubset(event_log.columns)
    assert event_log["event_type"].isin(["first_contact", "triage", "depart_ed"]).any()


def test_stage_reconstruction_and_concurrency_work() -> None:
    visits = apply_default_business_rules(generate_synthetic_ed_visits(n_visits=140, seed=202))

    intervals = reconstruct_stage_intervals(visits)
    concurrency = observed_concurrency(intervals)

    assert not intervals.empty
    assert "duration_hrs" in intervals.columns
    assert not concurrency.empty
    assert {"timestamp", "stage", "concurrency"}.issubset(concurrency.columns)


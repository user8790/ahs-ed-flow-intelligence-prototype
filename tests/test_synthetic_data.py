from __future__ import annotations

import pandas as pd

from ed_flow.data_contracts import TB_ED_VISITS_COLUMNS
from ed_flow.feature_engineering import apply_default_business_rules
from ed_flow.synthetic_data import generate_synthetic_ed_visits, generate_waiting_room_patients


def test_synthetic_data_has_required_columns() -> None:
    df = generate_synthetic_ed_visits(n_visits=250, seed=101)

    assert set(TB_ED_VISITS_COLUMNS).issubset(df.columns)
    assert {"Stollery Children's Hospital", "Alberta Children's Hospital"}.intersection(
        set(df["INSTITUTION_NAME"])
    )
    assert df["PATIENT_CHART"].astype(str).str.startswith("SYN-MRN-").all()
    assert df["PATIENT_PHN"].astype(str).str.startswith("SYN-PHN-").all()


def test_timestamps_are_ordered_or_flagged() -> None:
    df = generate_synthetic_ed_visits(n_visits=400, seed=102)
    valid = df[df["INVALID_LOS_CALC_FLAG"] != "Y"].copy()
    pairs = [
        ("FIRST_CONTACT_DATETIME", "REGISTRATION_DATETIME"),
        ("REGISTRATION_DATETIME", "TRIAGE_DATETIME"),
        ("TRIAGE_DATETIME", "INITIAL_ROOMED_IN_DATETIME"),
        ("INITIAL_ROOMED_IN_DATETIME", "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME"),
        ("PHYSICIAN_INITIAL_ASSESSMENT_DATETIME", "DISPOSITION_DATETIME"),
        ("DECISION_TO_ADMIT_DATETIME", "LAST_CONTACT_DATETIME"),
    ]
    for start, end in pairs:
        start_values = pd.to_datetime(valid[start], errors="coerce")
        end_values = pd.to_datetime(valid[end], errors="coerce")
        comparable = start_values.notna() & end_values.notna()
        assert (end_values[comparable] >= start_values[comparable]).all()


def test_invalid_los_rules_work() -> None:
    df = generate_synthetic_ed_visits(n_visits=500, seed=103)
    assert (df["INVALID_LOS_CALC_FLAG"] == "Y").any()

    filtered = apply_default_business_rules(df)

    assert not (filtered["INVALID_LOS_CALC_FLAG"] == "Y").any()
    assert not (filtered["SCHEDULED_ED_VISIT_FLAG"] == "Y").any()


def test_waiting_room_registry_is_synthetic() -> None:
    visits = generate_synthetic_ed_visits(n_visits=300, seed=104)
    waiting = generate_waiting_room_patients(visits, seed=105, n=15)

    assert len(waiting) == 15
    assert waiting["mrn"].astype(str).str.startswith("SYN-MRN-").all()
    assert waiting["current_stage"].notna().all()


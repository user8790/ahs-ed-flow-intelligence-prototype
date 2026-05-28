"""Pragmatic scenario and bed-placement optimization helpers."""

from __future__ import annotations

import pandas as pd


def rank_interventions(comparison: pd.DataFrame) -> pd.DataFrame:
    """Rank scenarios by wait, boarding, LWBS, and implementation friction."""

    if comparison.empty:
        return comparison
    out = comparison.copy()
    out["implementation_friction"] = out["scenario"].apply(
        lambda label: 1
        + int("physicians" in label) * 2
        + int("rooms" in label) * 2
        + int("boarding" in label) * 2
        + int("fast track" in label) * 1
    )
    out["benefit_score"] = (
        -out.get("p90_wait_hrs_mean", 0).astype(float)
        -0.03 * out.get("boarding_hours_mean", 0).astype(float)
        -10 * out.get("lwbs_risk_mean", 0).astype(float)
    )
    out["priority_score"] = out["benefit_score"] / out["implementation_friction"].clip(lower=1)
    return out.sort_values("priority_score", ascending=False).reset_index(drop=True)


def greedy_bed_placement_optimizer(active_patients: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    """Prototype bed-placement optimizer using an inspectable greedy heuristic."""

    if active_patients.empty or capacity.empty:
        return pd.DataFrame(columns=["mrn", "recommended_unit", "priority_reason", "expected_boarding_hours_reduced"])
    boarders = active_patients[active_patients["current_stage"].eq("decision_to_admit_boarder")].copy()
    if boarders.empty:
        boarders = active_patients.sort_values("triage_level").head(5).copy()
    latest_capacity = capacity.sort_values("snapshot_datetime").groupby("facility").tail(1)
    rows = []
    for _, patient in boarders.iterrows():
        facility_capacity = latest_capacity[latest_capacity["facility"] == patient["facility"]]
        available = int(facility_capacity["inpatient_available_beds"].iloc[0]) if not facility_capacity.empty else 0
        if available > 0:
            recommended_unit = "Synthetic pediatric/medicine unit with available bed"
            effect = min(4.0, 0.6 + available * 0.25)
        else:
            recommended_unit = "No immediate bed; prioritize discharge/cleaning cascade"
            effect = 0.4
        rows.append(
            {
                "mrn": patient["mrn"],
                "facility": patient["facility"],
                "recommended_unit": recommended_unit,
                "priority_reason": f"CTAS {patient['triage_level']} patient in {patient['current_stage']}",
                "expected_boarding_hours_reduced": round(float(effect), 2),
                "constraint_note": "Synthetic heuristic; governed pilot should validate placement constraints and unit rules.",
            }
        )
    return pd.DataFrame(rows).sort_values("expected_boarding_hours_reduced", ascending=False)


def staffing_sensitivity(active: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    """Estimate marginal impact of staffing changes for the expanded module."""

    if capacity.empty:
        return pd.DataFrame()
    latest = capacity.sort_values("snapshot_datetime").groupby("facility").tail(1)
    queue_pressure = active.groupby("facility").size().rename("active_patients").reset_index()
    merged = latest.merge(queue_pressure, on="facility", how="left").fillna({"active_patients": 0})
    rows = []
    for _, row in merged.iterrows():
        active_count = float(row["active_patients"])
        nurses = max(float(row["nurses_on_shift"]), 1.0)
        physicians = max(float(row["physicians_on_shift"]), 1.0)
        rows.append(
            {
                "facility": row["facility"],
                "add_one_nurse_estimated_wait_reduction_mins": round(active_count / nurses * 4.5, 1),
                "add_one_physician_estimated_pia_reduction_mins": round(active_count / physicians * 7.5, 1),
                "current_consult_queue": int(row["consult_queue"]),
                "implementation_note": "Sensitivity is synthetic and should be recalibrated with roster and timestamp validation.",
            }
        )
    return pd.DataFrame(rows)


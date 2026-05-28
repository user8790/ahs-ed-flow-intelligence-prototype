"""Operational metrics for the command centre and validation views."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ed_flow.data_contracts import DataQualityReport, TIMESTAMP_COLUMNS
from ed_flow.utils import ensure_datetime, safe_divide


def calculate_data_quality(df: pd.DataFrame) -> DataQualityReport:
    """Summarize data quality and freshness signals."""

    visits = ensure_datetime(df, TIMESTAMP_COLUMNS)
    invalid = int(visits.get("INVALID_LOS_CALC_FLAG", pd.Series([], dtype=str)).fillna("N").eq("Y").sum())
    scheduled = int(visits.get("SCHEDULED_ED_VISIT_FLAG", pd.Series([], dtype=str)).fillna("N").eq("Y").sum())
    missing_first = int(visits.get("FIRST_CONTACT_DATETIME", pd.Series([], dtype="datetime64[ns]")).isna().sum())
    max_update = None
    if "ROW_UPDATE_DATETIME" in visits and visits["ROW_UPDATE_DATETIME"].notna().any():
        max_update = visits["ROW_UPDATE_DATETIME"].max().to_pydatetime()
    warnings = []
    if invalid:
        warnings.append(f"{invalid} records are flagged invalid for LOS and are excluded by default.")
    if scheduled:
        warnings.append(f"{scheduled} scheduled ED/UCC/AACC visits are excluded by default.")
    if missing_first:
        warnings.append(f"{missing_first} records are missing FIRST_CONTACT_DATETIME.")
    if not warnings:
        warnings.append("Synthetic data passed core freshness and LOS screening checks.")
    return DataQualityReport(
        row_count=int(len(visits)),
        invalid_los_count=invalid,
        missing_first_contact_count=missing_first,
        scheduled_visit_count=scheduled,
        max_row_update_datetime=max_update,
        warnings=warnings,
    )


def current_state_metrics(active: pd.DataFrame, visits: pd.DataFrame) -> dict[str, float | int | str]:
    """Calculate current-state command-centre metrics."""

    stages = active.get("current_stage", pd.Series([], dtype=str)).fillna("")
    los = pd.to_numeric(visits.get("ED_LOS_HRS", pd.Series([], dtype=float)), errors="coerce")
    admitted = visits.get("DISPOSITION_GROUP", pd.Series([], dtype=str)).eq("Admitted")
    discharged = visits.get("DISPOSITION_GROUP", pd.Series([], dtype=str)).eq("Discharged")
    total = max(len(visits), 1)
    lwbs_values = pd.to_numeric(active.get("lwbs_risk", pd.Series([], dtype=float)), errors="coerce").dropna()
    metrics = {
        "arrivals": int(len(visits)),
        "waiting_to_triage": int(stages.eq("waiting_to_triage").sum()),
        "triaged_waiting": int(stages.eq("triaged_waiting").sum()),
        "roomed_not_seen": int(stages.eq("roomed_not_seen").sum()),
        "waiting_for_physician_initial_assessment": int(stages.eq("waiting_for_physician_initial_assessment").sum()),
        "consult_delay": int(stages.eq("consult_delay").sum()),
        "decision_to_admit_boarders": int(stages.eq("decision_to_admit_boarder").sum()),
        "ems_offload_delay": int(stages.eq("ems_offload_delay").sum()),
        "admitted_within_8_hours": float(visits.get("ADMITTED_WITHIN_8HRS_FLAG", pd.Series([], dtype=str)).eq("Y").sum() / max(admitted.sum(), 1)),
        "discharged_within_4_hours": float(visits.get("DISCHARGED_WITHIN_4HRS_FLAG", pd.Series([], dtype=str)).eq("Y").sum() / max(discharged.sum(), 1)),
        "lwbs_risk": float(lwbs_values.mean()) if not lwbs_values.empty else 0.0,
        "median_ed_los": float(los.dropna().median()) if los.notna().any() else 0.0,
        "p90_ed_los": float(los.dropna().quantile(0.9)) if los.notna().any() else 0.0,
        "admission_rate": safe_divide(float(admitted.sum()), float(total)),
        "discharge_rate": safe_divide(float(discharged.sum()), float(total)),
    }
    return metrics


def bottleneck_summary(active: pd.DataFrame, visits: pd.DataFrame) -> pd.DataFrame:
    """Rank likely current operational bottlenecks."""

    metrics = current_state_metrics(active, visits)
    rows = [
        {
            "constraint": "Waiting room to rooming",
            "signal": metrics["triaged_waiting"] + metrics["waiting_to_triage"],
            "why_it_matters": "Long pre-rooming queues raise LWBS risk and delay treatment starts.",
        },
        {
            "constraint": "Physician initial assessment",
            "signal": metrics["roomed_not_seen"] + metrics["waiting_for_physician_initial_assessment"],
            "why_it_matters": "Roomed patients waiting for PIA occupy spaces without progressing diagnostics or disposition.",
        },
        {
            "constraint": "Consult turnaround",
            "signal": metrics["consult_delay"],
            "why_it_matters": "Consult waits delay disposition for high-acuity and admission-likely patients.",
        },
        {
            "constraint": "Inpatient bed availability",
            "signal": metrics["decision_to_admit_boarders"],
            "why_it_matters": "Boarding consumes ED spaces and shifts the bottleneck back to rooming.",
        },
        {
            "constraint": "EMS offload",
            "signal": metrics["ems_offload_delay"],
            "why_it_matters": "Offload delay affects EMS availability and early ED processing.",
        },
    ]
    out = pd.DataFrame(rows)
    out["signal"] = pd.to_numeric(out["signal"], errors="coerce").fillna(0)
    out["priority"] = out["signal"].rank(method="dense", ascending=False).astype(int)
    return out.sort_values(["priority", "constraint"]).reset_index(drop=True)


def los_summary_by_facility(df: pd.DataFrame) -> pd.DataFrame:
    """Facility-level LOS and outcome summary."""

    if df.empty:
        return pd.DataFrame()
    grouped = df.groupby("INSTITUTION_NAME", dropna=False)
    rows = []
    for facility, group in grouped:
        los = pd.to_numeric(group["ED_LOS_HRS"], errors="coerce").dropna()
        rows.append(
            {
                "facility": facility,
                "visits": int(len(group)),
                "median_los_hrs": float(los.median()) if not los.empty else np.nan,
                "p90_los_hrs": float(los.quantile(0.9)) if not los.empty else np.nan,
                "admission_rate": float(group["DISPOSITION_GROUP"].eq("Admitted").mean()),
                "lwbs_rate": float(group["DISPOSITION_GROUP"].eq("LWBS").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("visits", ascending=False)


def validation_metric_summary(observed: pd.DataFrame, simulated: pd.DataFrame) -> pd.DataFrame:
    """Compare observed and simulated headline metrics."""

    def summarize(frame: pd.DataFrame, label: str) -> dict[str, float | str]:
        los_col = "ED_LOS_HRS" if "ED_LOS_HRS" in frame else "ed_los_hrs"
        wait_col = "wait_to_physician_hrs" if "wait_to_physician_hrs" in frame else los_col
        los = pd.to_numeric(frame.get(los_col, pd.Series([], dtype=float)), errors="coerce").dropna()
        wait = pd.to_numeric(frame.get(wait_col, pd.Series([], dtype=float)), errors="coerce").dropna()
        return {
            "source": label,
            "n": int(len(frame)),
            "median_los_hrs": float(los.median()) if not los.empty else np.nan,
            "p90_los_hrs": float(los.quantile(0.9)) if not los.empty else np.nan,
            "median_wait_hrs": float(wait.median()) if not wait.empty else np.nan,
            "p90_wait_hrs": float(wait.quantile(0.9)) if not wait.empty else np.nan,
        }

    return pd.DataFrame([summarize(observed, "observed"), summarize(simulated, "simulated")])

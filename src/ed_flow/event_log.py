"""Event-log construction and queue/stage reconstruction."""

from __future__ import annotations

import pandas as pd

from ed_flow.data_contracts import TIMESTAMP_COLUMNS
from ed_flow.utils import ensure_datetime


EVENT_MAPPINGS: list[tuple[str, str]] = [
    ("FIRST_CONTACT_DATETIME", "first_contact"),
    ("REGISTRATION_DATETIME", "registration"),
    ("TRIAGE_DATETIME", "triage"),
    ("EMS_OFFLOAD_DATETIME", "ems_offload"),
    ("INITIAL_ROOMED_IN_DATETIME", "roomed"),
    ("PHYSICIAN_INITIAL_ASSESSMENT_DATETIME", "physician_initial_assessment"),
    ("INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME", "consult_request"),
    ("INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME", "consult_completed"),
    ("DISPOSITION_DATETIME", "disposition"),
    ("DECISION_TO_ADMIT_DATETIME", "decision_to_admit"),
    ("IP_BED_ASSIGN_DATETIME", "ip_bed_assignment"),
    ("DEPART_ED_DATETIME", "depart_ed"),
    ("LAST_CONTACT_DATETIME", "last_contact"),
]

STAGE_INTERVALS: list[tuple[str, str, str]] = [
    ("arrival_to_registration", "FIRST_CONTACT_DATETIME", "REGISTRATION_DATETIME"),
    ("registration_to_triage", "REGISTRATION_DATETIME", "TRIAGE_DATETIME"),
    ("triaged_waiting", "TRIAGE_DATETIME", "INITIAL_ROOMED_IN_DATETIME"),
    ("roomed_waiting_physician", "INITIAL_ROOMED_IN_DATETIME", "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME"),
    ("treatment_diagnostics_consults", "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME", "DISPOSITION_DATETIME"),
    ("consult_delay", "INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME", "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME"),
    ("decision_to_admit_boarding", "DECISION_TO_ADMIT_DATETIME", "LAST_CONTACT_DATETIME"),
    ("disposition_to_departure", "DISPOSITION_DATETIME", "DEPART_ED_DATETIME"),
]


def construct_event_log(df: pd.DataFrame) -> pd.DataFrame:
    """Transform one-row-per-visit data into a long event log."""

    visits = ensure_datetime(df, TIMESTAMP_COLUMNS)
    rows = []
    for _, row in visits.iterrows():
        record_id = row.get("DATA_RECORD_ID")
        for column, event_type in EVENT_MAPPINGS:
            if column in visits.columns and pd.notna(row.get(column)):
                rows.append(
                    {
                        "DATA_RECORD_ID": record_id,
                        "event_type": event_type,
                        "event_datetime": row[column],
                        "facility": row.get("INSTITUTION_NAME"),
                        "triage_level": row.get("TRIAGE_LEVEL"),
                        "disposition": row.get("DISPOSITION_GROUP"),
                    }
                )
    if not rows:
        return pd.DataFrame(columns=["DATA_RECORD_ID", "event_type", "event_datetime"])
    return pd.DataFrame(rows).sort_values(["DATA_RECORD_ID", "event_datetime"]).reset_index(drop=True)


def reconstruct_stage_intervals(df: pd.DataFrame) -> pd.DataFrame:
    """Create visit-stage intervals suitable for concurrency and validation."""

    visits = ensure_datetime(df, TIMESTAMP_COLUMNS)
    rows = []
    for _, row in visits.iterrows():
        invalid = row.get("INVALID_LOS_CALC_FLAG") == "Y"
        for stage, start_col, end_col in STAGE_INTERVALS:
            if start_col not in visits.columns or end_col not in visits.columns:
                continue
            start = row.get(start_col)
            end = row.get(end_col)
            if pd.isna(start) or pd.isna(end):
                continue
            duration_hrs = (end - start).total_seconds() / 3600
            rows.append(
                {
                    "DATA_RECORD_ID": row.get("DATA_RECORD_ID"),
                    "stage": stage,
                    "start_datetime": start,
                    "end_datetime": end,
                    "duration_hrs": duration_hrs,
                    "facility": row.get("INSTITUTION_NAME"),
                    "triage_level": row.get("TRIAGE_LEVEL"),
                    "invalid_or_reversed": bool(invalid or duration_hrs < 0),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "DATA_RECORD_ID",
                "stage",
                "start_datetime",
                "end_datetime",
                "duration_hrs",
                "invalid_or_reversed",
            ]
        )
    return pd.DataFrame(rows).reset_index(drop=True)


def observed_concurrency(intervals: pd.DataFrame, freq: str = "1h") -> pd.DataFrame:
    """Estimate concurrency by stage over regular time buckets."""

    if intervals.empty:
        return pd.DataFrame(columns=["timestamp", "stage", "concurrency"])
    clean = intervals[~intervals["invalid_or_reversed"]].copy()
    clean = clean.dropna(subset=["start_datetime", "end_datetime"])
    if clean.empty:
        return pd.DataFrame(columns=["timestamp", "stage", "concurrency"])
    start = clean["start_datetime"].min().floor(freq)
    end = clean["end_datetime"].max().ceil(freq)
    timestamps = pd.date_range(start, end, freq=freq)
    rows = []
    for stage, group in clean.groupby("stage"):
        for ts in timestamps:
            rows.append(
                {
                    "timestamp": ts,
                    "stage": stage,
                    "concurrency": int(((group["start_datetime"] <= ts) & (group["end_datetime"] > ts)).sum()),
                }
            )
    return pd.DataFrame(rows)


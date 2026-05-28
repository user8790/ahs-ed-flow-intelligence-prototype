"""Constrained feature engineering using only TB_ED_VISITS contract columns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ed_flow.data_contracts import TIMESTAMP_COLUMNS, constrained_projection
from ed_flow.utils import ensure_datetime, hours_between


def apply_default_business_rules(
    df: pd.DataFrame,
    include_scheduled: bool = False,
    include_invalid_los: bool = False,
) -> pd.DataFrame:
    """Apply default LOS and scheduled-visit rules."""

    out = df.copy()
    if not include_invalid_los and "INVALID_LOS_CALC_FLAG" in out:
        out = out[out["INVALID_LOS_CALC_FLAG"].fillna("N") != "Y"]
    if not include_scheduled and "SCHEDULED_ED_VISIT_FLAG" in out:
        out = out[out["SCHEDULED_ED_VISIT_FLAG"].fillna("N") != "Y"]
    return out.reset_index(drop=True)


def add_flow_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add portable duration and calendar features derived from visit timestamps."""

    out = ensure_datetime(constrained_projection(df), TIMESTAMP_COLUMNS)
    if "FIRST_CONTACT_DATETIME" in out:
        out["arrival_hour"] = out["FIRST_CONTACT_DATETIME"].dt.hour
        out["arrival_day_of_week"] = out["FIRST_CONTACT_DATETIME"].dt.day_name()
        out["arrival_date"] = out["FIRST_CONTACT_DATETIME"].dt.date
    pairs = {
        "registration_wait_mins": ("FIRST_CONTACT_DATETIME", "REGISTRATION_DATETIME"),
        "triage_wait_mins": ("REGISTRATION_DATETIME", "TRIAGE_DATETIME"),
        "rooming_wait_hrs": ("TRIAGE_DATETIME", "INITIAL_ROOMED_IN_DATETIME"),
        "physician_wait_hrs": ("INITIAL_ROOMED_IN_DATETIME", "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME"),
        "consult_delay_hrs": ("INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME", "INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME"),
        "boarding_delay_hrs": ("DECISION_TO_ADMIT_DATETIME", "LAST_CONTACT_DATETIME"),
    }
    for new_col, (start, end) in pairs.items():
        if start in out and end in out:
            factor = 60 if new_col.endswith("_mins") else 1
            out[new_col] = hours_between(out[start], out[end]) * factor
    out["was_admitted"] = out.get("DISPOSITION_GROUP", pd.Series("", index=out.index)).eq("Admitted")
    out["was_discharged"] = out.get("DISPOSITION_GROUP", pd.Series("", index=out.index)).eq("Discharged")
    out["was_lwbs"] = out.get("DISPOSITION_GROUP", pd.Series("", index=out.index)).eq("LWBS")
    out["was_transferred"] = out.get("DISPOSITION_GROUP", pd.Series("", index=out.index)).eq("Transferred")
    return out


def arrival_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize facility/hour/day/triage/age/complaint arrival patterns."""

    featured = add_flow_features(df)
    group_cols = [
        "INSTITUTION_NAME",
        "arrival_day_of_week",
        "arrival_hour",
        "TRIAGE_LEVEL",
        "PATIENT_AGE_GROUP",
        "PRESENTING_COMPLAINT",
        "ARRIVAL_MODE",
    ]
    present = [col for col in group_cols if col in featured.columns]
    return featured.groupby(present, dropna=False).size().reset_index(name="arrivals")


def route_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate route/disposition probabilities by interpretable cohorts."""

    featured = add_flow_features(df)
    group_cols = ["INSTITUTION_NAME", "TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "PRESENTING_COMPLAINT"]
    present = [col for col in group_cols if col in featured.columns]
    counts = featured.groupby(present + ["DISPOSITION_GROUP"], dropna=False).size().reset_index(name="n")
    totals = counts.groupby(present, dropna=False)["n"].transform("sum")
    counts["probability"] = counts["n"] / totals
    return counts.sort_values("n", ascending=False)


def stage_duration_distributions(df: pd.DataFrame) -> pd.DataFrame:
    """Return median/p90 duration distributions for reconstructed stages."""

    featured = add_flow_features(df)
    duration_cols = [
        "registration_wait_mins",
        "triage_wait_mins",
        "rooming_wait_hrs",
        "physician_wait_hrs",
        "consult_delay_hrs",
        "boarding_delay_hrs",
        "ED_LOS_HRS",
        "ED_LOS_ADMITTED_HRS",
        "ED_LOS_DISCHARGED_HRS",
    ]
    rows = []
    for col in duration_cols:
        if col not in featured:
            continue
        values = pd.to_numeric(featured[col], errors="coerce")
        values = values[(values >= 0) & np.isfinite(values)]
        if values.empty:
            continue
        rows.append(
            {
                "stage": col,
                "n": int(values.count()),
                "median": float(values.median()),
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.9)),
                "mean": float(values.mean()),
            }
        )
    return pd.DataFrame(rows)


def estimate_baseline_parameters(df: pd.DataFrame) -> dict[str, float | int | dict[str, float]]:
    """Infer transparent baseline simulation parameters from constrained data."""

    featured = add_flow_features(df)
    valid = featured.dropna(subset=["FIRST_CONTACT_DATETIME"]).copy()
    if valid.empty:
        return {
            "arrival_rate_per_hour": 2.0,
            "triage_capacity": 2,
            "room_capacity": 18,
            "physician_capacity": 5,
        }
    elapsed_hours = max(
        (valid["FIRST_CONTACT_DATETIME"].max() - valid["FIRST_CONTACT_DATETIME"].min()).total_seconds() / 3600,
        1,
    )
    rate = len(valid) / elapsed_hours
    demo_rate = max(float(rate), 3.0)
    durations = stage_duration_distributions(valid)

    def median_for(stage: str, default: float) -> float:
        match = durations[durations["stage"] == stage]
        if match.empty:
            return default
        return float(match["median"].iloc[0])

    arrival_by_triage = valid["TRIAGE_LEVEL"].value_counts(normalize=True).sort_index().to_dict()
    disposition_probs = valid["DISPOSITION_GROUP"].value_counts(normalize=True).to_dict()
    consult_probability = float((pd.to_numeric(valid.get("CONSULT_COUNT", 0), errors="coerce").fillna(0) > 0).mean())
    return {
        "arrival_rate_per_hour": demo_rate,
        "observed_historical_arrival_rate_per_hour": float(rate),
        "triage_capacity": int(max(1, np.ceil(demo_rate * 0.25))),
        "room_capacity": int(max(8, np.ceil(demo_rate * median_for("rooming_wait_hrs", 1.0) * 1.2))),
        "physician_capacity": int(max(2, np.ceil(demo_rate * median_for("physician_wait_hrs", 0.6) * 0.7))),
        "registration_median_mins": median_for("registration_wait_mins", 8),
        "triage_service_median_mins": max(median_for("triage_wait_mins", 10), 4),
        "rooming_wait_median_hrs": median_for("rooming_wait_hrs", 1.0),
        "physician_wait_median_hrs": median_for("physician_wait_hrs", 0.6),
        "consult_delay_median_hrs": median_for("consult_delay_hrs", 2.0),
        "boarding_delay_median_hrs": median_for("boarding_delay_hrs", 4.0),
        "ed_los_median_hrs": median_for("ED_LOS_HRS", 5.0),
        "discharged_los_median_hrs": median_for("ED_LOS_DISCHARGED_HRS", 3.5),
        "admitted_los_median_hrs": median_for("ED_LOS_ADMITTED_HRS", 8.0),
        "arrival_by_triage": {str(k): float(v) for k, v in arrival_by_triage.items()},
        "disposition_probs": {str(k): float(v) for k, v in disposition_probs.items()},
        "consult_probability": consult_probability,
    }

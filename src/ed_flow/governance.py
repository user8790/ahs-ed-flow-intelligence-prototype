"""Validation and governance utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from ed_flow.data_contracts import TIMESTAMP_COLUMNS
from ed_flow.feature_engineering import add_flow_features
from ed_flow.metrics import calculate_data_quality
from ed_flow.utils import ensure_datetime


def holdout_split_by_date(df: pd.DataFrame, holdout_fraction: float = 0.25) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create chronological train/holdout split."""

    visits = ensure_datetime(df, TIMESTAMP_COLUMNS).dropna(subset=["FIRST_CONTACT_DATETIME"]).sort_values("FIRST_CONTACT_DATETIME")
    if visits.empty:
        return visits.copy(), visits.copy()
    split_idx = max(1, int(len(visits) * (1 - holdout_fraction)))
    return visits.iloc[:split_idx].copy(), visits.iloc[split_idx:].copy()


def facility_calibration_table(df: pd.DataFrame) -> pd.DataFrame:
    """Facility-level calibration summary for governance review."""

    featured = add_flow_features(df)
    rows = []
    for facility, group in featured.groupby("INSTITUTION_NAME", dropna=False):
        los = pd.to_numeric(group["ED_LOS_HRS"], errors="coerce").dropna()
        rows.append(
            {
                "facility": facility,
                "n": int(len(group)),
                "observed_admission_rate": float(group["was_admitted"].mean()),
                "observed_lwbs_rate": float(group["was_lwbs"].mean()),
                "median_los_hrs": float(los.median()) if not los.empty else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("n", ascending=False)


def admission_lwbs_calibration(df: pd.DataFrame) -> pd.DataFrame:
    """Train simple interpretable disposition models and return calibration bins."""

    featured = add_flow_features(df).dropna(subset=["TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "PRESENTING_COMPLAINT"])
    if len(featured) < 50:
        return pd.DataFrame()
    x = featured[["TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "PRESENTING_COMPLAINT", "ARRIVAL_MODE"]].astype(str)
    y = featured["was_admitted"].astype(int)
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        encoded = encoder.fit_transform(x)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        encoded = encoder.fit_transform(x)
    x_train, x_test, y_train, y_test = train_test_split(encoded, y, test_size=0.25, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=500)
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    bins = pd.qcut(probabilities, q=min(5, len(np.unique(probabilities))), duplicates="drop")
    table = (
        pd.DataFrame({"predicted_probability": probabilities, "observed": y_test.to_numpy(), "bin": bins})
        .groupby("bin", observed=False)
        .agg(
            n=("observed", "size"),
            mean_predicted_probability=("predicted_probability", "mean"),
            observed_admission_rate=("observed", "mean"),
        )
        .reset_index()
    )
    table["brier_score"] = brier_score_loss(y_test, probabilities)
    return table.astype({"bin": str})


def missing_timestamp_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Quantify missing key timestamps."""

    visits = ensure_datetime(df, TIMESTAMP_COLUMNS)
    key_cols = [
        "FIRST_CONTACT_DATETIME",
        "REGISTRATION_DATETIME",
        "TRIAGE_DATETIME",
        "INITIAL_ROOMED_IN_DATETIME",
        "PHYSICIAN_INITIAL_ASSESSMENT_DATETIME",
        "DISPOSITION_DATETIME",
        "DEPART_ED_DATETIME",
    ]
    rows = []
    for col in key_cols:
        if col in visits:
            rows.append({"timestamp": col, "missing_count": int(visits[col].isna().sum()), "missing_rate": float(visits[col].isna().mean())})
    return pd.DataFrame(rows)


def drift_checks(train: pd.DataFrame, holdout: pd.DataFrame) -> pd.DataFrame:
    """Simple distribution-drift checks for high-value categorical fields."""

    rows = []
    for col in ["TRIAGE_LEVEL", "PATIENT_AGE_GROUP", "DISPOSITION_GROUP", "ARRIVAL_MODE"]:
        if col not in train or col not in holdout:
            continue
        train_dist = train[col].value_counts(normalize=True)
        holdout_dist = holdout[col].value_counts(normalize=True)
        labels = sorted(set(train_dist.index).union(holdout_dist.index))
        drift = sum(abs(float(train_dist.get(label, 0)) - float(holdout_dist.get(label, 0))) for label in labels) / 2
        rows.append({"field": col, "population_stability_proxy": round(float(drift), 4), "review_flag": drift > 0.12})
    return pd.DataFrame(rows)


def governance_summary(df: pd.DataFrame) -> dict[str, object]:
    """Bundle validation and governance outputs for the app."""

    train, holdout = holdout_split_by_date(df)
    return {
        "data_quality": calculate_data_quality(df),
        "train_count": int(len(train)),
        "holdout_count": int(len(holdout)),
        "facility_calibration": facility_calibration_table(df),
        "admission_calibration": admission_lwbs_calibration(df),
        "missing_timestamps": missing_timestamp_checks(df),
        "drift": drift_checks(train, holdout),
        "explainability": [
            "Empirical distributions drive simulation parameters before any model layer is used.",
            "Disposition calibration uses interpretable logistic regression for admission probability review.",
            "AI-generated narratives are limited to summarization/explanation and are not sources of truth.",
        ],
        "audit_log_design": [
            "Record user, timestamp, facility filter, scenario inputs, data extract version, model provider, and output hash.",
            "Persist chart-summary prompts/responses only in approved secure environments with PHI controls.",
            "Retain simulation seeds and parameter snapshots for reproducibility.",
        ],
    }

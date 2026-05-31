"""Hybrid public/open-data and internal-ready forecasting helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def public_pressure_index(public_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine public-context features into a site-level pressure index."""

    facilities = public_data.get("facility_reference", pd.DataFrame()).copy()
    if facilities.empty:
        return pd.DataFrame()
    wait = _latest_by_facility(public_data.get("public_wait_times", pd.DataFrame()), "posted_timestamp")
    env = _latest_by_facility(public_data.get("environmental_stress", pd.DataFrame()), "timestamp")
    travel = _latest_by_facility(public_data.get("travel_friction", pd.DataFrame()), "timestamp")
    respiratory = public_data.get("respiratory_surveillance", pd.DataFrame()).copy()
    if not respiratory.empty:
        respiratory = respiratory.sort_values("week_start").groupby("zone", as_index=False).tail(4)
        respiratory = respiratory.groupby("zone", as_index=False)["pediatric_pressure_index"].mean()
    merged = facilities.merge(wait[["facility", "estimated_wait_mins"]], on="facility", how="left")
    merged = merged.merge(env[["facility", "aqhi", "environmental_stress_index", "weather_alert_count"]], on="facility", how="left")
    merged = merged.merge(travel[["facility", "travel_friction_index", "road_incidents"]], on="facility", how="left")
    merged = merged.merge(respiratory, on="zone", how="left")
    for column in [
        "estimated_wait_mins",
        "aqhi",
        "environmental_stress_index",
        "weather_alert_count",
        "travel_friction_index",
        "road_incidents",
        "pediatric_pressure_index",
    ]:
        if column not in merged:
            merged[column] = 0
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0)
    merged["public_pressure_index"] = (
        np.clip(merged["estimated_wait_mins"] / 220, 0, 1) * 0.35
        + merged["environmental_stress_index"] * 0.2
        + merged["travel_friction_index"] * 0.18
        + np.clip(merged["pediatric_pressure_index"], 0, 1) * 0.2
        + np.clip(merged["weather_alert_count"] / 4, 0, 1) * 0.07
    )
    merged["pressure_band"] = pd.cut(
        merged["public_pressure_index"],
        bins=[-0.01, 0.35, 0.62, 1.01],
        labels=["Watch", "Pressure", "High pressure"],
    ).astype(str)
    return merged.sort_values("public_pressure_index", ascending=False).reset_index(drop=True)


def hybrid_arrival_forecast(
    visits: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
    horizon_hours: int = 24,
) -> pd.DataFrame:
    """Build a transparent hybrid forecast from empirical arrivals and open pressure context."""

    visit_view = visits[visits["INSTITUTION_NAME"] == facility].copy() if "INSTITUTION_NAME" in visits else visits.copy()
    if visit_view.empty:
        base_rate = 2.0
    else:
        visit_view["FIRST_CONTACT_DATETIME"] = pd.to_datetime(visit_view["FIRST_CONTACT_DATETIME"], errors="coerce")
        hourly = visit_view.dropna(subset=["FIRST_CONTACT_DATETIME"]).copy()
        hourly["hour"] = hourly["FIRST_CONTACT_DATETIME"].dt.hour
        base_rate = max(float(hourly.groupby("hour").size().mean()), 0.5)
    pressure = public_pressure_index(public_data)
    site_pressure = 0.35
    if not pressure.empty and facility in pressure["facility"].values:
        site_pressure = float(pressure.loc[pressure["facility"] == facility, "public_pressure_index"].iloc[0])
    rows = []
    for hour in range(horizon_hours):
        diurnal = 1.0 + 0.24 * np.sin((hour - 9) / 24 * 2 * np.pi)
        pressure_multiplier = 1.0 + 0.55 * site_pressure
        expected = max(base_rate * diurnal * pressure_multiplier, 0.1)
        rows.append(
            {
                "hour_ahead": hour + 1,
                "expected_arrivals": expected,
                "p10_arrivals": max(expected * 0.72, 0),
                "p90_arrivals": expected * 1.32,
                "public_pressure_index": site_pressure,
                "lineage": "HYBRID_OPEN_SYNTHETIC",
            }
        )
    return pd.DataFrame(rows)


def likely_binding_constraints(
    active: pd.DataFrame,
    capacity: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
) -> pd.DataFrame:
    """Forecast likely operational constraints from synthetic expanded feeds and public pressure."""

    active_view = active[active.get("facility", pd.Series(dtype=str)) == facility].copy() if not active.empty else active
    capacity_view = capacity[capacity.get("facility", pd.Series(dtype=str)) == facility].copy() if not capacity.empty else capacity
    pressure = public_pressure_index(public_data)
    pressure_value = float(pressure.loc[pressure["facility"] == facility, "public_pressure_index"].iloc[0]) if not pressure.empty and facility in pressure["facility"].values else 0.35
    latest = capacity_view.sort_values("snapshot_datetime").tail(1) if "snapshot_datetime" in capacity_view else pd.DataFrame()
    boarders = int(active_view.get("current_stage", pd.Series(dtype=str)).eq("decision_to_admit_boarder").sum())
    consult = int(active_view.get("current_stage", pd.Series(dtype=str)).eq("consult_delay").sum())
    rooms = int(active_view.get("current_stage", pd.Series(dtype=str)).isin(["triaged_waiting", "roomed_not_seen"]).sum())
    available_beds = int(latest["inpatient_available_beds"].iloc[0]) if not latest.empty and "inpatient_available_beds" in latest else 3
    rows = [
        ("Inpatient bed availability", boarders + max(0, 8 - available_beds), "Boarding reduces ED treatment-space turnover."),
        ("Physician initial assessment", rooms + int(pressure_value * 6), "Rising arrivals increase roomed-not-seen and PIA waits."),
        ("Consult turnaround", consult + int(pressure_value * 4), "Consult queues bind when high-acuity and admitted routes increase."),
        ("Travel and EMS access", int(pressure_value * 10), "Weather, smoke, road, and transit disruptions may change arrival mode and timing."),
    ]
    out = pd.DataFrame(rows, columns=["constraint", "risk_score", "interpretation"])
    out["uncertainty_band"] = np.where(out["risk_score"] >= out["risk_score"].quantile(0.75), "wide", "moderate")
    return out.sort_values("risk_score", ascending=False).reset_index(drop=True)


def _latest_by_facility(frame: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    if frame.empty or timestamp_col not in frame or "facility" not in frame:
        return pd.DataFrame({"facility": []})
    return frame.sort_values(timestamp_col).groupby("facility", as_index=False).tail(1)

"""Lightweight interpretable forecasts for operational constraints."""

from __future__ import annotations

import pandas as pd

from ed_flow.feature_engineering import add_flow_features
from ed_flow.metrics import bottleneck_summary


def hourly_arrival_forecast(df: pd.DataFrame, facility: str | None = None, horizon_hours: int = 24) -> pd.DataFrame:
    """Simple empirical hourly forecast using historical hour-of-week averages."""

    visits = add_flow_features(df)
    if facility:
        visits = visits[visits["INSTITUTION_NAME"] == facility]
    if visits.empty:
        return pd.DataFrame({"hour_ahead": range(horizon_hours), "expected_arrivals": [0.0] * horizon_hours})
    by_hour = visits.groupby("arrival_hour").size()
    average = by_hour.reindex(range(24), fill_value=by_hour.mean()).astype(float)
    start_hour = int(visits["arrival_hour"].max() if visits["arrival_hour"].notna().any() else 0)
    rows = []
    for h in range(horizon_hours):
        hour = (start_hour + h + 1) % 24
        rows.append({"hour_ahead": h + 1, "clock_hour": hour, "expected_arrivals": float(average.loc[hour])})
    return pd.DataFrame(rows)


def next_constraint_forecast(active: pd.DataFrame, visits: pd.DataFrame) -> pd.DataFrame:
    """Forecast the next likely constraint using current queues and arrival pressure."""

    bottlenecks = bottleneck_summary(active, visits).copy()
    forecast = hourly_arrival_forecast(visits, horizon_hours=6)
    arrival_pressure = float(forecast["expected_arrivals"].mean() if not forecast.empty else 0)
    bottlenecks["arrival_pressure_next_6h"] = arrival_pressure
    bottlenecks["risk_score"] = bottlenecks["signal"] * 1.0 + arrival_pressure * 0.12
    bottlenecks["forecast_statement"] = bottlenecks.apply(
        lambda row: f"{row['constraint']} is most likely to bind if average arrivals stay near {arrival_pressure:.1f} per hour.",
        axis=1,
    )
    return bottlenecks.sort_values("risk_score", ascending=False).reset_index(drop=True)


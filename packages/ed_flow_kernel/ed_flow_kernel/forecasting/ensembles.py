"""Forecast ensemble wrapper."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.modeling import ForecastBundle, forecast_external_pressure


def external_pressure_forecast(public_data: dict[str, pd.DataFrame], facility: str, horizon_hours: int = 72) -> ForecastBundle:
    """Return P10/P50/P90 public external pressure forecasts."""

    return forecast_external_pressure(public_data, facility, horizon_hours=horizon_hours)

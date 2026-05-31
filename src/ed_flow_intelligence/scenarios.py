"""Scenario workbench helpers."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.forecasting import hybrid_arrival_forecast, public_pressure_index


def run_public_scenario(
    visits: pd.DataFrame,
    public_data: dict[str, pd.DataFrame],
    facility: str,
    horizon_hours: int,
    respiratory_multiplier: float,
    smoke_heat_multiplier: float,
    travel_friction_multiplier: float,
    public_wait_override_mins: int | None = None,
) -> pd.DataFrame:
    """Estimate demand pressure changes from public-context levers."""

    forecast = hybrid_arrival_forecast(visits, public_data, facility, horizon_hours)
    pressure = public_pressure_index(public_data)
    base_pressure = float(pressure.loc[pressure["facility"] == facility, "public_pressure_index"].iloc[0]) if not pressure.empty and facility in pressure["facility"].values else 0.35
    wait_effect = 0.0 if public_wait_override_mins is None else min(max(public_wait_override_mins - 90, 0) / 260, 0.5)
    scenario_pressure = min(
        1.0,
        base_pressure * (0.45 * respiratory_multiplier + 0.3 * smoke_heat_multiplier + 0.25 * travel_friction_multiplier)
        + wait_effect,
    )
    expected_arrivals = forecast["expected_arrivals"].sum()
    scenario_arrivals = expected_arrivals * (1 + 0.42 * scenario_pressure)
    return pd.DataFrame(
        [
            {
                "scenario": "baseline public context",
                "expected_arrivals": expected_arrivals,
                "public_pressure_index": base_pressure,
                "expected_pia_wait_mins": 58 + base_pressure * 74,
                "expected_lwbs_risk": 0.04 + base_pressure * 0.09,
                "lineage": "HYBRID_OPEN_SYNTHETIC",
            },
            {
                "scenario": "public stress scenario",
                "expected_arrivals": scenario_arrivals,
                "public_pressure_index": scenario_pressure,
                "expected_pia_wait_mins": 58 + scenario_pressure * 92,
                "expected_lwbs_risk": 0.04 + scenario_pressure * 0.13,
                "lineage": "HYBRID_OPEN_SYNTHETIC",
            },
        ]
    )

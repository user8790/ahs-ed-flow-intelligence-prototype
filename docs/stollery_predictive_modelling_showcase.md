# Stollery Predictive Modelling Showcase

The predictive section demonstrates how a future ED flow intelligence layer could combine public context, synthetic operating state, and scenario analysis.

## Baseline Models Represented

- seasonal naive baseline
- moving average baseline
- regression-style adjustment
- tree-style nonlinear modifier
- bootstrap interval wrapper
- deterministic scenario adjustment engine

The generated artifacts include P10/P50/P90 intervals for hourly demand and physician wait, 28-day daily arrival forecasts, service bed demand, model drivers, and synthetic holdout validation.

## Baseline Versus Scenario

Baseline charts and tables are loaded from `stollery_forecast_baseline.json` and remain fixed. Scenario overlays are computed in the browser from:

- `stollery_scenario_catalog.json`
- `stollery_scenario_coefficients.json`
- `stollery_scenario_presets.json`

## Validation Posture

The validation artifact is synthetic. It shows the type of reporting expected before an internal pilot:

- holdout metrics
- interval coverage
- admission/flow calibration style tables
- drift checks
- limitations

Real deployment would require facility/date holdouts, seasonality checks, model monitoring, and replay against governed internal ED, bed-board, diagnostic, consult, and staffing feeds.

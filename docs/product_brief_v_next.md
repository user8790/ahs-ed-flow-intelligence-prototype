# Product Brief vNext

## What Improved

The app moved from a broad prototype to a more credible operational intelligence cockpit:

- Executive Pressure Cockpit with computed Alberta/site/pediatric/respiratory/environmental/travel pressure cards.
- Watch-points, operational levers, and pressure-movement interpretation.
- Research-to-Capability Map visible in the app.
- Stronger external-pressure forecasting with seasonal naive, moving average, ridge regression, random forest, ensemble forecast, P10/P50/P90 intervals, holdout metrics, rolling-origin backtest, and feature drivers.
- Combined public scenario builder covering respiratory, school, holiday, events, smoke, heat/cold, traffic, wildfire/access, wait-time deterioration, and synthetic internal capacity constraints.
- Enhanced simulation interpretation with utilization, stage occupancy, LWBS hazard sensitivity, bottleneck migration, scenario ranking, and deterministic capacity huddle brief.
- Richer lineage fields: grain, geography, downstream usage, activation status, internal activation needs, and blockers.
- Additional Snowflake SQL for hybrid model features and simulation feature tables.

## Capability Tiers

1. Public prototype capability: open-source metadata plus synthetic fallback data; useful for external pressure awareness and scenario demonstration.
2. Day-one Snowflake capability: real `TB_ED_VISITS`, chart semantic views, constrained flow analytics, calibration, and internal-ready hybrid feature views.
3. Early/aspirational Snowflake capability: operational feeds for bed board, ADT, staffing, diagnostics, consults, EMS/offload, transfers, bed cleaning, and inpatient capacity.

## Decision Frame

The app supports operational preparation and tabletop scenario discussion. It does not automate clinical judgement, staffing decisions, bed placement, triage, or discharge.

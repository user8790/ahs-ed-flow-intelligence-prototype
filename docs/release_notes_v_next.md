# Release Notes vNext

## Added

- Current-state gap audit.
- Executive Pressure Cockpit with computed metric cards, trends, confidence, lineage, watch-points, levers, and pressure-movement explanation.
- In-app Research-to-Capability Map.
- Public external-pressure ensemble forecast with seasonal naive, moving average, ridge regression, random forest, P10/P50/P90 intervals, holdout metrics, rolling-origin backtest, model registry, and feature drivers.
- Pediatric respiratory scenario controls including RSV, influenza, COVID, school reopening, measles exposure cluster, smoke overlay, and cold snap.
- Environmental scenario controls for AQHI, smoke duration, heat, extreme cold, and snow/freezing rain.
- Travel scenario controls for road disruption, public events, transit disruption, and severe weather access.
- Combined Open Data Scenario Workbench with scenario ranking, affected stages, watch-points, levers, and deterministic huddle brief.
- Enhanced Simulation Lab outputs: resource utilization, stage occupancy, bottleneck migration, LWBS hazard sensitivity, scenario ranking, pressure-to-action translator, and huddle brief.
- Expanded lineage and refresh fields.
- Snowflake SQL assets for hybrid model features and simulation feature tables.
- Tests for ensemble forecasting, scenario workbench, enhanced simulation, LWBS hazard, executive cockpit, research map, and new SQL assets.

## Preserved

- Synthetic-only public repository.
- Local mode without Snowflake credentials.
- `TB_ED_VISITS` constrained analysis boundary.
- Mock model client as the local default.
- Guarded Snowflake imports and SQL template design.

## Known Gaps

- Local public/open values remain synthetic fallbacks.
- The forecasting model is credible for demonstration but not operationally validated.
- A true ED digital twin still requires governed Snowflake operational feeds.
- MRN semantic-view mapping must be validated before internal chart-review use.

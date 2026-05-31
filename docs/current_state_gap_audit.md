# Current-State Gap Audit

Audit date: 2026-05-31

## Commands Run

```powershell
git status
git branch --show-current
git log --oneline -n 5
bash -lc "find . -maxdepth 3 -type f | sort"
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8503
```

The repository was clean on `main` at commit `639ad91` before this improvement pass. Dependency installation succeeded in the current Python 3.13 environment; `snowflake-snowpark-python` was skipped by its Python version marker. The existing test suite passed with 25 tests. The local Streamlit app launched successfully and the deployed public Streamlit shell was reachable.

## What Currently Works

- V2 has a working Streamlit app with 16 tabs and no dead top-level pages.
- Synthetic `TB_ED_VISITS`-shaped data, waiting-room patients, chart notes, expanded capacity feeds, and open-data fallback CSVs are present.
- Public pressure, wait-time, respiratory, environmental, travel, scenario, internal-ready flow, MRN chart-summary, hybrid forecast, simulation, validation, Snowflake, and lineage tabs all render.
- The constrained internal-ready module respects the `TB_ED_VISITS` boundary and excludes sensitive columns from constrained analysis.
- The MRN chart-summary workflow uses synthetic MRNs and a mock model client by default.
- Snowflake SQL templates and a guarded `SnowflakeBackend` exist.
- Local mode runs without Snowflake credentials.

## Meaningful Versus Shallow Tabs

Meaningful:

- `TB_ED_VISITS Internal-Ready Flow Analytics`: uses real synthetic visit rows, event-log reconstruction, route probabilities, stage durations, and replay validation.
- `Waiting Room MRN Chart Summaries`: has working add/remove, synthetic source sections, freshness, and summarization.
- `Simulation Lab`: runs stochastic replications and scenario comparisons.
- `Data Linkages & Refresh Status`: shows registry and refresh status rows.

Partly meaningful but too shallow:

- `Executive Command Centre`: has metrics but does not yet feel like an Alberta pressure cockpit with trend, confidence, watch-points, and operational levers on every metric.
- `Public ED Wait Times Monitor`: charts synthetic fallback wait-time series but does not validate or nowcast deterioration deeply.
- `Pediatric Respiratory Surge`: shows pathogen trends but lacks scenario controls, school/post-holiday effects, smoke overlay, and operational translation.
- `Smoke, Heat, Weather & Air Quality Stress`: shows synthetic stress but lacks scenario injection and site-station mapping details.
- `Travel Friction & Access Disruption`: shows travel score but lacks event/transit overlays and action interpretation.
- `Public Scenario Workbench`: has only a limited combined stress scenario.
- `Hybrid Forecasting Lab`: provides a heuristic hourly forecast but not baselines, richer models, validation, feature drivers, or daily/province views.
- `Snowflake Porting & Day-One Internal Setup`: useful, but SQL assets need more internal feature tables and simulation-ready views.

## Data And Lineage Findings

- Public/open data in the current repo is synthetic fallback cache with official-source metadata. It is not live official data.
- Internal-ready data is synthetic `TB_ED_VISITS` shaped data.
- Expanded operational data is synthetic and assumption-based.
- Model outputs are computed but mostly heuristic. The app lacks a formal model registry, rolling-origin backtesting, interval coverage, top-decile surge recall, and baseline comparisons.
- Simulation outputs are genuinely stochastic, but the current model has limited patient-class/resource detail and limited utilization metrics.

## Research-Inspiration Gaps

The current app reflects major research ideas: external pressure, respiratory/weather/travel stress, scenario analysis, a lightweight simulation, validation/governance, and Snowflake boundaries. However, the connection is not explicit enough in the UI. A research-to-capability map is needed so users can see which research insight maps to which module, data asset, model, chart, and Snowflake activation path.

## Confusing Or Weak UX Points

- Some tabs read as technical dashboards rather than operational decision surfaces.
- Metric cards lack consistent trend, confidence, lineage, and practical interpretation.
- Users may over-read synthetic fallback charts as official open data unless labels are repeated near outputs.
- Scenario results need a deterministic huddle brief, watch-points, and action questions.
- The difference between public capability, day-one Snowflake capability, and aspirational Snowflake capability needs to be visible in the app.

## Snowflake Portability Gaps

- Existing SQL templates are useful but missing `hybrid_open_internal_features.sql` and `simulation_feature_tables.sql`.
- The source registry needs grain, geography, activation status, downstream usage, blockers, and internal activation requirements.
- Forecast/model outputs need registry metadata documenting target, features, training window, validation window, limitations, lineage, and whether the model is public-only or internal-ready.
- Simulation features should be designed as Snowflake feature tables/views, not only app-level computations.

## Implementation Priorities From Audit

1. Add reusable operational UI components: lineage, confidence, freshness, impact, drivers, huddle brief, and bottleneck migration cards.
2. Add stronger public/hybrid forecasting with seasonal naive, moving average, regression, random forest, ensemble, intervals, validation metrics, and feature drivers.
3. Add a richer public scenario builder with combined respiratory, school, holiday, event, smoke, heat/cold, traffic, wildfire, wait-time, and capacity shocks.
4. Add enhanced simulation outputs: utilization, stage occupancy, LWBS hazard response, bottleneck movement, scenario ranking, and pressure-to-action translation.
5. Improve respiratory, environmental, and travel modules with scenario injections and operational translation.
6. Expand lineage/refresh dashboard and Snowflake SQL assets.
7. Add research-to-capability map in docs and app.

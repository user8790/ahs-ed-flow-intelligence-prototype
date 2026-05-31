# AHS ED Flow Intelligence Prototype vNext

Synthetic, Snowflake-portable Streamlit prototype for pediatric and provincial emergency department flow intelligence.

Live app: [ahs-ed-flow-intelligence.streamlit.app](https://ahs-ed-flow-intelligence.streamlit.app/)

This is an internal-capability prototype, not a vendor recommendation. It combines ED flow simulation, public/open contextual pressure signals, constrained `TB_ED_VISITS` analytics, MRN chart-summary workflow design, validation/governance, and Snowflake transfer readiness. It uses synthetic local data only and does not contain real PHI.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
python -m compileall src app.py
python -c "import app; print('app import ok')"
streamlit run app.py
```

The first app run creates local CSVs under `data/synthetic/` and `data/open/` if they are missing.

## V2 App Surface

The app has 16 working tabs:

1. Executive Command Centre
2. Alberta Public Pressure Map & Site Explorer
3. Public ED Wait Times Monitor
4. Pediatric Respiratory Surge
5. Smoke, Heat, Weather & Air Quality Stress
6. Travel Friction & Access Disruption
7. Public Scenario Workbench
8. `TB_ED_VISITS` Internal-Ready Flow Analytics
9. Waiting Room MRN Chart Summaries
10. Hybrid Forecasting Lab
11. Simulation Lab
12. Bed, Boarding, Discharge & Transfer Intelligence
13. Staffing & Resource Sensitivity
14. Model Validation, Calibration & Governance
15. Snowflake Porting & Day-One Internal Setup
16. Data Linkages & Refresh Status

## What Works Locally

- Synthetic `TB_ED_VISITS`-shaped ED/UCC/AACC visit data.
- Synthetic public/open-data fallback cache for wait times, respiratory surveillance, weather/AQHI/smoke, travel friction, calendar, population, and public aggregate ED metrics.
- Executive Pressure Cockpit with Alberta/site/pediatric/respiratory/environmental/travel pressure cards, confidence, lineage, watch-points, levers, and pressure-movement explanation.
- Public pressure map and facility explorer.
- Ensemble external-pressure forecasting with baselines, regression, random forest, P10/P50/P90 intervals, validation, model registry, and feature drivers.
- Combined open-data scenario builder with affected stages, scenario ranking, uncertainty, implementation friction, and deterministic huddle brief.
- Manual synthetic MRN add/remove and mock chart summaries.
- Constrained analytics using only columns available in the supplied `TB_ED_VISITS` contract.
- Event-log construction, stage reconstruction, observed concurrency, route probabilities, consult/boarding analysis, and replay validation.
- Monte Carlo discrete-event simulation with uncertainty intervals, utilization, stage occupancy, LWBS hazard sensitivity, bottleneck migration, scenario ranking, and action interpretation.
- Expanded synthetic feeds for beds, staffing, diagnostics, consult queues, EMS, transfers, and operational events.
- Validation/governance views for holdout split, calibration, missing timestamps, drift, data quality, explainability, and audit design.
- SQL templates for Snowflake open-data landing, constrained visit views, semantic-view queries, placeholders, lineage/audit tables, and hybrid joins.

## Repository Layout

```text
app.py
config/data_sources.yml
src/ed_flow/                    # v1 core, still used by v2
src/ed_flow_intelligence/       # v2 public/open-data, lineage, forecasting, SQL helpers
sql/snowflake/                  # Snowflake transfer templates
tests/
docs/
data/synthetic/
data/open/
```

## Snowflake Direction

The target secure deployment is Streamlit in Snowflake with Snowpark Python:

- Use `snowflake.snowpark.context.get_active_session()` inside Streamlit in Snowflake.
- Use `TB_ED_VISITS` for constrained internal-ready historical flow analytics.
- Use governed semantic views for chart-review sources keyed by validated `PATIENT_CHART` to `PAT_MRN_ID` mapping.
- Add open-data landing tables and tasks for public context.
- Add governed operational feeds for bed board, ADT, staffing, consult queues, diagnostics, EMS, transfer, EVS, and unit capacity.
- Keep model calls isolated in `src/ed_flow/ai_layer.py`; local default is `MockModelClient`.

See [docs/snowflake_porting.md](docs/snowflake_porting.md), [docs/internal_data_activation.md](docs/internal_data_activation.md), and [sql/snowflake](sql/snowflake).

## Recent Improvement Docs

- [Current-state gap audit](docs/current_state_gap_audit.md)
- [Research-to-capability map](docs/research_to_capability_map.md)
- [vNext product brief](docs/product_brief_v_next.md)
- [vNext release notes](docs/release_notes_v_next.md)

## No PHI

Do not add real MRNs, PHNs, ULIs, birthdates, postal codes, patient IDs, provider IDs, source notes, or private facility extracts. Synthetic identifiers intentionally use `SYN-*` formats.

## Validated Commands

```powershell
python -m pytest
python -m compileall src app.py
python -c "import app; print('app import ok')"
```

## Known Limits

- All local results are synthetic and not operationally calibrated.
- Public/open-data cache values are synthetic fallbacks with official-source metadata.
- Expanded operational intelligence is assumption-based until AHS curates secure Snowflake feeds.
- Simulation uses transparent empirical distributions and a lightweight resource model; it requires validation before operational use.
- Chart summaries are deterministic mock summaries in local mode and are not clinical chart review.

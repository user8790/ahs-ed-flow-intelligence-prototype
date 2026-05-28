# AHS ED Flow Intelligence Prototype

Synthetic, Snowflake-portable Streamlit prototype for pediatric and provincial emergency department flow intelligence.

Live app: [ahs-ed-flow-intelligence.streamlit.app](https://ahs-ed-flow-intelligence.streamlit.app/)

The app demonstrates an internal capability layer for data-informed operational decisions: command-centre metrics, chart-summary workflow, constrained `TB_ED_VISITS` analytics, discrete-event simulation, expanded system-intelligence concepts, validation/governance, and Snowflake transfer readiness.

It does **not** recommend vendor software, automate clinical judgement, or use real PHI.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
streamlit run app.py
```

The first app run creates CSVs under `data/synthetic/` if they are missing.

## What Works Locally

- Synthetic `TB_ED_VISITS`-shaped ED/UCC/AACC visit data.
- Synthetic current waiting-room registry and chart-note sources.
- Manual synthetic MRN add/remove in the chart-summary tab.
- Mock chart summarizer with required structured sections.
- Constrained analytics using only `TB_ED_VISITS` columns.
- Event-log construction, stage reconstruction, duration distributions, route probabilities, consult and boarding analysis.
- Discrete-event simulation with Monte Carlo uncertainty intervals and scenario comparison.
- Expanded synthetic feeds for beds, staffing, diagnostics, consult queues, EMS, transfers, and operational events.
- Validation and governance tables for holdout split, calibration, missing timestamps, drift, data quality, and audit design.
- Snowflake SQL templates and backend adapter design.

## Repository Layout

```text
app.py
src/ed_flow/
  config.py
  data_contracts.py
  synthetic_data.py
  local_backend.py
  snowflake_backend.py
  feature_engineering.py
  event_log.py
  metrics.py
  forecasting.py
  simulation_engine.py
  scenario_models.py
  optimization.py
  chart_review.py
  ai_layer.py
  governance.py
  visualizations.py
tests/
docs/
data/synthetic/
```

## Snowflake Direction

The future secure deployment should run Streamlit in Snowflake and use:

- `snowflake.snowpark.context.get_active_session()` for in-Snowflake execution.
- `TB_ED_VISITS` for constrained historical flow analytics.
- Governed semantic views for chart-review sources keyed by validated `PATIENT_CHART` to `PAT_MRN_ID` mapping.
- Snowpark-backed dataframes or curated secure views for expanded system feeds.
- A controlled model interface: mock/no model, approved OpenAI route, or Snowflake-native model calls.

See [docs/snowflake_transfer.md](docs/snowflake_transfer.md) for the transfer checklist and SQL templates.

## Known Limitations

- All data is synthetic and generated for demonstration, not operational calibration.
- Expanded system intelligence is assumption-based until AHS curates corresponding Snowflake datasets.
- The simulation uses transparent empirical distributions and simple resource scheduling; it is not clinically validated.
- Chart summaries use a deterministic mock provider by default and must not be treated as clinical chart review.
- Snowflake persistence for waiting-room registry/audit tables is intentionally not implemented until governed target tables are approved.

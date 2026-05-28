# Architecture

## Local Architecture

```text
Synthetic CSV files
  -> LocalBackend
  -> pandas feature engineering, metrics, event log, simulation
  -> Streamlit app tabs
  -> MockModelClient for summaries and explanations
```

## Future Snowflake Architecture

```text
Curated Snowflake tables/views
  -> TB_ED_VISITS constrained extract
  -> chart-review semantic views by PAT_MRN_ID
  -> expanded operational secure views
  -> SnowflakeBackend using get_active_session()
  -> same contracts and analytics modules
  -> Streamlit in Snowflake
  -> controlled model provider interface
```

## Module Responsibilities

- `config.py`: environment-backed runtime config.
- `data_contracts.py`: `TB_ED_VISITS` column contract, semantic view contracts, pydantic models.
- `synthetic_data.py`: deterministic local synthetic data generation.
- `local_backend.py`: CSV-backed development adapter.
- `snowflake_backend.py`: Snowpark-ready adapter and SQL templates.
- `feature_engineering.py`: constrained features and parameter estimation.
- `event_log.py`: timestamp-to-event-log and stage interval reconstruction.
- `metrics.py`: command-centre and validation metrics.
- `simulation_engine.py`: portable discrete-event simulation.
- `optimization.py`: scenario ranking and greedy bed-placement heuristic.
- `ai_layer.py`: mock/OpenAI/Snowflake/no-model provider interface.
- `governance.py`: validation, calibration, drift, missing timestamp, audit design helpers.

## Design Boundary

The constrained module must only use columns from `TB_ED_VISITS`. Expanded features are explicitly labelled as synthetic and assumption-based until AHS curates additional Snowflake datasets.


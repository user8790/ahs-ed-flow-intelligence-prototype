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
- `ed_flow_intelligence/modeling.py`: public/hybrid forecasting, validation, model registry, and feature drivers.
- `ed_flow_intelligence/advanced_scenarios.py`: combined public shock scenario workbench.
- `ed_flow_intelligence/simulation_vnext.py`: utilization, occupancy, LWBS hazard, bottleneck migration, scenario ranking, and huddle brief wrappers.
- `ed_flow_intelligence/operational_intelligence.py`: executive cockpit, watch-points, levers, huddle briefs, and research-to-capability map.

## Design Boundary

The constrained module must only use columns from `TB_ED_VISITS`. Expanded features are explicitly labelled as synthetic and assumption-based until AHS curates additional Snowflake datasets.

## Capability Tiers

1. Public prototype: public-source metadata plus synthetic fallback data; computes external pressure, scenario stress, and plausible queue effects.
2. Day-one Snowflake: real `TB_ED_VISITS`, semantic views, open-data landing tables, internal calibration, and governed model/audit controls.
3. Early/aspirational Snowflake: bed board, ADT, staffing, diagnostics, consults, EMS/offload, transfers, EVS, inpatient capacity, and location-event feeds.

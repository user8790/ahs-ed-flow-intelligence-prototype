# Architecture v2

## Local Runtime

```text
data/synthetic/*.csv
data/open/*.csv
        |
        v
LocalBackend + OpenDataHub
        |
        v
pandas/numpy/scikit-learn feature, metric, forecast, and simulation helpers
        |
        v
Streamlit app.py
```

## Snowflake Runtime

```text
Public open-data landing tables
Curated TB_ED_VISITS secure view
Chart-review semantic views
Governed operational feeds
        |
        v
SnowflakeBackend + Snowpark Session
        |
        v
Shared data contracts and app-facing dataframes
        |
        v
Streamlit in Snowflake
```

Inside Streamlit in Snowflake, the backend should use:

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
```

## Key Boundaries

- `src/ed_flow/snowflake_backend.py`: Snowflake data access and SQL templates.
- `src/ed_flow/ai_layer.py`: model-provider interface.
- `src/ed_flow_intelligence/data_sources/`: public/open-data registry and local fallback cache.
- `sql/snowflake/`: target DDL, views, tasks, lineage, and semantic-view query templates.

## Lineage Categories

The app labels data as `OPEN_DATA`, `SYNTHETIC_DATA`, `SECURE_INTERNAL_PLACEHOLDER`, `SECURE_INTERNAL_READY_SCHEMA`, `HYBRID_OPEN_SYNTHETIC`, `HYBRID_OPEN_INTERNAL_READY`, `MODEL_OUTPUT`, or `USER_INPUT`.

The final app tab is the source-of-truth screen for lineage, refresh, fallback status, Snowflake target mapping, and PHI/identifier risk.

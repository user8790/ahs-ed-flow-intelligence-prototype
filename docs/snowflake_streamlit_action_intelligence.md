# Snowflake Streamlit Action Intelligence

`AHS ED Flow Action Intelligence` is a new internal/Snowflake-portable Streamlit app at:

`apps/streamlit_action_intelligence/app.py`

Suggested Streamlit slug:

`ahs-ed-flow-action-intelligence`

Preferred URL:

`https://ahs-ed-flow-action-intelligence.streamlit.app/`

## Local Mode

Local mode uses synthetic TB_ED_VISITS-shaped rows, synthetic active-state rows, public/open-data-shaped synthetic fallback cache, and the shared `ed_flow_kernel`. No Snowflake credentials are required.

## Snowflake Mode

Inside Streamlit in Snowflake, use the guarded backend pattern:

```python
from snowflake.snowpark.context import get_active_session
```

through the existing Snowflake backend. The app should prefer the active Snowflake session and only use environment-based fallback during approved local development.

## Day-One Activation

1. Confirm RBAC for `CURATED.TB_ED_VISITS`.
2. Deploy open-data tables and refresh logs under `OPEN_DATA` and `GOVERNANCE`.
3. Validate constrained feature views and default business rules.
4. Validate semantic chart-review identifier mapping in secure runtime only.
5. Calibrate forecasts and simulation by facility/date holdout.
6. Enable audit logging for scenario runs and operational huddle views.

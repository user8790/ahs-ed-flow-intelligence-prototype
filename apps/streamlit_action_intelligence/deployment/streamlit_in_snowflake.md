# Streamlit In Snowflake Deployment

Deploy the Action Intelligence app inside the governed Snowflake account after package compatibility and RBAC review.

1. Create/validate schemas: `OPEN_DATA`, `CURATED`, `SEMANTIC`, `GOVERNANCE`, `MODELS`, `SIMULATION`, `APP_CONFIG`.
2. Load or create views from `sql/snowflake/*.sql`.
3. Package the shared `ed_flow_kernel` and app code as approved Snowflake imports.
4. Use `snowflake.snowpark.context.get_active_session()` through the guarded backend.
5. Keep chart-review semantic views and identifiers inside Snowflake.
6. Validate facility calibration, holdout performance, and replay simulation before pilot workflow use.

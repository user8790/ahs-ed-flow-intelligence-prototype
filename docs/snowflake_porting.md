# Snowflake Porting

## Day-One Setup

1. Create `OPEN_DATA`, `CURATED`, `OPERATIONS`, `ANALYTICS`, and `GOVERNANCE` schemas.
2. Deploy SQL files from [sql/snowflake](../sql/snowflake).
3. Create `CURATED.V_ED_VISITS_CORE` from `TB_ED_VISITS`.
4. Configure open-data landing tables and refresh audit logs.
5. Configure semantic-view query access for chart review.
6. Replace `LocalBackend` calls with `SnowflakeBackend` using `get_active_session()`.
7. Keep `MockModelClient` or no-model mode until model/PHI approval is complete.

## SQL Files

- `open_data_ddl.sql`
- `open_data_tasks.sql`
- `tb_ed_visits_core.sql`
- `tb_ed_visits_feature_views.sql`
- `semantic_view_queries.sql`
- `secure_internal_placeholders.sql`
- `lineage_and_refresh_tables.sql`
- `v_ed_visits_with_open_context.sql`

## Package Notes

The app keeps dependencies Snowflake-friendly: Streamlit, pandas, numpy, scipy, scikit-learn, plotly, pydantic, PyYAML, pytest, SimPy, and Snowpark. SimPy is optional from an architecture point of view because the local engine has a lightweight fallback design.

## Secure Handling

No PHI should leave governed Snowflake views. External model calls must be disabled unless approved for the exact data class and audited in `GOVERNANCE.MODEL_CALL_AUDIT_LOG`.

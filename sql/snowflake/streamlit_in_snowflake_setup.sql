-- Streamlit in Snowflake setup notes for AHS ED Flow Action Intelligence.
-- Review warehouse, RBAC, package availability, and import locations before use.

CREATE SCHEMA IF NOT EXISTS APP_CONFIG;

CREATE OR REPLACE STAGE APP_CONFIG.ACTION_INTELLIGENCE_APP_STAGE
  DIRECTORY = (ENABLE = TRUE);

-- Example only. Use an approved warehouse and package policy.
CREATE OR REPLACE STREAMLIT APP_CONFIG.AHS_ED_FLOW_ACTION_INTELLIGENCE
  ROOT_LOCATION = '@APP_CONFIG.ACTION_INTELLIGENCE_APP_STAGE'
  MAIN_FILE = 'apps/streamlit_action_intelligence/app.py'
  QUERY_WAREHOUSE = WH_SMALL
  COMMENT = 'Snowflake-portable Action Intelligence app; decision support only.';

-- Required grants should be minimized and role-based.
-- GRANT USAGE ON SCHEMA CURATED TO ROLE <APP_ROLE>;
-- GRANT SELECT ON TABLE CURATED.TB_ED_VISITS TO ROLE <APP_ROLE>;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA SEMANTIC TO ROLE <APP_ROLE>;
-- GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA GOVERNANCE TO ROLE <APP_ROLE>;

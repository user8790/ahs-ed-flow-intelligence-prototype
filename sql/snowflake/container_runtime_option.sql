-- Optional Snowpark Container Services runtime option.
-- Use only if package/runtime needs exceed Streamlit in Snowflake's supported package set.

CREATE SCHEMA IF NOT EXISTS APP_CONFIG;

CREATE TABLE IF NOT EXISTS APP_CONFIG.CONTAINER_RUNTIME_DECISION_LOG (
  DECISION_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  DECISION_OWNER STRING,
  REASON STRING,
  APPROVED BOOLEAN DEFAULT FALSE,
  SECURITY_REVIEW_REFERENCE STRING
);

-- Candidate container responsibilities:
-- 1. Run heavier simulation batches.
-- 2. Export public-safe artifacts for non-PHI showcase deployments.
-- 3. Execute scheduled validation/calibration jobs.
-- 4. Keep all PHI-sensitive computation inside approved Snowflake network boundaries.

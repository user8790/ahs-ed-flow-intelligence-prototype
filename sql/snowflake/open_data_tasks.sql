-- Example task shells. Replace COPY statements with approved external stage/API procedures.

CREATE OR REPLACE TASK OPEN_DATA.TASK_REFRESH_AHS_WAIT_TIMES
  WAREHOUSE = WH_SMALL
  SCHEDULE = '5 MINUTE'
AS
  INSERT INTO OPEN_DATA.REFRESH_AUDIT_LOG
  SELECT 'ahs_public_wait_times', CURRENT_TIMESTAMP(), 'configured', 'Use approved AHS/public ingest procedure';

CREATE OR REPLACE TASK OPEN_DATA.TASK_REFRESH_RESPIRATORY_SURVEILLANCE
  WAREHOUSE = WH_SMALL
  SCHEDULE = 'USING CRON 0 */6 * * * America/Edmonton'
AS
  INSERT INTO OPEN_DATA.REFRESH_AUDIT_LOG
  SELECT 'alberta_respiratory_dashboard', CURRENT_TIMESTAMP(), 'configured', 'Use approved Alberta public dashboard ingest procedure';

CREATE OR REPLACE TASK OPEN_DATA.TASK_REFRESH_WEATHER_AQHI_WILDFIRE
  WAREHOUSE = WH_SMALL
  SCHEDULE = '15 MINUTE'
AS
  INSERT INTO OPEN_DATA.REFRESH_AUDIT_LOG
  SELECT 'eccc_geomet_weather_alerts', CURRENT_TIMESTAMP(), 'configured', 'Use approved ECCC/Alberta AQHI/wildfire ingest procedures';

CREATE OR REPLACE TASK OPEN_DATA.TASK_REFRESH_TRAVEL_FRICTION
  WAREHOUSE = WH_SMALL
  SCHEDULE = '15 MINUTE'
AS
  INSERT INTO OPEN_DATA.REFRESH_AUDIT_LOG
  SELECT 'alberta_511_events', CURRENT_TIMESTAMP(), 'configured', 'Use approved 511 and municipal open-data ingest procedures';

# Snowflake Transfer Plan

Prototype v2 adds a more complete Snowflake transfer package. See [snowflake_porting.md](snowflake_porting.md), [internal_data_activation.md](internal_data_activation.md), and [../sql/snowflake](../sql/snowflake).

## Target Runtime

- Streamlit in Snowflake.
- Snowpark Python.
- Curated `TB_ED_VISITS` data.
- Governed chart-review semantic views.
- Optional expanded operational secure views.
- Controlled model layer using mock/no model, approved OpenAI route, or Snowflake-native calls.

## Adapter Strategy

Local mode:

```text
CSV -> LocalBackend -> same app contracts
```

Snowflake mode:

```text
get_active_session() -> SnowflakeBackend -> same app contracts
```

When running inside Streamlit in Snowflake, use:

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
```

For local Snowflake development, use environment variables for account, user, role, warehouse, database, and schema. Do not commit credentials.

## Constrained SQL Template

```sql
SELECT
  DATA_RECORD_ID,
  DATA_SOURCE,
  DEPARTMENT_TYPE,
  INSTITUTION_NAME,
  INSTITUTION_CODE,
  INSTITUTION_ZONE_NAME,
  INSTITUTION_CORRIDOR_NAME,
  INSTITUTION_PEER_GROUP,
  ARRIVAL_MODE,
  TRIAGE_LEVEL,
  DISPOSITION_GROUP,
  DISPOSITION_PERFORMANCE_REPORT,
  PRESENTING_COMPLAINT,
  DIAGNOSIS_DESCRIPTION,
  PRIMARY_ADMIT_DIAGNOSIS,
  ADMIT_PATIENT_SERVICE_DESCRIPTION,
  ADMIT_UNIT_NAME,
  ADMIT_UNIT_SPECIALTY,
  PATIENT_SEX,
  PATIENT_AGE,
  PATIENT_AGE_GROUP,
  PATIENT_ZONE_NAME,
  PATIENT_CORRIDOR_NAME,
  FIRST_CONTACT_DATETIME,
  REGISTRATION_DATETIME,
  TRIAGE_DATETIME,
  EMS_OFFLOAD_DATETIME,
  INITIAL_LOCATION_DATETIME,
  INITIAL_ROOMED_IN_DATETIME,
  PHYSICIAN_INITIAL_ASSESSMENT_DATETIME,
  INITIAL_PHYSICIAN_CONSULT_REQUEST_DATETIME,
  INITIAL_PHYSICIAN_CONSULT_COMPLETED_DATETIME,
  DISPOSITION_DATETIME,
  DECISION_TO_ADMIT_DATETIME,
  IP_BED_ASSIGN_DATETIME,
  DEPART_ED_DATETIME,
  LAST_CONTACT_DATETIME,
  INITIAL_ROOMED_IN_LOCATION_DESCRIPTION,
  LOCATION_ID_COUNT,
  LAST_LOCATION_DESCRIPTION,
  LAST_LOCATION_DATETIME,
  INITIAL_PHYSICIAN_CONSULT_PROVIDER_TYPE_NAME,
  INITIAL_PHYSICIAN_CONSULT_SPECIALTY_NAME,
  CONSULT_COUNT,
  ADMITTED_WITHIN_8HRS_FLAG,
  DISCHARGED_WITHIN_4HRS_FLAG,
  ED_LOS_HRS,
  ED_LOS_ADMITTED_HRS,
  ED_LOS_DISCHARGED_HRS,
  ED_LOS_FIRST_CONTACT_TO_EMS_HANDOFF_MINS,
  ED_LOS_FIRST_CONTACT_TO_INITIAL_ROOMED_IN_ED_HRS,
  ED_LOS_FIRST_CONTACT_TO_PHYSICIAN_INITIAL_ASSESSMENT_HRS,
  ED_LOS_PHYSICIAN_INITIAL_ASSESSMENT_TO_DISPOSITION_HRS,
  ED_LOS_PHYSICIAN_INITIAL_CONSULT_REQUEST_TO_DISPOSITION_HRS,
  ED_LOS_DECISION_TO_ADMIT_TO_LAST_CONTACT_HRS,
  INSTITUTION_MUNICIPALITY,
  INSTITUTION_OPERATOR,
  INSTITUTION_ABBREVIATION,
  PATIENT_MUNICIPALITY
FROM TB_ED_VISITS
WHERE INVALID_LOS_CALC_FLAG <> 'Y'
  AND COALESCE(SCHEDULED_ED_VISIT_FLAG, 'N') <> 'Y'
  AND FIRST_CONTACT_DATETIME >= :start_datetime
  AND FIRST_CONTACT_DATETIME < :end_datetime;
```

## Chart Semantic View Pattern

```sql
SELECT <approved columns>
FROM DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS.MSB_CLINICAL_GENETICS.<semantic_view>
WHERE PAT_MRN_ID = :mrn
ORDER BY <available freshness columns> DESC;
```

## Security and PHI

- Keep PHI in Snowflake governed views.
- Use least-privilege role grants.
- Validate `PATIENT_CHART` to `PAT_MRN_ID` mapping before use.
- Disable external model calls unless approved for the data class.
- Audit chart-summary prompts/responses, scenario inputs, seeds, data version, model provider, and output hashes.

## Migration Checklist

1. Validate the real `TB_ED_VISITS` column names and timestamp semantics.
2. Create constrained secure view with only approved columns.
3. Validate MRN/chart mapping.
4. Create semantic views with freshness fields and row-level controls.
5. Replace `LocalBackend` with `SnowflakeBackend` in config.
6. Calibrate simulation by facility and holdout date.
7. Validate route/disposition and duration models.
8. Implement audit tables.
9. Complete privacy/security/model-governance review.
10. Pilot with human-in-the-loop operational review.

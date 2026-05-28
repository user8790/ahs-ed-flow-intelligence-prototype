# Data Contract

## Constrained Table

The constrained module is built around `TB_ED_VISITS`, grain one row per emergency department visit identified by `DATA_RECORD_ID`.

Default rules:

- Exclude `INVALID_LOS_CALC_FLAG = 'Y'` for LOS analysis.
- Exclude `SCHEDULED_ED_VISIT_FLAG = 'Y'` for typical walk-in analysis unless explicitly included.
- Use `FIRST_CONTACT_DATETIME` as the primary visit start timestamp.
- Use `DISPOSITION_PERFORMANCE_REPORT` for standardized disposition metrics.
- Do not use `ROW_CREATE_DATETIME` or `ROW_UPDATE_DATETIME` as clinical event timestamps.
- Treat PHN, ULI, patient ID, birthdate, postal code, and chart/MRN as sensitive.

## Sensitive Fields

The local synthetic data contains non-real placeholder identifiers only. In Snowflake, these fields require least-privilege access controls:

- `PATIENT_ID`
- `PATIENT_PHN`
- `PATIENT_BIRTHDATE`
- `PATIENT_CHART`
- `PATIENT_ULI`
- `PATIENT_POSTALCODE`
- note text and MRN fields in chart-review views

## Chart-Review Semantic Views

The adapter expects governed semantic views in:

- Database: `DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS`
- Schema: `MSB_CLINICAL_GENETICS`
- Warehouse: `WH_SMALL`

Views:

- `SV_ADMISSION_HP_NOTES`
- `SV_CONSULT_NOTES`
- `SV_IMAGING_NOTES`
- `SV_LAB_REPORTS`
- `SV_ENC_NOTES`
- `SV_PROBLEM_LIST`
- `SV_MEDICAL_HISTORY`
- `SV_EDPROVIDER_NOTES`
- `SV_REFERRALS`

The ED visit table uses `PATIENT_CHART`; the semantic views use `PAT_MRN_ID`. Mapping must be configurable and validated before a governed pilot.

## Expanded Synthetic Feeds

The expanded module assumes future curated feeds for location events, beds, inpatient census, pending discharges, bed cleaning, staffing, consult queues, labs, imaging, transport, EMS, transfers, and service/team assignment.


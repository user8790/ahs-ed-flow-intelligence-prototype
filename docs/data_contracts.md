# Data Contracts

## Constrained Internal Contract

`TB_ED_VISITS` is the constrained ED table. Grain is one row per ED/UCC/AACC visit identified by `DATA_RECORD_ID`.

Default rules:

- Exclude `INVALID_LOS_CALC_FLAG = 'Y'` for LOS analysis.
- Exclude `SCHEDULED_ED_VISIT_FLAG = 'Y'` for typical walk-in ED analysis.
- Use `FIRST_CONTACT_DATETIME` as the visit start timestamp.
- Use `DISPOSITION_PERFORMANCE_REPORT` for standardized disposition metrics.
- Never use `ROW_CREATE_DATETIME` or `ROW_UPDATE_DATETIME` as clinical event timestamps.
- Treat PHN, ULI, patient ID, birthdate, postal code, chart/MRN, and note text as sensitive.

The constrained app module uses `constrained_projection()` and tests assert that no non-contract columns are required.

## Chart Review Contract

Chart-review semantic views are addressed through `PAT_MRN_ID`. `TB_ED_VISITS` uses `PATIENT_CHART`. The mapping layer is explicit and must be validated before any internal pilot.

Local mode uses one synthetic MRN string per waiting-room patient and `MockModelClient` summaries.

## Public/Open Contract

Public datasets are site, zone, time, calendar, or aggregate context only. They must not contain patient identifiers.

## Expanded Operational Contract

Expanded operational feeds are placeholders until AHS creates governed Snowflake views for location events, ADT/bed board, inpatient census, pending discharges, EVS cleaning, staffing, consult queues, diagnostics, EMS, transfers, unit capacity, and service/team assignment.

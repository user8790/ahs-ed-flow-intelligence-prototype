# Internal Data Activation

## Required Internal Feeds

- `TB_ED_VISITS`
- real-time ED location tracking events
- ADT bed board and bed status
- inpatient census
- pending discharges
- EVS bed cleaning
- isolation requirements
- nurse/physician staffing and shift rosters
- consult queues
- lab/imaging diagnostic turnaround
- transport/transfer requests
- EMS arrival estimates
- inpatient unit capacity
- service/team assignment
- chart-review semantic views

## Activation Sequence

1. Start with `TB_ED_VISITS` only and reproduce constrained module metrics.
2. Add public/open-data tables and verify source freshness in the lineage tab.
3. Add chart-review semantic views with validated MRN mapping and mock/no-model summaries first.
4. Add bed board, pending discharge, and inpatient capacity feeds.
5. Add staffing, consult, diagnostics, transport, and EMS feeds.
6. Calibrate models by facility and population strata.
7. Run human-in-the-loop tabletop validation before workflow pilot.

## Internal-Ready Feature Views

The Snowflake package now includes:

- site-hour arrivals
- site-day arrivals
- pediatric respiratory features
- weather/open-data context joined to site-hour
- admission probability features
- LWBS features
- LOS and PIA quantile features
- boarding features
- flow stage duration distributions
- observed concurrency estimates
- simulation scenario audit outputs

## Validation Gates

- Schema and column validation.
- Timestamp ordering and missingness checks.
- Facility-level calibration.
- PHI/identifier access review.
- Model provider approval.
- Audit-log dry run.
- Drift and failure-mode review.

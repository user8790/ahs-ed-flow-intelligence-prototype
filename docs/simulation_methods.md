# Simulation Methods

## Summary

The simulation is a transparent discrete-event ED flow model with Monte Carlo replications. It runs locally with synthetic data and is designed to be recalibrated from `TB_ED_VISITS` and optional secure operational feeds in Snowflake.

## Stages

1. First contact / arrival.
2. Registration.
3. Triage.
4. Waiting room.
5. Rooming.
6. Physician initial assessment.
7. Treatment, diagnostics, and consults.
8. Disposition.
9. Discharge departure or decision-to-admit boarding.
10. Inpatient bed assignment / ED departure.

## Baseline Estimation

In constrained mode, baseline parameters are inferred from `TB_ED_VISITS` timestamp differences and disposition fields:

- arrival rate by facility and filter
- triage mix from `TRIAGE_LEVEL`
- route probabilities from `DISPOSITION_GROUP`
- consult probability from `CONSULT_COUNT`
- stage duration medians and p90 values from timestamp intervals
- boarding delay from `DECISION_TO_ADMIT_DATETIME` to `LAST_CONTACT_DATETIME`
- capacity assumptions from observed flow/concurrency summaries

## Scenario Controls

The app supports arrival surge, triage capacity, physician capacity, rooming capacity, CTAS 4/5 fast track, consult turnaround, diagnostic turnaround, admission bed availability, boarding reduction, discharge acceleration, EMS offload improvement, random seed, and Monte Carlo replication count.

## Outputs

Outputs include median and p90 wait, admitted/discharged LOS measures, admitted within 8 hours, discharged within 4 hours, LWBS risk, boarding hours, queue pressure over time, bottleneck shift analysis, uncertainty intervals, scenario comparison, and practical interpretation.

## Validation Requirement

Simulation outputs should be compared against holdout periods by facility, age group, triage, disposition, and hour/day. No scenario should be used operationally until calibrated and reviewed with operational and clinical leaders.

## Local Limits

Local mode is not operationally calibrated. It uses synthetic distributions and a lightweight resource allocation model. Snowflake pilot work should validate stage definitions, capacity assumptions, and nonlinear boarding cascades by facility.

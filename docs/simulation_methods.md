# Simulation Methods

## Stages

The simulation models:

1. First contact / arrival
2. Registration
3. Triage
4. Waiting room
5. Rooming
6. Physician initial assessment
7. Treatment / diagnostics / consults
8. Disposition
9. Discharge departure or decision-to-admit boarding
10. Inpatient bed assignment / ED departure

## Baseline Estimation

In constrained mode, baseline parameters are inferred from `TB_ED_VISITS` timestamp differences and disposition fields:

- Arrival rate by facility and filter.
- Triage mix from `TRIAGE_LEVEL`.
- Route probabilities from `DISPOSITION_GROUP`.
- Consult probability from `CONSULT_COUNT`.
- Stage duration medians and p90 values from timestamp intervals.
- Boarding delay from `DECISION_TO_ADMIT_DATETIME` to `LAST_CONTACT_DATETIME`.

The local synthetic dataset is sparse relative to a real provincial feed, so the prototype applies a transparent minimum demonstration arrival rate for simulation usability. A Snowflake pilot should replace this with validated facility/hour/day rates.

## Scenario Controls

- Arrival surge multiplier
- Triage capacity change
- Physician initial assessment capacity change
- Rooming capacity change
- Fast-track CTAS 4/5 stream
- Consult turnaround improvement
- Diagnostic turnaround improvement
- Admission bed availability improvement
- Boarding reduction
- Discharge acceleration
- EMS offload improvement
- Monte Carlo replications

## Outputs

- Median and p90 wait to physician initial assessment
- Median and p90 ED LOS
- Admitted within 8 hours
- Discharged within 4 hours
- LWBS risk
- Boarding hours
- Queue pressure over time
- Bottleneck shift analysis
- Uncertainty intervals

## Validation Requirement

Simulation outputs should be compared against holdout periods by facility, age group, triage, disposition, and hour/day. No scenario should be used operationally until calibrated and reviewed with operational and clinical leaders.


# Modelling Methods

## Baseline

Prototype v2 uses interpretable methods first:

- empirical distributions
- route probabilities by facility, triage, age group, and complaint
- timestamp-derived stage durations
- observed concurrency reconstruction
- bootstrapped Monte Carlo uncertainty
- simple public-pressure feature weighting

## Hybrid Forecasting

The hybrid arrival forecast combines empirical arrivals from synthetic `TB_ED_VISITS` rows with public pressure context:

- posted wait-time fallback
- respiratory pediatric pressure
- environmental stress
- travel friction
- calendar context

The method is transparent and intentionally conservative. It should be recalibrated with real TB_ED_VISITS holdouts and governed open-data feeds in Snowflake.

## Scenario Ranking

Scenario ranking compares simulated outcomes such as median/p90 waits, LOS, admitted-within-8h, discharged-within-4h, LWBS risk, and boarding hours. AI-generated text may explain results but is not the source of results.

## Validation Required

Before an internal pilot, validate:

- facility-level calibration
- pediatric/all-age strata
- stage-duration distributions
- admission/discharge/LWBS/transfer calibration
- consult and boarding delay estimates
- drift across season, facility, and public-pressure conditions

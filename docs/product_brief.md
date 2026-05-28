# Product Brief

## Purpose

The AHS ED Flow Intelligence Prototype demonstrates an internal, Snowflake-portable capability layer for pediatric and provincial emergency department operations. It helps leaders inspect current flow pressure, understand constrained historical patterns, test operational scenarios, and review validation/governance signals before interventions are tested in real workflows.

## Product Principle

The app supports data-informed operational decisions. It does not automate clinical judgement, replace chart review, or make patient-specific clinical recommendations.

## Local Prototype Scope

- Runs with synthetic data only.
- Uses no real PHI, MRNs, PHNs, ULIs, birthdates, postal codes, provider notes, or patient details.
- Uses a mock model provider by default.
- Keeps constrained analytics separate from expanded assumption-based intelligence.
- Exposes uncertainty, freshness, assumptions, and data quality warnings.

## Primary Users

- ED operational leaders.
- Pediatric and provincial flow teams.
- Analytics teams preparing Snowflake data products.
- Clinical leaders reviewing simulation assumptions and governance readiness.

## Main Workflows

1. Review current simulated ED pressure in the Executive Command Centre.
2. Add/remove synthetic MRNs and refresh mock chart summaries.
3. Explore constrained `TB_ED_VISITS` flow patterns and event reconstruction.
4. Run simulation scenarios and compare uncertainty intervals.
5. Inspect expanded synthetic feeds for beds, staffing, consults, diagnostics, and transfers.
6. Review holdout validation, calibration, drift, missing timestamps, and audit controls.
7. Prepare for Snowflake transfer using the adapter and SQL templates.


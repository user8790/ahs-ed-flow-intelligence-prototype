# Product Brief v2

## Purpose

Prototype v2 demonstrates how AHS could build an internal ED flow intelligence layer on AHS-owned infrastructure instead of buying an external flow-optimization product. The app supports data-informed operational decisions by making bottlenecks, uncertainty, assumptions, source freshness, and scenario trade-offs visible.

## Users

- Pediatric ED and hospital operations leaders.
- Provincial flow, access, and capacity teams.
- Analytics, data science, Snowflake, and governance teams preparing an internal pilot.

## Core Capabilities

- Executive ED state and bottleneck summary.
- Public pressure context from wait-time, respiratory, weather/AQHI/smoke, travel, calendar, and population features.
- Constrained `TB_ED_VISITS` analytics using only the real data contract.
- Waiting-room MRN chart-summary workflow with mock local summarizer and semantic-view adapter design.
- Discrete-event simulation and scenario comparison with uncertainty intervals.
- Expanded assumption-based bed, boarding, discharge, transfer, staffing, and resource views.
- Validation, calibration, data quality, drift, audit, and human-in-the-loop governance.
- Snowflake porting plan with SQL templates and adapter boundaries.

## Product Principle

The app estimates expected operational effects before leaders test changes in real workflows. It does not automate clinical judgement, triage, bed assignment, discharge decisions, or staffing decisions.

## Data Posture

Local mode uses synthetic data only. Public/open-source metadata is present, but local public values are synthetic fallback cache values. Internal-ready Snowflake views are represented by schemas, SQL templates, and adapter interfaces.

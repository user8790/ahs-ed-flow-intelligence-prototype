# Governance and Validation

## Decision-Support Frame

The prototype is for operational decision support. It should never automate clinical judgement or hide uncertainty from leaders.

## Validation Included

- Chronological holdout split.
- Facility-level calibration table.
- Stage-duration distribution comparison.
- Simulated versus observed LOS comparison.
- Admission model calibration bins.
- Data quality checks.
- Missing timestamp rates.
- Distribution drift checks.
- Explainability summary.
- Audit log design.

## Data Quality Rules

- Exclude invalid LOS records from LOS analysis by default.
- Exclude scheduled ED visits by default.
- Treat missing first-contact timestamps as critical.
- Keep `ROW_CREATE_DATETIME` and `ROW_UPDATE_DATETIME` for freshness only.
- Flag reversed or negative timestamp intervals.

## Audit Design

Audit records should include:

- User and role.
- Timestamp.
- Facility/filter selections.
- Data extract version.
- Scenario inputs.
- Random seed and simulation parameters.
- Model provider.
- Prompt/response hash where model calls are allowed.
- Output hash and rendered recommendation set.

## Model Governance

Interpretable empirical methods should be the baseline. AI-generated narratives may summarize chart context or explain scenario results, but they must not generate simulation outcomes or be presented as source data.

## V2 Additions

- Public/open-data values are labelled as synthetic fallback in local mode.
- Every app tab shows lineage badges.
- The final tab centralizes source registry, refresh status, Snowflake target mapping, fallback reason, quality score, and PHI/identifier risk.
- Snowflake pilot should persist scenario audit logs, model-call audit logs, refresh audit logs, and data-source registry updates.
- Chart-summary prompts and outputs require PHI/model approval before real semantic-view content is summarized.

## vNext Additions

- Every forecast model has registry metadata and validation metrics.
- Public forecasts show baseline comparison, richer model comparison, and interval coverage.
- Scenario outputs include uncertainty, implementation friction, watch-points, levers, and deterministic huddle briefs.
- Simulation outputs include resource utilization, bottleneck migration, and pressure-to-action questions.
- Lineage rows include grain, geography, downstream usage, activation status, internal activation needs, and blockers.

## Action Intelligence and Showcase Boundary

The public showcase consumes only exported static artifacts. The exporter validates the artifact envelope and applies public-safe redaction of internal identifier column names before writing JSON. The Action Intelligence app keeps human-in-the-loop framing visible in every scenario and simulation workflow.

# Assumptions and Limits

## Assumptions

- Synthetic data approximates ED flow variation but is not calibrated to actual AHS volumes.
- Pediatric examples include Stollery Children's Hospital and Alberta Children's Hospital.
- The constrained module can infer useful baseline parameters from `TB_ED_VISITS` timestamps.
- Public/open-data source metadata can be curated into Snowflake, but local public values are synthetic fallbacks.
- Expanded operational feeds can be curated in Snowflake later.
- Model calls are optional and must remain behind a provider interface.

## Limits

- Local results are not operationally valid.
- Public pressure, respiratory, weather, AQHI, wildfire, travel, and calendar outputs are not official live values in local mode.
- Forecast models are credible for demonstration but trained/validated on synthetic fallback history, not operational AHS truth.
- Scenario huddle briefs are deterministic operational interpretations, not instructions.
- Synthetic identifiers are not real and must not be replaced with PHI in the repo.
- Bed-placement optimization is a greedy heuristic, not a governed placement policy.
- Staffing sensitivity is illustrative until roster and workload feeds are validated.
- Chart summaries are deterministic mock summaries in local mode.
- Snowflake write-back for registries and audit logs requires approved target tables.

## Known Risk Areas

- Timestamp missingness and reversed intervals can bias wait and LOS estimates.
- Facility-level calibration may differ materially by site, season, triage mix, and inpatient capacity.
- Arrival surges and boarding cascades can create nonlinear effects that simple models understate.
- MRN/chart mapping errors would be high risk in chart-review workflows.

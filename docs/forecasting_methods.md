# Forecasting Methods

Forecasting is implemented in the Python capability kernel and existing `src/ed_flow_intelligence.modeling` module.

Current methods:

- seasonal naive baseline
- moving-average baseline
- Ridge regression
- random forest regression
- weighted ensemble
- P10/P50/P90 uncertainty intervals
- holdout validation
- rolling-origin backtest
- feature driver summaries
- model registry rows with limitations and lineage

The public showcase consumes exported results only. It does not rebuild models in TypeScript.

Snowflake validation requirements:

- facility-specific calibration
- date-based holdout
- surge-period holdout
- calibration by pediatric/all-age segment
- top-decile surge recall
- interval coverage checks
- drift monitoring after deployment

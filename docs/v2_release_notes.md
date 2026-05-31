# V2 Release Notes

## Backup

Before v2 implementation, v1 was preserved as:

- Branch: `backup/v1-current-state-20260531-0952`
- Tag: `v1-current-state-20260531-0952`
- Local backup: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952`
- Bundle: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952\ahs-ed-flow-intelligence-v1-20260531-0952.bundle`

See [v2_backup_manifest.md](v2_backup_manifest.md).

## Added

- 16-tab Streamlit v2 experience.
- Public/open-data source registry and synthetic fallback cache.
- Public pressure map, wait-time monitor, respiratory surge, weather/AQHI/smoke, travel friction, and public scenario workbench.
- Hybrid forecasting lab joining internal-ready flow with public pressure context.
- Final lineage and refresh-status tab.
- Snowflake SQL transfer templates.
- V2 docs and tests.

## Preserved

- Synthetic-only local data policy.
- `TB_ED_VISITS` constrained module boundary.
- Mock model client as local default.
- Snowflake access isolated in `src/ed_flow/snowflake_backend.py`.
- Model-provider access isolated in `src/ed_flow/ai_layer.py`.

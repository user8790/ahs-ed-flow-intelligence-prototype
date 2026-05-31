# Open Data Refresh Strategy

## Local Prototype

Local mode calls `ensure_public_open_data()` and reads CSVs from `data/open/`. The sidebar refresh button regenerates synthetic fallback data and clears the Streamlit data cache.

## Snowflake Target

Use Snowflake landing tables in `OPEN_DATA`:

- `OPEN_DATA.AHS_ED_WAIT_TIMES`
- `OPEN_DATA.AB_RESPIRATORY_SURVEILLANCE`
- `OPEN_DATA.ENVIRONMENTAL_STRESS`
- `OPEN_DATA.TRAVEL_FRICTION`
- `OPEN_DATA.CALENDAR_CONTEXT`

Task shells are in [sql/snowflake/open_data_tasks.sql](../sql/snowflake/open_data_tasks.sql). Replace placeholder task bodies with approved API, stage, or external-access integrations.

## Required Refresh Metadata

Each refresh job should write:

- source id
- refresh timestamp
- source timestamp range
- row count
- status
- error or fallback reason
- official source URL or API endpoint
- licensing/terms note where needed

## Failure Mode

If a public feed fails, the app should show stale/missing/fallback status and continue using internal-ready analytics. Public pressure should never silently become clinical truth.

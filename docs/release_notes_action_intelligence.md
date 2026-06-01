# Release Notes: Action Intelligence

This branch adds a separate Action Intelligence app without changing the existing production Streamlit app.

Highlights:

- new Streamlit entry point at `apps/streamlit_action_intelligence/app.py`
- shared `ed_flow_kernel` package
- command huddle cockpit
- public shock scenario-to-action workflow
- enhanced simulation and bottleneck migration
- Snowflake activation workbench
- lineage and validation tab
- local synthetic mode with no Snowflake credentials

Known limits:

- still synthetic/local until governed Snowflake data is connected
- model outputs require internal validation before operational pilot
- chart-review semantic views remain contract-only in public/local mode

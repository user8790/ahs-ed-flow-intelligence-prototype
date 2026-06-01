# Streamlit Cloud Deployment

This app is deployed as a separate Streamlit Cloud app. Do not modify the existing `ahs-ed-flow-intelligence` deployment.

- Repository: `user8790/ahs-ed-flow-intelligence-prototype`
- Branch: `feature/action-intelligence-kernel-and-showcase-v4`
- Main file path: `apps/streamlit_action_intelligence/app.py`
- App slug: `ahs-ed-flow-action-intelligence`
- URL: `https://ahs-ed-flow-action-intelligence.streamlit.app/`
- Secrets required for local/public demo: none
- Data mode: synthetic/public fallback only
- Deployment status: live and smoke-tested on 2026-06-01

Snowflake credentials or Streamlit secrets must not be added to this public deployment. Secure Snowflake configuration belongs in governed AHS runtime only.

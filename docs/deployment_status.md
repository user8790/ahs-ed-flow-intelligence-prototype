# Deployment Status

Updated: 2026-06-01

## Existing Production App

- URL: `https://ahs-ed-flow-intelligence.streamlit.app/`
- Status: preserved
- Branch: `main`
- Entry point: `app.py`
- This branch does not repoint or redeploy it.

## Restore Point

- Restore branch: `restore/pre-action-intelligence-and-showcase-20260601-0726`
- Restore tag: `restore-pre-action-intelligence-and-showcase-20260601-0726`
- Bundle: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo.bundle`
- Files backup: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo-files\`

## Action Intelligence Streamlit App

- Entry point: `apps/streamlit_action_intelligence/app.py`
- Suggested slug: `ahs-ed-flow-action-intelligence`
- Preferred URL: `https://ahs-ed-flow-action-intelligence.streamlit.app/`
- Local mode: working with synthetic/public fallback data
- Secrets required: none for local/public demo
- Deployment status: ready for new Streamlit Cloud app creation from `feature/action-intelligence-kernel-and-showcase-v4`
- Current blocker: Streamlit Cloud showed a sign-in screen in the in-app browser. User interactive sign-in is required before creating the new app.

## Public Showcase

- App: `apps/public_showcase`
- Route: `/Reimagining-Alberta-ED-Flow-Intelligence`
- Lowercase redirect: configured
- Preferred SAO URL: `https://www.sao-advisory.com/Reimagining-Alberta-ED-Flow-Intelligence`
- Local build: passing
- Standalone Vercel deployment: `https://reimagining-alberta-ed-flow-intelli.vercel.app/Reimagining-Alberta-ED-Flow-Intelligence`
- Lowercase route verified: `https://reimagining-alberta-ed-flow-intelli.vercel.app/reimagining-alberta-ed-flow-intelligence`
- Deployment status: standalone Vercel deployed; SAO integration awaits repo/project access
- Vercel/SAO note: `www.sao-advisory.com` is currently aliased in Vercel to an existing project (`v0-image-analysis...`). This branch did not modify or replace that production site.

## Validation

- Python compile: passed with `python -m compileall app.py apps packages src`
- Python tests: 39 passed with `python -m pytest`
- Public artifact export: passed and generated 22 JSON artifacts
- Next typecheck: passed with `npm run typecheck`
- Next audit: passed with `npm audit --audit-level=moderate`
- Next build: passed with `npm run build`
- Browser smoke: passed for local Action Intelligence Streamlit app and public showcase route
- Vercel deployment: completed as standalone fallback
- Streamlit deployment: blocked pending interactive Streamlit Cloud sign-in

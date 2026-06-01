# Agent Notes

This repository is a synthetic local prototype for AHS ED flow intelligence. It is designed to move later into a governed Snowflake environment.

## Operating Rules

- Use synthetic data only in this repository.
- Do not add real MRNs, PHNs, ULIs, birthdates, postal codes, chart notes, patient IDs, provider IDs, or private facility extracts.
- Preserve the constrained-module boundary: it must only use fields available in `TB_ED_VISITS`.
- Keep Snowflake access isolated in `src/ed_flow/snowflake_backend.py`.
- Keep model calls isolated in `src/ed_flow/ai_layer.py`; local default must remain `MockModelClient`.
- Keep public/open-data connectors and fallback status explicit in `src/ed_flow_intelligence/data_sources/` and `config/data_sources.yml`.
- Public/open-data values in local mode are synthetic fallbacks unless explicitly replaced by approved Snowflake jobs.
- Protect secrets. Never print, commit, or push credentials, tokens, private extracts, or PHI.
- Keep public mode functional without Snowflake credentials.
- Keep Snowflake imports guarded and optional for local development.
- Maintain open/synthetic/internal-ready/aspirational lineage on data and model outputs.
- Every model output needs validation context, uncertainty, baseline comparison, and limitations.
- Every scenario output needs operational interpretation, watch-points, implementation friction, and human-in-the-loop framing.
- Do not add dead tabs, dead buttons, placeholder-only pages, or unexplained synthetic numbers.
- Prefer interpretable models first; AI narratives may explain results but must not generate numeric results.
- Update docs when behavior changes.
- Keep Snowflake portability central: SQL templates, backend boundaries, feature views, audit logs, and activation sequence.
- AI narrative output can explain or summarize; it must not be the source of simulation results.
- When adding scenario controls, document the assumed mechanism and validation requirement.
- Never modify, repoint, or redeploy the existing production Streamlit app without explicit user instruction.
- Keep new Action Intelligence and public showcase work on feature branches/worktrees until explicitly merged.
- Keep the shared capability kernel UI-independent: no Streamlit, React, Next.js, browser, or Vercel imports in `packages/ed_flow_kernel`.
- Do not duplicate analytical logic in the Vercel app; export public-safe artifacts from the Python kernel.
- Public artifacts must not contain real patient identifiers, secure AHS data, secrets, or private endpoints.
- Run Python compile/tests and public-showcase typecheck/build before completion.

## Validation Commands

```powershell
python -m pytest
python -m compileall src app.py
python -m compileall app.py apps packages src
python -c "import app; print('app import ok')"
cd apps/public_showcase
npm run typecheck
npm run build
```

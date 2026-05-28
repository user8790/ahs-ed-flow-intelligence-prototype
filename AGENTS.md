# Agent Notes

This repository is a synthetic local prototype for AHS ED flow intelligence. It is designed to move later into a governed Snowflake environment.

## Operating Rules

- Use synthetic data only in this repository.
- Do not add real MRNs, PHNs, ULIs, birthdates, postal codes, chart notes, patient IDs, provider IDs, or private facility extracts.
- Preserve the constrained-module boundary: it must only use fields available in `TB_ED_VISITS`.
- Keep Snowflake access isolated in `src/ed_flow/snowflake_backend.py`.
- Keep model calls isolated in `src/ed_flow/ai_layer.py`; local default must remain `MockModelClient`.
- AI narrative output can explain or summarize; it must not be the source of simulation results.
- When adding scenario controls, document the assumed mechanism and validation requirement.

## Validation Commands

```powershell
python -m pytest
python -m compileall src app.py
python -c "import app; print('app import ok')"
```


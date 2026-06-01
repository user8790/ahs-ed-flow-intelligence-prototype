# Capability Kernel Architecture

The Action Intelligence branch separates computation from presentation.

```text
Shared Python capability kernel
  contracts -> data-source registry -> features -> forecasting -> simulation
     -> action interpretation -> public artifact export -> governance metadata

Presentation surfaces
  existing app.py on main
  apps/streamlit_action_intelligence/app.py
  apps/public_showcase Next.js route
```

The kernel lives in `packages/ed_flow_kernel` and is exposed from the repository root through `ed_flow_kernel/__init__.py` so commands like `python -m ed_flow_kernel.exports.public_showcase_export` work from the repo root.

The kernel must not import Streamlit, React, Next.js, Vercel APIs, browser APIs, or UI components. Existing analytical modules in `src/ed_flow` and `src/ed_flow_intelligence` remain compatibility layers and are wrapped by the kernel rather than duplicated.

## Current Kernel Areas

- `contracts/`: TB_ED_VISITS, semantic-view, open-data, secure-placeholder, and public-artifact contracts.
- `backends/`: local and guarded Snowflake backend factories.
- `features/`: public site-hour features, constrained TB_ED_VISITS features, hybrid internal-ready targets.
- `forecasting/`: baselines, ensemble wrappers, intervals, validation, registry helpers.
- `simulation/`: public shocks, enhanced simulation, LWBS hazard, action interpretation.
- `exports/`: public-safe Vercel artifact export.
- `governance/`: privacy checks for public artifacts.

## Public Artifact Rule

The Vercel app consumes static JSON from `apps/public_showcase/public/data`. It may animate, sort, and display values, but it must not recreate the core forecasting/simulation logic in TypeScript.

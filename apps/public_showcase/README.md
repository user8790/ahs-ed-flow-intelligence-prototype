# Reimagining Alberta ED Flow Intelligence

Public Vercel showcase for a Stollery-focused ED flow intelligence product demo.

This is not a live AHS operational tool. It uses public references, public/open-data-shaped context signals, and synthetic internal ED operating data only. It contains no real patient data, real identifiers, secure AHS data, private Snowflake data, or private endpoints.

## Product Structure

The app is a one-page interactive showcase with four sections:

1. Open Data Context
2. Synthetic Stollery ED Operating Reality
3. Blended Predictive Intelligence
4. Scenario & What-If Studio

The baseline forecasts are loaded from generated JSON artifacts and remain fixed. Scenario sliders and presets update browser-side comparator outputs through `lib/scenarioEngine.ts`.

## Run Locally

```powershell
cd apps/public_showcase
npm install
npm run typecheck
npm run build
npm run dev
```

## Regenerate Public Artifacts

From the repository root:

```powershell
python -m ed_flow_kernel.exports.stollery_public_showcase_export --out apps/public_showcase/public/data --seed 20260601
```

Required artifacts are named `stollery_*.json` and include schema version, generation timestamp, focus site, data mode, source type, synthetic flag, caveats, and data.

## Deployment

Standalone Vercel project:

`https://reimagining-alberta-ed-flow-intelli.vercel.app/Reimagining-Alberta-ED-Flow-Intelligence`

The route is also reachable through the lowercase redirect:

`https://reimagining-alberta-ed-flow-intelli.vercel.app/reimagining-alberta-ed-flow-intelligence`

No secrets or environment variables are required.

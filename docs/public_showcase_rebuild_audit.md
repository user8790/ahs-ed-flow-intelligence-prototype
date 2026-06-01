# Public Showcase Rebuild Audit

Updated: 2026-06-01

## Current State

The public showcase is a standalone Next.js app in `apps/public_showcase`.

- Current branch before rebuild: `feature/action-intelligence-kernel-and-showcase-v4`
- Rebuild branch: `feature/rebuild-stollery-public-vercel-showcase`
- Current route: `/Reimagining-Alberta-ED-Flow-Intelligence`
- Current Vercel project: `reimagining-alberta-ed-flow-intelligence`
- Current standalone deployment: `https://reimagining-alberta-ed-flow-intelli.vercel.app/Reimagining-Alberta-ED-Flow-Intelligence`
- Framework: Next.js, TypeScript, React, minimal custom CSS
- Data loading: server-side JSON reads from `apps/public_showcase/public/data`
- Artifact export: `python -m ed_flow_kernel.exports.public_showcase_export --out apps/public_showcase/public/data --mode public_demo --seed 20260601`

The existing app renders a static public showcase with sections for an Alberta pressure cockpit, scenario theatre, digital twin canvas, respiratory story, Snowflake portability, lineage/trust, research-to-capability mapping, and validation posture.

## Why The Current Showcase Fails The Product Intent

The current showcase is technically useful but not the right public-facing product story. It foregrounds architecture, Snowflake transfer, lineage, governance, and research mapping. Those are valuable internal readiness topics, but they make the public experience feel like an implementation appendix rather than a memorable product demonstration for Stollery ED leaders.

The current experience also has limited interaction. Scenario outputs are exported as fixed artifacts and do not respond to user controls. The site is broad-Alberta rather than Stollery-first, and the synthetic internal operating state is not rich enough to feel like a credible pediatric ED command layer.

## Sections To Remove Or De-Emphasize

- Snowflake Portability Story as a major public section
- Research-to-Capability Map as a major public section
- Data Lineage and Trust as a major public section
- Architecture-heavy implementation diagrams
- Long governance copy
- Generic province-wide framing that dilutes the Stollery focus

Short caveats should remain, but only as concise public/synthetic/no-patient-data boundary notes.

## Components To Salvage

- Standalone Next.js app structure
- Route and lowercase redirect pattern
- Static JSON artifact loading
- Public-safe artifact envelope concept
- Shared kernel export pattern
- Vercel project linkage
- Existing privacy/PHI test posture
- Some colour/token ideas, after redesign

## Data Artifacts To Reuse

The previous artifacts are useful as a starting point for source categories and export mechanics, but the public app should replace them with Stollery-specific artifacts:

- open-data context
- public facts and assumptions
- synthetic ED history
- synthetic current state
- synthetic unit capacity
- baseline forecasts
- model drivers
- validation summary
- scenario catalog, coefficients, presets, result grid
- huddle briefs
- UI copy

## Synthetic Datasets To Expand

The rebuild needs richer synthetic data for:

- pediatric age bands and CTAS mix
- hourly arrivals and seasonal trends
- waiting, triage, rooming, physician, diagnostics, consult, disposition, boarding, EMS offload, and transfer queues
- pediatric resource pools
- inpatient unit/service receiving capacity
- bed cleaning and pending discharge timing
- 12 to 24 months of historical trends
- baseline forecasts with P10/P50/P90 intervals
- deterministic scenario coefficients and comparator outputs

## Deployment Path

The repo already controls a standalone Vercel project through `apps/public_showcase/.vercel/project.json`. The safe path is:

1. Rebuild locally on `feature/rebuild-stollery-public-vercel-showcase`.
2. Regenerate JSON artifacts under `apps/public_showcase/public/data`.
3. Run Python tests, TypeScript check, and Next build.
4. Deploy preview with `npx vercel` if needed.
5. Deploy production with `npx vercel --prod` if the Vercel session remains authenticated and the project link is unchanged.

No secrets or private endpoints are required.

## Product Changes Required

The rebuilt showcase should feel like a sophisticated interactive public demo. It should have exactly four major sections:

1. Open Data Context
2. Synthetic Stollery ED Operating Reality
3. Blended Predictive Intelligence
4. Scenario & What-If Studio

The central product change is browser-side scenario state. Baseline forecasts, baseline tables, and baseline charts must stay fixed. Scenario controls and presets should recompute comparator outputs deterministically, widen uncertainty under stress, update huddle interpretation, and show bottleneck migration.

## Rebuild Decision

This will be a ground-up replacement of the current public showcase UI and public artifacts while preserving the safe standalone Next/Vercel structure and shared-kernel export pattern.

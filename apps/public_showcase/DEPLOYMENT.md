# Public Showcase Deployment

Current standalone destination:

`https://reimagining-alberta-ed-flow-intelli.vercel.app/Reimagining-Alberta-ED-Flow-Intelligence`

Latest verified production deployment:

`https://reimagining-alberta-ed-flow-intelligence-9i83nmlcl.vercel.app`

## Build

```powershell
cd apps/public_showcase
npm install
npm run typecheck
npm run build
```

## Deploy

Use the existing `.vercel/project.json` linkage unless intentionally moving projects.

```powershell
cd apps/public_showcase
npx vercel
npx vercel --prod
```

No environment variables, secrets, private endpoints, or paid Vercel features are required.

## Safety Notes

- Do not add AHS secure data or patient-level data to `public/data`.
- Do not add `.env` or `.streamlit/secrets.toml` material here.
- Public facts are cited in `docs/stollery_public_facts_and_synthetic_assumptions.md`.
- Synthetic assumptions and scenario mechanics are documented in `docs/stollery_synthetic_data_design.md` and `docs/stollery_scenario_engine.md`.

## SAO Advisory Site

The preferred long-term destination remains an integrated SAO Advisory page, but the current standalone project is the safe public deployment path. Do not overwrite the existing `www.sao-advisory.com` Vercel alias without explicit site/repo access and approval.

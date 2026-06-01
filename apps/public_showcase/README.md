# Reimagining Alberta ED Flow Intelligence

Public Vercel/Next.js showcase for SAO Advisory.

Route:

- `/Reimagining-Alberta-ED-Flow-Intelligence`
- Lowercase redirect: `/reimagining-alberta-ed-flow-intelligence`

Run locally:

```powershell
npm install
npm run typecheck
npm run build
npm run dev
```

Refresh public artifacts from the repository root:

```powershell
python -m ed_flow_kernel.exports.public_showcase_export --out apps/public_showcase/public/data --mode public_demo --seed 20260601
```

This app is public/synthetic only. It does not connect to Snowflake, AHS private systems, patient-level data, or secrets.

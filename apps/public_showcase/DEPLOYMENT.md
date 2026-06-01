# Deployment

Preferred destination:

`https://www.sao-advisory.com/Reimagining-Alberta-ED-Flow-Intelligence`

If the SAO Advisory site repository is available, copy or merge this route into the existing site on a feature branch and deploy a Vercel preview first.

Standalone fallback:

```powershell
cd apps/public_showcase
npm install
npm run build
npx vercel
npx vercel --prod
```

Suggested standalone project name:

`reimagining-alberta-ed-flow-intelligence`

Current standalone deployment:

`https://reimagining-alberta-ed-flow-intelli.vercel.app/Reimagining-Alberta-ED-Flow-Intelligence`

No environment variables or secrets are required. Avoid paid Vercel features on the Hobby account.

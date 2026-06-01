# SAO Advisory Integration Plan

No local SAO Advisory website repository was found during restore-point discovery. The current branch therefore contains a standalone Next.js implementation that can be copied into the SAO site or deployed independently.

## Preferred Path

1. Locate or clone the SAO Advisory website repository.
2. Create branch `feature/reimagining-alberta-ed-flow-intelligence-page`.
3. Copy the route and components from `apps/public_showcase`.
4. Preserve existing SAO site styles and navigation.
5. Add route `/Reimagining-Alberta-ED-Flow-Intelligence`.
6. Add lowercase redirect `/reimagining-alberta-ed-flow-intelligence`.
7. Build and deploy a Vercel preview.
8. Promote to production only after review.

## Fallback Path

Deploy `apps/public_showcase` as a standalone Vercel Hobby project named `reimagining-alberta-ed-flow-intelligence`, then link from SAO Advisory later.

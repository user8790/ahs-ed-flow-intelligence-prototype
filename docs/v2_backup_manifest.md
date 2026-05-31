# V2 Backup Manifest

Created before Prototype v2 implementation.

## Snapshot

- Timestamp: `20260531-0952`
- Source branch at backup time: `main`
- Source commit: `6598758470bf1911a1e461d81ed9e3b02fd041ac`
- Remote: `https://github.com/user8790/ahs-ed-flow-intelligence-prototype.git`
- Backup branch: `backup/v1-current-state-20260531-0952`
- Backup tag: `v1-current-state-20260531-0952`
- Local filesystem backup: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952`
- Git bundle: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952\ahs-ed-flow-intelligence-v1-20260531-0952.bundle`

## Verification Commands Used

```powershell
git status --short --branch
git branch --show-current
git remote -v
git log --oneline -n 10
git branch backup/v1-current-state-20260531-0952 HEAD
git tag -a v1-current-state-20260531-0952 -m "Backup v1 current state 20260531-0952" HEAD
git bundle create "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952\ahs-ed-flow-intelligence-v1-20260531-0952.bundle" --all
git push origin backup/v1-current-state-20260531-0952
git push origin v1-current-state-20260531-0952
```

## Backup Copy Exclusions

The filesystem copy intentionally excluded local-only runtime and cache directories:

- `.git`
- `.runtime`
- `tools`
- `__pycache__`
- `.pytest_cache`
- `.ruff_cache`
- `.venv`
- `venv`
- `env`
- `.mypy_cache`

Git history is preserved in the git bundle and remote branch/tag. The filesystem copy is a working-tree recovery copy.

## Secrets And PHI Status

- No real PHI, MRNs, PHNs, ULIs, birthdates, chart notes, provider identifiers, or private extracts were added.
- No `.env` file or secrets were found in the tracked v1 state.
- Local prototype data remains synthetic.

## Recovery

To restore the exact v1 code state from GitHub:

```powershell
git fetch origin
git checkout v1-current-state-20260531-0952
```

To inspect the local bundle:

```powershell
git clone "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-v1-backup-20260531-0952\ahs-ed-flow-intelligence-v1-20260531-0952.bundle" ahs-ed-flow-v1-restore
```

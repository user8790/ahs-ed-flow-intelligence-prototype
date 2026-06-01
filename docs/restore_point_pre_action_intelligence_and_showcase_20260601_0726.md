# Restore Point: Pre Action Intelligence and Showcase

Created: 2026-06-01 07:26 America/Los_Angeles

This restore point preserves the colleague-portable state of the AHS ED Flow Intelligence prototype before starting the separate Action Intelligence capability-kernel and public showcase work.

## Source State

- Source branch: `main`
- Source commit SHA: `b2ca6f1784d1c71a5b52b6c00e6e9f9c95292cf2`
- Repository: `https://github.com/user8790/ahs-ed-flow-intelligence-prototype`
- Remote names:
  - `origin` fetch: `https://github.com/user8790/ahs-ed-flow-intelligence-prototype.git`
  - `origin` push: `https://github.com/user8790/ahs-ed-flow-intelligence-prototype.git`
- Remote default branch: `main`
- Current app entry point: `app.py`
- Current public Streamlit URL: `https://ahs-ed-flow-intelligence.streamlit.app/`
- Current Streamlit deployment branch: not directly discoverable from local git; current public deployment is known to use `main` and `app.py`.
- Existing Vercel/SAO Advisory repo status: no local SAO Advisory repo was found under the inspected local document/workspace directories.
- Vercel CLI status: not installed or not available on `PATH` at restore time.
- GitHub CLI status: installed and authenticated enough to inspect the current repository.

## Restore Assets

- Restore branch: `restore/pre-action-intelligence-and-showcase-20260601-0726`
- Restore branch push: succeeded
- Restore tag: `restore-pre-action-intelligence-and-showcase-20260601-0726`
- Restore tag push: succeeded
- Git bundle: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo.bundle`
- Git bundle verification: succeeded
- Local filesystem backup: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo-files\`
- Feature worktree for new work: `C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-action-v4`
- Feature branch for new work: `feature/action-intelligence-kernel-and-showcase-v4`

## Secret and Config File Check

Detected repo-local config/template files:

- `.env.example`
- `.streamlit/config.toml`

No `.streamlit/secrets.toml`, real `.env`, Snowflake credentials, Streamlit credentials, Vercel tokens, OpenAI keys, or GitHub tokens were found in the repository tree during the restore-point scan. Certificate files inside `.venv` were detected but excluded from the file backup because `.venv` is not part of the source restore archive.

## Files Intentionally Excluded From Filesystem Backup

The Git bundle preserves repository history and refs. The filesystem backup intentionally excludes local/generated directories and binary cache noise:

- `.git`
- `.venv`
- `.runtime`
- `.pytest_cache`
- `__pycache__`
- `*.pyc`
- `*.pyo`

## Commands Recorded

```powershell
git status --short --branch
git branch --show-current
git remote -v
git log --oneline -n 10
git rev-parse HEAD
git remote show origin
git branch restore/pre-action-intelligence-and-showcase-20260601-0726 b2ca6f1784d1c71a5b52b6c00e6e9f9c95292cf2
git tag restore-pre-action-intelligence-and-showcase-20260601-0726 b2ca6f1784d1c71a5b52b6c00e6e9f9c95292cf2
git bundle create "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo.bundle" --all
git bundle verify "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo.bundle"
git push origin restore/pre-action-intelligence-and-showcase-20260601-0726
git push origin restore-pre-action-intelligence-and-showcase-20260601-0726
git worktree add -b feature/action-intelligence-kernel-and-showcase-v4 "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-action-v4" main
```

## Restore From Remote Branch

```powershell
git fetch origin
git switch main
git reset --hard restore/pre-action-intelligence-and-showcase-20260601-0726
```

Only run `git reset --hard` when intentionally restoring and after preserving any newer work.

## Restore From Tag

```powershell
git fetch origin --tags
git switch -c restored-pre-action-intelligence restore-pre-action-intelligence-and-showcase-20260601-0726
```

## Restore From Bundle

```powershell
cd "C:\Users\carrc\OneDrive\Documents"
git clone "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo.bundle" ahs-ed-flow-intelligence-restored-from-bundle
cd ahs-ed-flow-intelligence-restored-from-bundle
git switch main
```

## Restore From Filesystem Backup

```powershell
Copy-Item -Recurse -Force `
  "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restore-20260601-0726\repo-files" `
  "C:\Users\carrc\OneDrive\Documents\ahs-ed-flow-intelligence-restored-files"
```

## Production Protection Note

The existing public Streamlit app `https://ahs-ed-flow-intelligence.streamlit.app/` must not be repointed or redeployed by the Action Intelligence work. New development continues on `feature/action-intelligence-kernel-and-showcase-v4` and should use a separate Streamlit app slug: `ahs-ed-flow-action-intelligence`.

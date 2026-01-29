# Contributing

Thanks for contributing to Narrative Flow! This guide keeps the branching and release flow simple and predictable.

## Quick Rules

- **Feature work:** create a branch from `develop`
- **Merge to develop:** **squash merge only**
- **Promotion to main:** automated PR from `develop` → `main`, **merge commit only**
- **Release PR on main:** created by release-please, **merge commit only**
- **Back-merge to develop:** automated PR from `main` → `develop`, **auto-merged with merge commit**

## Workflow (Step-by-step)

1. Create a feature branch from `develop`.
2. Open a PR into `develop`.
3. **Squash merge** the PR into `develop`.
4. The repo automation opens a **promotion PR** (`develop` → `main`).
5. **Merge commit** the promotion PR.
6. release-please opens a **release PR** on `main`.
7. **Merge commit** the release PR to publish a GitHub Release.
8. The back-merge PR (`main` → `develop`) is auto-merged with a **merge commit**.

## Why we avoid squash in two places

- **Promotion PRs** and **back-merge PRs** must use merge commits to preserve ancestry.
- Squashing those two creates confusing diffs and can re-open empty promotion PRs.

## Commands people usually run

```bash
# Feature branch
git checkout develop
git checkout -b feature/my-change

# Push + PR
git push -u origin feature/my-change

# After PR is merged, automation handles the rest.
```

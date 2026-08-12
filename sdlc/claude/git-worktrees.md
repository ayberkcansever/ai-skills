# Git Worktrees

Ensure work happens in an isolated workspace without disturbing the current
checkout. Detect first, ask consent, then create.

**Announce at start:** "I'm using the git-worktrees skill to set up an isolated workspace."

## Step 1: Detect existing isolation

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree. Report path + branch,
  skip to Step 3. Exception: if `git rev-parse --show-superproject-working-tree`
  prints a path, you are in a submodule, not a worktree — treat as normal repo.
- `GIT_DIR == GIT_COMMON` → normal checkout, continue.

## Step 2: Create the worktree (consent required)

Ask once, unless the user already told you their preference:

> "Set up an isolated worktree? It protects your current branch and
> uncommitted work."

If declined, work in place and stop here.

If your harness offers a native worktree tool, use it and skip the manual
steps. Otherwise:

```bash
# .worktrees/ must be ignored — check before creating
git check-ignore -q .worktrees || echo ".worktrees/" >> .gitignore

git worktree add .worktrees/<branch-name> -b <branch-name>
cd .worktrees/<branch-name>
```

Branch name follows repo conventions (ticket key first, e.g.
`PROJ-123-short-description`). Base it on the branch the user names, or the
current branch by default.

## Step 3: Project setup

Run the project's install + baseline check so failures later are attributable
to the new work, not the environment:

```bash
npm install && npm run compile   # or: pip install -r requirements.txt / make test-fast
```

Baseline must pass before any edit. If it fails, report and stop — do not
build on a broken base.

## Step 4: Cleanup (at finish, after merge or explicit user OK)

```bash
git worktree remove .worktrees/<branch-name>
git branch -d <branch-name>   # only if merged
```

Never remove a worktree with uncommitted changes without explicit confirmation.

## Rules

- Never create a worktree inside another worktree — Step 1 prevents this.
- Never start implementation on `main`/`master`; a worktree with a feature
  branch is the default answer when the user is parked on a protected branch.
- `.worktrees/` stays gitignored; a tracked worktree directory pollutes status
  for every other checkout.

---
name: git-worktrees
description: >-
  Set up an isolated git worktree so the current checkout stays untouched and
  several tickets can run at once on one repo. Detects existing isolation and
  reuses a ticket's worktree, creates or attaches .worktrees/<branch>, verifies
  setup. Use when the user asks for a worktree; execute-plan calls it for every
  run (consent implied there).
---

# Git Worktrees

Ensure work happens in an isolated workspace without disturbing the current
checkout. Detect first, ask consent, then create.

**Announce at start:** "I'm using the git-worktrees skill to set up an isolated workspace."

## Step 1: Detect existing isolation

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
git worktree list
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree. Report path + branch,
  skip to Step 3. Exception: if `git rev-parse --show-superproject-working-tree`
  prints a path, you are in a submodule, not a worktree — treat as normal repo.
- `git worktree list` already shows a worktree for this ticket → `cd` into it
  and skip to Step 3. Never create a second one for the same ticket.
- `GIT_DIR == GIT_COMMON` and no ticket worktree → normal checkout, continue.

## Step 2: Create the worktree

**Consent:** ask once, unless the user already told you their preference —

> "Set up an isolated worktree? It protects your current branch and
> uncommitted work."

If declined, work in place and stop here. **Invoked from execute-plan, consent
is implied and this question is skipped**: that skill executes in a worktree by
definition, and the user opted in by running it.

Path is `.worktrees/<branch-name>`; branch name follows repo conventions —
ticket key first, e.g. `PROJ-123-short-description`.

If your harness offers a native worktree tool, use it and skip the manual
steps. Otherwise:

```bash
# .worktrees/ must be ignored — check before creating
git check-ignore -q .worktrees || echo ".worktrees/" >> .gitignore
```

Then pick the mode by what the branch already is — **a branch can be checked
out in only one worktree at a time**, so this is a git constraint, not a
preference:

| Branch state | Command |
|---|---|
| Does not exist | `git worktree add .worktrees/<branch> -b <branch> <base>` |
| Exists, not checked out anywhere | `git worktree add .worktrees/<branch> <branch>` |
| Exists, checked out in another worktree | stop — report which, and either reuse that worktree or pick a different branch |
| Exists, checked out in the user's own checkout | stop and ask: switch that checkout off the branch, or execute in place |

`<base>` defaults to the repo's default branch (`origin/HEAD`) for new work;
use the branch the user names when they name one.

```bash
cd .worktrees/<branch-name>
```

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
- One worktree per ticket, reused across runs. Several **different** tickets
  may hold worktrees at once — that is how parallel work on one repo is done.
- Never start implementation on `main`/`master`; a worktree with a feature
  branch is the default answer when the user is parked on a protected branch.
- `.worktrees/` stays gitignored; a tracked worktree directory pollutes status
  for every other checkout.
- A gitignored path does **not** exist in a new worktree. Anything the work
  depends on that git does not track — WIP plans and specs, `.env` files,
  local config — must be copied in deliberately. The caller owns that copy
  (see execute-plan Step 2).

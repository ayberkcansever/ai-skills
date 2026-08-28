# Git Worktrees

Ensure work happens in an isolated workspace without disturbing the current
checkout. Detect first. Consent only when the user invoked this skill
directly; execute-plan skips the consent question, not this skill.

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
- Current branch already matches this ticket (`git branch --show-current`
  contains the ticket key) → this checkout is the venue. Skip Step 2.
  Go to Step 3.
- `GIT_DIR == GIT_COMMON` and no ticket worktree → normal checkout, continue.

## Step 2: Create the worktree

**Consent:** ask once, unless the user already told you their preference —

> "Set up an isolated worktree? It protects your current branch and
> uncommitted work."

If declined, stop. Do not execute in the current checkout. **Invoked from
execute-plan, consent is implied and this question is skipped**: execute-plan
only reaches this skill when the checkout is not already on the ticket
branch.

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
| Exists, checked out in this checkout | this checkout is the venue — skip create, go to Step 3. Do not stop. |

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
- The worktree's branch is never `main`/`master`. The user's checkout may
  stay on a protected branch — that is the point.
- `.worktrees/` stays gitignored; a tracked worktree directory pollutes status
  for every other checkout.
- A gitignored path does **not** exist in a new worktree. Anything the work
  depends on that git does not track — WIP plans and specs, `.env` files,
  local config — must be copied in deliberately. The caller owns that copy
  (see execute-plan Step 2).

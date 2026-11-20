---
name: implement-plan
description: >-
  Implement a prepare-plan plan: run tasks as parallel subagent waves, verify
  every gate yourself, commit per task, then run review-build until ship. Use
  when the user says implement or execute the plan (sdlc-lite chain).
argument-hint: "[plan name or path]"
disable-model-invocation: true
---

# Implement Plan

You are the orchestrator. Subagents write code; you own verification, git,
and the plan file.

Input: $ARGUMENTS

**Reads:** the plan, its spec, `docs/quirks.md`, git history.
**Writes:** code (through subagents), `[T<N>]` commits, the plan's state
lines, and new spec decisions the user approves.

## Invariants

- The plan folder (`<root>/docs/plans/<plan>/`, `<root>` the main checkout)
  is never committed, copied, or moved — one live copy, read by absolute path.
- Every subagent is a fresh Agent-tool subagent given only paths and its
  task — never a fork of this conversation, which would carry its context in.
- The plan file is the state: checkboxes, `> Gate:`, `> Drift:`, `## Review`,
  `## Blockers`, `## E2E`. After a context compaction, re-read the plan and
  spec; resume from them, never from memory.
- Only you commit, tick checkboxes, and write the plan and spec. Subagents
  edit and test.
- Tick a task only after you re-ran its gate yourself. A subagent's "done" is
  a claim, not evidence.
- Commit only the paths the task changed: `git add -- <paths>`, then
  `git commit -m "[T<N>] <summary>" -- <paths>`, then check
  `git show --name-only --format= HEAD` lists only those. A plain
  `git commit` takes the whole index, including a wave-mate's staged
  `git rm`. Never `git add .` / `-A` — it sweeps in unrelated files such as
  a copied `.env`.
- Never weaken a gate or flip an assertion to go green.
- Run to the end. Stop for the user only on a blocker, behaviour the spec does
  not decide, drift that changes a decision, contract, or later task, a
  `block` verdict, or an action others can see (push, PR, deploy). Ask through
  `AskUserQuestion` with a recommended option. Don't end a turn announcing a
  next step you could take.

## Checks

Each check runs at its own step and nowhere else. The plan's `**Checks:**`
names the commands; the repo's instructions (`AGENTS.md` / `CLAUDE.md`)
win over the plan, and the defaults below apply only where neither says.

| Check | When | Default |
|---|---|---|
| task | each task's gate and commit | the task's own test files |
| fast | after each wave; after a rebase that brought in commits | the full suite when it runs in about two minutes, else the tests covering the wave's files |
| release | once, at Release checks | the full suite plus what CI runs (lint, typecheck, format, build) |

- A task `Gate:` that names a release-only check (the whole suite, a
  database, an e2e stack) runs the narrow equivalent there; its `> Gate:`
  line says `deferred to Release checks`.
- Don't re-run a green check after a commit that cannot affect it (docs,
  another module's tests); say which earlier run still covers it.
- **Light finish** — `light finish: yes` in the plan, or the user's words
  `light finish` / "skip heavy checks": the release checks and the review
  loop are skipped (the user may still ask for a review); the fast check and
  the quick CI steps (lint, typecheck) still run. If the diff touches money,
  auth, deploy, migration or alerting code, or a path the repo names as
  risky, list those files and ask once whether to skip anyway. Record
  `light finish: release checks skipped by the user` under `## Review` and
  in the last commit message. Only the user turns it on.

## 1. Load

`<root>` is the main checkout:
`root="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"`.
The input names a plan or a path → `$root/docs/plans/<plan>/plan.md` or that
path. No input → the plan prepared or implemented earlier in this session,
else the current branch name or its ticket key, else ask once. Read the plan
and its spec.
The spec's `**Status:**` is not `plan-approved`, or `## Open questions` is not
empty → stop and say the plan is not ready. Raise gaps or concerns before
touching code.

## 2. Venue

Every plan runs in its own worktree, never in the main checkout, so plans can
be implemented in parallel without touching each other or the user's tree.

- `git worktree list` shows `$root/.worktrees/<plan>` → reuse it (one per
  plan). Look it up by this path, not by branch — the branch may carry a
  slug.
- Otherwise create it under the main checkout:

  ```bash
  common="$(git rev-parse --path-format=absolute --git-common-dir)"
  root="$(dirname "$common")"
  git -C "$root" fetch origin    # no origin/HEAD → git -C "$root" remote set-head origin -a
  git -C "$root" check-ignore -q .worktrees || echo ".worktrees/" >> "$common/info/exclude"
  git -C "$root" worktree add ".worktrees/<plan>" -b <plan> --no-track origin/HEAD   # bare ticket key → append -<slug>
  # branch already exists: git -C "$root" worktree add ".worktrees/<plan>" <branch>
  ```

  Git refuses a branch checked out elsewhere: if the main checkout is on the
  plan's branch, ask the user to switch it — never switch it yourself.

Work in the venue by absolute path and `git -C`. `EnterWorktree` may enter
that path, never create it, and refuses when the session already sits in
another worktree. The worktree gets code only — subagents and the reviewer
read the plan folder by its absolute path, so it survives worktree removal.
Copy untracked build inputs (`.env`).

First run only (the branch has no `[T` commit yet): install and run the
fast check as the baseline (red → stop). Afterwards `git status --porcelain` must be
empty — add copied or generated files to `$common/info/exclude`. Then compare
with the spec's `Baseline:` SHA: if `git diff --stat <baseline> HEAD -- <the
plan's Files>` shows changes, re-check the plan's `file:line` references
against the current code and record differences as `> Drift:` before Task 1.

Report the venue path. On resume, reconcile with
`git log origin/HEAD..HEAD`: ticked without a `[T<N>]` commit → redo; commit
without a tick → re-run the gate and tick; an unticked task with uncommitted
changes → once no subagent is still working on it, fan it in if its gate
passes, else discard its changes and re-dispatch. A `wip(T<N>)` commit named
in `## Blockers` → continue from it and mark the entry resolved.

## 3. Run tasks in waves

Each round, the ready set is every unticked task where:

1. every `Depends on:` task is ticked (all tasks omit it → run sequentially;
   only some omit it → ask);
2. its `Files:` paths are disjoint from the rest of the wave (strip
   `:line-range` first);
3. its gate does not share mutable outputs with a wave-mate — port, build dir,
   test DB, coverage file. A repo-wide gate (typecheck, lint) reads siblings'
   half-written files: that task runs in a wave of its own;
4. it is not Release checks or the Review gate (step 4 runs those).

Dispatch the whole ready set as parallel Agent-tool calls
(`general-purpose`) in one message; they run in the background, so fan in
only after every one has reported. Each prompt contains: the absolute venue
path (work only there), the absolute plan and spec paths, the task number,
`docs/quirks.md` if present, the gate command verbatim, and the two lists
below.

How to build it — direction, not a checklist. Follow the intent; where the
case calls for something else, do that and say why in your report:

- Test first: write the task's tests, watch them fail for the stated reason,
  then write the least code that passes. Minimal means general — no
  hardcoded expected values or branches on test input; a test a constant
  would pass is too weak.
- Tests prove behaviour: assert on what the code produces — return value,
  output, stored state — not on calls to mocks, and keep the real code in
  the path; a test that still passes with the behaviour removed proves
  nothing. Keep them deterministic: no real clock, randomness, sleeps, or
  dependence on test order.
- Follow the Architecture constraints and the neighbouring code — layering,
  injected dependencies, error types, naming; reuse the named helpers.
- Simple over clever: the simplest code that fits its neighbours. Add an
  abstraction, parameter, or config when this task needs it, not in case a
  later one does; give each unit one job; extend the way the codebase
  already does (a new handler or strategy) rather than growing a conditional.
- Handle the failure modes you can name; never swallow an error.

Hard limits — the tree, the plan, and the data are shared:

- Stay inside the task's `Files:`; wave-mates are editing the rest of the
  tree. No drive-by refactors, and no dependency the plan does not name.
- Never delete, skip, or loosen an existing test or assertion, except those
  the task's `Tests:` names. Another one that must change → change it and
  report it as `> Drift:` with the reason.
- Keep old callers, readers, and stored data working: never remove or rename
  a field, column, route, or event the spec does not decide.
- Edit and test only — never commit, never stage (no `git add` / `git rm` /
  `git mv`; delete with plain `rm`), never edit the plan or spec.
- Return changed paths, red and green gate output, any mismatch with the plan
  as `> Drift: <what and why>`, and any case the spec does not decide as
  `> Undecided: <case>` instead of picking a behaviour. Stop and report a
  blocker when you are no longer making progress — around five failed gate
  runs, or a long stretch without running the gate.

Small or tightly coupled plans may run inline under the same rules.

Fan in after the whole wave returns. First `git status --porcelain -uall`
must list only paths in the wave's `Files:`. Any other path → find the task
that made it: a file the plan missed (lockfile, registration, snapshot) is
drift — add it to that task's `Files:` with a `> Drift:` note; anything
else is reverted.

Then serially, in task order:

1. Check the tests guard the change: on each line of logic the task added
   or edited, make the small slip a real bug would — flip a comparison or
   condition, swap `and`/`or`, shift a boundary, return a different value —
   run the task's tests, see one fail, restore the line. Aim for the slip
   most likely to get past the tests; an edit to old code counts too. Still
   green → the tests are too weak; re-dispatch the task with the slip that
   got through, so it adds a test that catches it. Then re-run the gate and
   append `> Gate: <cmd> | exit <n> | <one-line result>` — for every run,
   failed ones too.
2. Skim the diff against the plan's Architecture constraints. A task
   changing a contract or persisted data gets this skim from a fresh
   read-only subagent instead.
3. Write drift notes under the task. A `> Undecided:` case, or drift that
   changes a decision, a contract, or a later task, or loosens an existing
   assertion the task's `Tests:` does not name, is not drift: ask the user,
   record the answer in the spec as a new `D<n>` in prepare-plan's format
   (the one it supersedes struck) with its Test matrix row, then re-dispatch
   the task with it.
4. Commit the task's paths as the invariants say and tick it.

After the wave's commits, run the fast check before the next wave. Red →
fix it before the next wave, as a task `N.x` ahead of the Review gate
(`N` is the gate's number; `x` keeps counting up across waves and cycles).

A failed task does not void its siblings: commit the passing ones, then retry
once with the failure in the prompt, else record a `## Blockers` entry and
stop. Never open a wave over a blocker. Park partial work as a commit on the
ticket branch — `git add -- <paths> && git commit -m "wip(T<N>): blocked —
<reason>" -- <paths>` — and record its SHA in the entry.

## 4. Finish

1. **Data path:** for each field that is persisted or transmitted, open the
   real writer (insert / build / publish) and confirm the field is there.
   Confirm a test reaches the sink without mocking it, or flag it.
2. **Release checks** (§ Checks): run the fast check at HEAD, then start
   every release check together in the background and open the first review
   cycle at the same time — neither waits for the other. All green and the
   tree clean → tick Release checks. A failure the base branch already has is
   not yours: confirm it there, name it in the report, leave it. Light
   finish → skip the release checks, record it as § Checks says, and skip the
   review loop unless the user asked for a review: tick Release checks and
   the Review gate, each with `light finish` after its checkbox.
3. **Review loop** (max 3 cycles):
   - Append `cycle <c> | reviewed @ <HEAD> | base @ <base> | suite: fast
     <cmd> → <result> @ <SHA>; release <cmds> → <result, or running> @
     <SHA>` to `## Review`. When a running release check finishes, add its
     result to that line.
   - Launch a fresh Agent-tool subagent (`subagent_type: Plan` — read-only
     tools) told to read and follow
     `${CLAUDE_SKILL_DIR}/../review-build/SKILL.md`, to work only in the
     absolute venue path, with the spec and plan absolute paths, on the model
     that skill names. Under the cycle line, append its verdict lines, the
     model used, and each required finding as
     `R<c>.<n> | file:line | problem | fix` — the next cycle and retro-build
     read them there.
   - Before accepting a finding, reproduce its mechanism; fix the real cause
     and note a corrected mechanism on its `R` line. Cannot reproduce it →
     keep it open as `R<c>.<n> | disputed: <evidence>`; the next cycle's
     reviewer upholds or withdraws it. Never drop a finding silently.
   - `block` → stop and ask before fixing: data loss, security holes, and
     compat breaks usually need a decision first.
   - Required findings become tasks `N.x` (`Implements: R<c>.<n>`) inserted
     before the gate, same shape as other tasks; run them as waves
     (section 3), then the fast check; re-run a release check only when a
     fix touches what it covers, and name the earlier run that covers the
     rest; open a new cycle. Advisory findings go to
     `## Deferred suggestions` for the user.
   - `ship` → tick the Review gate once the release checks are green at
     HEAD or at an earlier SHA the cycle line says still covers it. A
     release check still running → wait for it; red → a task `N.x` and a
     new cycle. The gate has no commit: on resume, a ticked gate whose last
     verdict is `ship` at HEAD skips this loop.
   - Third non-ship verdict → `## Blockers`, escalate to the user.
4. Report, leading with the outcome. Claim only what a `> Gate:` line, a suite
   run, or a `## Review` entry shows, and name what was skipped. Give the
   venue path, branch, and plan folder, the `## E2E` steps to run with the
   user, and the `## Release` steps (results are recorded there after deploy). No PR or
   merge unless asked. Leave the worktree; remove it only after merge
   (`git worktree remove <path>`). After deploy: `/retro-build <plan>`.
5. **E2E:** as the user runs each step, record `<step> | <env> | pass / fail:
   <observed>` under `## E2E`. A fail is a finding: reproduce it, add task
   `N.x` before the gate, run it as a wave (section 3), untick the gate, and
   reopen the review loop.

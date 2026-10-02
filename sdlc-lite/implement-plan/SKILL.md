---
name: implement-plan
description: >-
  Implement a prepare-plan plan: run tasks as parallel subagent waves, verify
  every gate yourself, commit per task, then run review-build until ship. Use
  when the user says implement or execute the plan (sdlc-lite chain).
argument-hint: "[plan path]"
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

- The plan file is the state: checkboxes, `> Gate:`, `> Drift:`, `## Review`,
  `## Blockers`, `## E2E`. After a context compaction, re-read the plan and
  spec; resume from them, never from memory.
- Only you commit, tick checkboxes, and write the plan and spec. Subagents
  edit and test.
- Tick a task only after you re-ran its gate yourself. A subagent's "done" is
  a claim, not evidence.
- Commit explicit paths with `[T<N>]` in the message. Never `git add .` /
  `-A` — the venue holds copied `.env` files and WIP docs.
- Never weaken a gate or flip an assertion to go green.
- Run to the end. Stop for the user only on a blocker, behaviour the spec does
  not decide, drift that changes a decision, contract, or later task, a
  `block` verdict, or an action others can see (push, PR, deploy). Ask through
  `AskUserQuestion` with a recommended option. Don't end a turn announcing a
  next step you could take.

## 1. Load

Plan path in the input → use it. Otherwise look in `docs/plans/<TICKET-ID>/`, then
`docs/features/<TICKET-ID>/` (`<TICKET-ID>` from the branch, else ask once);
copies in both that differ → ask which is live. Read the plan and its spec.
The spec's `**Status:**` is not `plan-approved` → stop and say the plan is
unapproved. Raise gaps or concerns before touching code.

## 2. Venue

- Current branch contains `<TICKET-ID>` → work in this checkout.
- Otherwise reuse the ticket's worktree if `git worktree list` shows one, or
  create it (never two per ticket):

  ```bash
  git fetch origin
  git check-ignore -q .worktrees || echo ".worktrees/" >> "$(git rev-parse --git-common-dir)/info/exclude"
  git worktree add .worktrees/<TICKET-ID>-<slug> -b <TICKET-ID>-<slug> origin/HEAD
  # branch already exists: git worktree add .worktrees/<branch> <branch>
  ```

  `EnterWorktree` may enter that path, never create it.
  Copy `docs/plans/<TICKET-ID>` and `docs/specs/<TICKET-ID>` in **only if
  missing** there — an existing copy is live. Copy other untracked inputs the
  build needs (`.env`).

In either venue: install and run the baseline suite (red → stop). Then compare
with the spec's `Baseline:` SHA: if `git diff --stat <baseline> HEAD -- <the
plan's Files>` shows changes, re-check the plan's `file:line` references
against the current code and record differences as `> Drift:` before Task 1.

Report the venue path. On resume, reconcile with `git log`: ticked without a
`[T<N>]` commit → redo; commit without a tick → re-run the gate and tick. A
`wip(T<N>)` commit named in `## Blockers` → continue from it and mark the
entry resolved.

## 3. Run tasks in waves

Each round, the ready set is every unticked task where:

1. every `Depends on:` task is ticked (all tasks omit it → run sequentially;
   only some omit it → ask);
2. its `Files:` paths are disjoint from the rest of the wave (strip
   `:line-range` first);
3. its gate does not share mutable outputs with a wave-mate — port, build dir,
   test DB, coverage file. Repo-wide typecheck / lint reads siblings'
   half-written files: scope it to the task's paths or use a later wave;
4. it is not the Review gate.

Dispatch the whole ready set as parallel Agent-tool calls in one message; they
run in the background, so fan in only after every one has reported. Each prompt
contains: the absolute venue path (work only there), plan and spec paths, the
task number, `docs/quirks.md` if present, the gate command verbatim, and:
*edit and test only — never commit or edit the plan or spec; return changed
paths, red and green gate output, any mismatch with the plan as
`> Drift: <what and why>`, and any case the spec does not decide as
`> Undecided: <case>` instead of picking a behaviour; after ~5 failing gate
runs or ~30 tool calls without one, stop and report a blocker.* Small or
tightly coupled plans may run inline under the same rules.

Fan in serially, in task order, after the whole wave returns:

1. Re-run the gate. Skim the diff against the plan's Architecture constraints.
   A task changing a contract or persisted data gets this skim from a fresh
   read-only subagent instead.
2. Write drift notes under the task. A `> Undecided:` case, or drift that
   changes a decision, a contract, or a later task, or narrows an existing
   assertion, is not drift: ask the user, record the answer in the spec as a
   new `D<n>` (`supersedes D<m>` when it replaces one) with its Test matrix
   row, then continue.
3. Commit the task's paths with `[T<N>]`, tick it, append
   `> Gate: <cmd> | exit <n> | <one-line result>`. Tracked plan → include it
   in the commit.

A failed task does not void its siblings: commit the passing ones, then retry
or record a `## Blockers` entry and stop. Never open a wave over a blocker.
Park partial work as a commit on the ticket branch —
`git add <paths> && git commit -m "wip(T<N>): blocked — <reason>"` — and
record its SHA in the entry.

## 4. Finish

1. **Data path:** for each field that is persisted or transmitted, open the
   real writer (insert / build / publish) and confirm the field is there.
   Confirm a test reaches the sink without mocking it, or flag it.
2. Run the full suite; it must be green. Tree clean.
3. **Review loop** (max 3 cycles):
   - Append `cycle <c> | reviewed @ <HEAD> | base @ <base> | suite: <cmd> →
     <result>` to `## Review`.
   - Launch an Agent-tool subagent told to read and follow
     `${CLAUDE_SKILL_DIR}/../review-build/SKILL.md`, to work only in the
     absolute venue path, with the spec and plan absolute paths, on the model
     that skill names. Under the cycle line, append its verdict lines, the
     model used, and each required finding as
     `R<c>.<n> | file:line | problem | fix` — the next cycle and retro-build
     read them there.
   - Before accepting a finding, reproduce its mechanism; fix the real cause
     and note a corrected mechanism on its `R` line.
   - `block` → stop and ask before fixing: data loss, security holes, and
     compat breaks usually need a decision first.
   - Required findings become tasks `N.1`, `N.2`, … (`Implements: R<c>.<n>`)
     inserted before the gate, same shape as other tasks; run them through
     step 3, re-run the full suite, open a new cycle. Advisory findings go to
     `## Deferred suggestions` for the user.
   - Third non-ship verdict → `## Blockers`, escalate to the user.
4. Move (not copy) the spec to `docs/features/<TICKET-ID>/design.md` and the
   plan beside it, point the plan's `**Spec:**` line at the new path, and
   commit. One live copy remains; the commit is docs-only, so `ship` stands.
5. Report, leading with the outcome. Claim only what a `> Gate:` line, a suite
   run, or a `## Review` entry shows, and name what was skipped. Give the venue
   path and branch, the `## E2E` steps to run with the user, and the
   `## Release` steps (results are recorded there after deploy). No PR or
   merge unless asked. Leave the worktree; remove it only after merge
   (`git worktree remove <path>`).
6. **E2E:** as the user runs each step, record `<step> | <env> | pass / fail:
   <observed>` under `## E2E` and commit. A fail is a finding: reproduce it,
   add task `N.x` before the gate, run it through step 3, and reopen the
   review loop.

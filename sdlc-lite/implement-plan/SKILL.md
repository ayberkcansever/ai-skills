---
name: implement-plan
description: >-
  Implement a prepare-plan plan: run tasks as parallel subagent waves, verify
  every gate yourself, commit per task, then run review-build until ship. Use
  when the user says implement or execute the plan (sdlc-lite chain).
disable-model-invocation: true
---

# Implement Plan

You are the orchestrator. Subagents write code; you own verification, git,
and the plan file.

## Invariants

- The plan file is the state: checkboxes, `> Gate:`, `> Drift:`, `## Review`,
  `## Blockers`. After a context compaction, re-read this file and the plan;
  resume from the plan, never from memory.
- Only you commit, tick checkboxes, and write the plan. Subagents edit and test.
- Tick a task only after you re-ran its gate yourself. A subagent's "done" is
  a claim, not evidence.
- Commit explicit paths with `[T<N>]` in the message. Never `git add .` / `-A`.
- Blocked → stop and ask. Never weaken a gate or flip an assertion to go green.

## 1. Load

Plan path given → use it. Otherwise look in `docs/features/<TICKET-ID>/`, then
`docs/plans/<TICKET-ID>/` (`<TICKET-ID>` from the branch, else ask once). Read
the plan and its spec. Raise gaps or concerns before touching code.

## 2. Venue

- Current branch contains `<TICKET-ID>` → work in this checkout.
- Otherwise reuse the ticket's worktree if `git worktree list` shows one, or
  create it (never two per ticket):

  ```bash
  git check-ignore -q .worktrees || echo ".worktrees/" >> .gitignore
  git worktree add .worktrees/<TICKET-ID>-<slug> -b <TICKET-ID>-<slug> origin/HEAD
  # branch already exists: git worktree add .worktrees/<branch> <branch>
  ```

  Harness tools such as `EnterWorktree` may enter that path, never create it.
  Copy `docs/plans/<TICKET-ID>` and `docs/specs/<TICKET-ID>` in **only if
  missing** there — an existing copy is live. Copy other untracked inputs the
  build needs (`.env`). Run install + baseline tests; red baseline → stop.

Report the venue path. On resume, reconcile with `git log`: ticked without a
`[T<N>]` commit → redo; commit without a tick → re-run the gate and tick. A
stash OID in `## Blockers` → `git stash apply <OID>`, mark it resolved.

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

Dispatch the whole ready set in one message as parallel subagents. Each prompt
contains: the absolute venue path (work only there), plan and spec paths, the
task number, `docs/quirks.md` if present, the gate command verbatim, and:
*edit and test only — never commit or edit the plan; return changed paths, red
and green gate output, and any mismatch with the plan as `> Drift: <what and
why>`; after ~5 failing gate runs or ~30 tool calls without one, stop and
report a blocker.* Small or tightly coupled plans may run inline under the
same rules.

Fan in serially, in task order, after the whole wave returns:

1. Re-run the gate. Skim the diff against the plan's Architecture constraints.
   A task changing a contract or persisted data gets this skim from a fresh
   read-only subagent instead.
2. Write drift notes under the task. Drift that changes a decision, a
   contract, or a later task, or narrows an existing assertion, is not drift:
   stop and ask. If approved, record the new decision in the spec
   (`supersedes D<n>`) before continuing.
3. Commit the task's paths with `[T<N>]`, tick it, append
   `> Gate: <cmd> | exit <n> | <one-line result>`. Tracked plan → include it
   in the commit.

A failed task does not void its siblings: commit the passing ones, then retry
or record a `## Blockers` entry and stop. Never open a wave over a blocker.
Park partial work: `git stash push -u -m "T<N>-blocked" -- <paths>` and record
`git rev-parse stash@{0}` in the entry.

## 4. Finish

1. **Data path:** for each field that is persisted or transmitted, open the
   real writer (insert / build / publish) and confirm the field is there.
   Confirm a test reaches the sink without mocking it, or flag it.
2. Run the full suite; it must be green.
3. Copy the spec to `docs/features/<TICKET-ID>/design.md`, commit. Tree clean.
4. **Review loop** (max 3 cycles):
   - Append `cycle <c> | reviewed @ <HEAD> | base @ <base> | suite: <cmd> →
     <result>` to `## Review`.
   - Launch **review-build** (sibling folder `review-build/SKILL.md`) as a
     read-only subagent with the venue as working directory and the spec and
     plan absolute paths. Append its verdict lines and the model used.
   - Before accepting a finding, reproduce its mechanism; fix the real cause.
   - Required findings become tasks `N.1`, `N.2`, … inserted before the gate,
     same shape as other tasks; run them through step 3, re-run the full
     suite, open a new cycle. Advisory findings go to `## Deferred
     suggestions` for the user.
   - Third non-ship verdict → `## Blockers`, escalate to the user.
5. Copy the plan to `docs/features/<TICKET-ID>/`, commit.
6. Report what shipped, which checks passed, what was skipped, and the venue
   path and branch. List the `## E2E` steps to run with the user. No PR or
   merge unless asked. Leave the worktree; remove it only after merge
   (`git worktree remove <path>`).

# Execute Plan

## Overview

Load plan, review critically, execute all tasks step-by-step, run the
verifications the plan specifies, report when complete.

**Announce at start:** "I'm using the execute-plan skill to implement this plan."

## The Process

### Step 1: Load and Review Plan

1. Read the plan file (the one produced by **write-plan** or **interview-plan**).
   If the user did not say which file, search in this order:
   - `docs/features/<TICKET-ID>/` (tracked — prefer when present)
   - `docs/plans/<TICKET-ID>/` (gitignored WIP)
   - Legacy flat `docs/plans/*.md` or `docs/PLAN_*.md`
   Infer `<TICKET-ID>` from branch name or ask once.
2. **Resume check:** if the plan already has ticked checkboxes (`- [x]`), resume
   from the first unticked task — cross-check `git log` to confirm completed tasks
   were actually committed. The plan file's checkboxes are the source of truth for
   progress; TodoWrite is an optional in-session mirror only.
3. Review it critically — identify any questions, gaps, or concerns before
   touching code.
4. If concerns: raise them with the user before starting.
5. If no concerns: create a TodoWrite list (one todo per plan task) and proceed.

### Step 2: Confirm a safe workspace

- Never start implementation on `main` / `master` without explicit user consent.
- If on a protected branch, ask the user for the feature branch to use (or to
  confirm creating one). Reference the ticket key from the branch-naming rules
  when relevant.

### Step 3: Execute Tasks

**Plans with more than 3 tasks: run each task in a fresh subagent (default).**
This session acts as orchestrator. Inline execution (this session does the
tasks) only for plans with 3 or fewer tasks.

**Subagent contract — the prompt MUST contain all of:**

- the plan file path and the task number (the plan's **Architecture
  constraints** section is the subagent's conventions source — it sees nothing
  else);
- the spec file path from the plan header (so decisions are checkable, not
  hearsay);
- the repo quirks doc path when it exists (e.g. `docs/quirks.md`);
- the task's gate/verification command(s) verbatim;
- the 5-attempt cap and the instruction to report a blocker instead of
  grinding;
- the Plan Drift Protocol below (adapt, amend the step in place, add
  `> Drift:` note).

**Trust but verify:** subagents overclaim. Before ticking a task's checkbox,
the orchestrator **re-runs the task's gate command itself** and confirms the
expected output. A subagent "done" summary is a claim, not evidence.

For each task, in order:

1. Mark the todo `in_progress`.
2. Follow each step exactly — the plan has bite-sized steps (write failing test
   → run red → minimal impl → run green → commit). When reality contradicts a
   step, apply the Plan Drift Protocol — do not silently diverge and do not
   stop for trivial mismatches.
3. Run the verifications the step specifies. Do not skip them. Do not invent your
   own success criteria when the plan gave one.
4. When the plan step says "commit", stage explicit paths (or use the repo's
   commit helper) and commit — never `git add .` / `git add -A`. Keep the
   plan's `[T<N>]` task tag in the message.
5. **Per-task check (orchestrator, cheap):** re-run the gate command (see
   above), then skim the task's diff against the plan's Architecture
   constraints — layering respected, canonical helpers used, no hardcoded
   test-expected values. For a task that changes a **contract or persisted
   data** (API/event shape, schema, migration), have a fresh read-only
   subagent do this skim instead — the implementer must not check its own
   contract change. Findings → fix now, before the next task builds on it.
6. **Tick the task's checkboxes (`- [x]`) in the plan file** after the
   orchestrator's own gate run passes — the plan file tracks progress, not the
   session. Then mark the todo `completed`.

**Parallel dispatch (optional):** tasks whose `Depends on:` is satisfied AND
whose `Files:` sets are mutually disjoint may run as parallel subagents.
Anything else runs sequentially — same-file edits and commit races are not
worth the speedup. If the plan lacks `Depends on:` metadata, execute
sequentially.

### Plan Drift Protocol (plan meets reality)

Plan code was written before implementation; minor mismatch is normal, not a
blocker. When a step's code or command doesn't match reality (renamed symbol,
different signature, moved file, API mismatch):

1. **Adapt** — implement what the step *intends* against the real code.
2. **Amend the plan step in place** — update the code block/command to what
   was actually done, and append a one-line `> Drift: <what differed and why>`
   under the step. The plan file stays the as-built source of truth; a plan
   that lies about what was built is worse than no plan.
3. **Escalate instead** when the drift changes a spec **decision**, a
   contract, or invalidates a later task — that is a plan gap, not drift.
   Stop and ask (see below).

### Step 4: Complete

After all tasks are done and verified:

1. **Trace the data path to its real sink.** If the change persists or transmits a
   field, follow the value from its source to where it lands (DB write, queue
   publish, HTTP response). Open the actual writer — the repository insert /
   `build(...)` / publish payload — and confirm the new field is listed there, not
   just on the domain type. Green unit tests that mock the writer do NOT prove
   this; confirm at least one test reaches the sink without mocking it (in-memory
   DB round-trip or emitted-payload assertion), or flag it to the user. A field set
   on a domain object but missing from the writer ships schema defaults (`0`/`null`)
   to production — a silent failure that looks deployed.
2. Run the full relevant test/lint suite for the touched code.
3. **Run the review gate:** invoke **thermo-nuclear-code-quality-review** as a
   read-only subagent on the branch diff (it reads the spec + plan for
   conformance). Accepted findings append to the plan file as new task
   checkboxes; fix them via the same Step 3 loop, then have the reviewer
   re-check the changed areas. Repeat until the verdict is `ship`.
4. **As-built reconciliation:** re-read the plan file end to end — every
   checkbox ticked or explained, every `> Drift:` note in place, `## Blockers`
   entries resolved or still-open-and-flagged; mark superseded spec decisions
   (`supersedes D<n>`) in the spec file. Then promote spec + plan to
   `docs/features/<TICKET-ID>/` (spec → `design.md`) and commit, or ask the
   user if promotion is premature.
5. Report what was implemented, which verifications passed, and anything skipped.
6. Hand back to the user for manual testing. Do not open a PR or merge unless the
   user asks.

## When to Stop and Ask for Help

**STOP executing immediately when:**

- You hit a blocker (missing dependency, failing test you can't trivially fix,
  unclear instruction).
- The plan has a critical gap that prevents starting a task.
- You don't understand a step.
- **A verification fails 5 times (hard cap).** On the 5th failure: STOP, append
  the blocker to a `## Blockers` section at the end of the plan file (task number,
  what fails, what was tried), and escalate to the user. Never grind past the cap.

**Leave a clean tree when blocked.** Before escalating, park the partial work so
resume doesn't inherit a dirty workspace: `git stash push -m "T<N>-blocked"`
(default), or a wip commit on the feature branch if the user prefers history.
Record which was done in the `## Blockers` entry.

Ask for clarification rather than guessing.

## When to Revisit the Plan

Return to Step 1 (review) when:

- The user updates the plan based on your feedback.
- The fundamental approach needs rethinking.

Don't force through blockers — stop and ask.

## Subagent-driven execution (default for >3 tasks)

Subagent-per-task is the **default** for plans with more than 3 tasks (see
Step 3). Each task gets a fresh context, which prevents context rot on long
plans; the plan file (checkboxes + `## Blockers`) carries all state between
tasks, so any session — or a replacement session — can resume from it.

A subagent that hits the 5-attempt cap reports the blocker back; the
orchestrator writes it to the plan file and stops. Inline execution remains
fine for small plans (≤3 tasks) where one context comfortably holds the work.

## Remember

- Review the plan critically first.
- Follow plan steps exactly; don't skip verifications.
- Commit with explicit paths only (or the repo's commit helper); never `git add .`.
- Stop when blocked — don't guess.
- Never start implementation on main/master without explicit user consent.

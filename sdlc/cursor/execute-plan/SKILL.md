---
name: execute-plan
description: Use when you have a written implementation plan (from write-plan or interview-plan) and the user says "execute" / "implement it". Loads the plan, reviews it critically, executes each task step-by-step running the verifications the plan specifies, and stops to ask when blocked.
---

# Execute Plan

## Overview

Load plan, review critically, execute all tasks step-by-step, run the
verifications the plan specifies, report when complete.

**Announce at start:** "I'm using the execute-plan skill to implement this plan."

## The Process

### Step 1: Load and Review Plan

1. Read the plan file (the one produced by **write-plan** or **interview-plan**).
   If the user did not say which file, search in this order:
   - `docs/features/<JIRA-ID>/` (tracked — prefer when present)
   - `docs/superpowers/plans/<JIRA-ID>/` (gitignored WIP)
   - Legacy flat `docs/superpowers/plans/*.md` or `docs/PLAN_*.md`
   Infer `<JIRA-ID>` from branch name or ask once.
2. Review it critically — identify any questions, gaps, or concerns before
   touching code.
3. If concerns: raise them with the user before starting.
4. If no concerns: create a TodoWrite list (one todo per plan task) and proceed.

### Step 2: Confirm a safe workspace

- Never start implementation on `main` / `master` without explicit user consent.
- If on a protected branch, ask the user for the feature branch to use (or to
  confirm creating one). Reference the Jira key from the branch-naming rules
  when relevant.

### Step 3: Execute Tasks

For each task, in order:

1. Mark the todo `in_progress`.
2. Follow each step exactly — the plan has bite-sized steps (write failing test
   → run red → minimal impl → run green → commit).
3. Run the verifications the step specifies. Do not skip them. Do not invent your
   own success criteria when the plan gave one.
4. When the plan step says "commit", commit using the repo's committer script
   (`scripts/committer "<msg>" <paths...>`) — never `git add .`.
5. **Before marking a task completed:** if branch has `PRTD-*` / `AS-*` and
   `docs/features/<JIRA-ID>/` exists, run **maintain-feature-docs** (`.cursor/skills/maintain-feature-docs/SKILL.md`) — sync ticket docs in the same commit when the task changed decisions, contracts, deploy, or QA; skip for behavior-preserving fixes.
6. Mark the todo `completed` only after its verification passes.

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
2. Run the full relevant test/lint suite for the touched service(s).
3. Report what was implemented, which verifications passed, and anything skipped.
4. Hand back to the user for manual testing. Do not open a PR or merge unless the
   user asks.

## When to Stop and Ask for Help

**STOP executing immediately when:**

- You hit a blocker (missing dependency, failing test you can't trivially fix,
  unclear instruction).
- The plan has a critical gap that prevents starting a task.
- You don't understand a step.
- A verification fails repeatedly (more than ~2 focused attempts).

Ask for clarification rather than guessing.

## When to Revisit the Plan

Return to Step 1 (review) when:

- The user updates the plan based on your feedback.
- The fundamental approach needs rethinking.

Don't force through blockers — stop and ask.

## Optional: subagent-driven execution

This skill runs **inline** by default (this session executes the tasks). That is
enough for the normal "execute then test manually" loop, and it keeps full
context for review between tasks.

Cursor does support subagents (the Task tool), so you *can* dispatch a fresh
subagent per task for isolation or parallel attempts. Only do this when the user
explicitly asks for it, or when a task is large enough that a clean,
single-purpose context clearly helps. For most feature work, inline is simpler
and you do not need a separate subagent-driven-development skill.

## Remember

- Review the plan critically first.
- Follow plan steps exactly; don't skip verifications.
- Commit via the repo committer script, explicit paths only.
- Stop when blocked — don't guess.
- Never start implementation on main/master without explicit user consent.

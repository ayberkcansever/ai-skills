---
name: write-plan
description: Use when you have a spec or requirements for a multi-step task, before touching code. Write comprehensive, bite-sized, TDD-oriented implementation plans saved under docs/plans/<TICKET-ID>/ (gitignored WIP); promote stable docs to docs/features/<TICKET-ID>/ (tracked).
---

# Write Plan

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for the codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the write-plan skill to create the implementation plan."

**Context:** Plans are written in the user's checkout; they are *executed* in a per-ticket worktree that execute-plan opens via the `git-worktrees` skill. Keep every path in the plan repo-relative so it resolves in either place.

## Documentation layout (two tiers)

| Tier | Path | Git | Use |
|------|------|-----|-----|
| **Durable** | `docs/features/<TICKET-ID>/` | tracked | Design, implementation plans, test checklists — commit when stable |
| **WIP** | `docs/plans/<TICKET-ID>/` | gitignored | Agent scratch during write-plan / execute-plan |

Infer `<TICKET-ID>` from the branch name (e.g. `PROJ-123`) or ask once if unclear. If your project does not use ticket IDs, use a short kebab-case slug for the feature.

**Save new implementation plans to (WIP):**

`docs/plans/<TICKET-ID>/<scope>-implementation-plan.md`

**Overwrite guard:** if the target plan file already exists, do not rewrite it
silently — it may already be audited (interview-plan) or partially executed
(ticked checkboxes). Confirm with the user before replacing; prefer amending
the existing plan.

Examples:

- `docs/plans/PROJ-123/backend-implementation-plan.md`
- `docs/plans/PROJ-123/service-implementation-plan.md`

**Canonical filenames when promoting to `docs/features/<TICKET-ID>/`:**

- `README.md` — index, status, cross-repo links
- `design.md` — architecture + decisions
- `backend-implementation-plan.md` / `service-implementation-plan.md` / `frontend-implementation-plan.md`
- `test-checklist.html` — optional manual QA

**Promote when stable:** copy finalized docs from `docs/plans/<TICKET-ID>/` to `docs/features/<TICKET-ID>/` and commit (or ask the user). Follow your repo's own docs convention if it has one.

**While executing:** if your repo has a feature-docs sync flow (a skill or script that keeps `docs/features/<TICKET-ID>/` in sync with code), **execute-plan** runs it after each task — update those docs in the same commit when code changes decisions, contracts, deploy, or QA.

(User preferences for plan location override these defaults.)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Data-Path Trace (features that persist or transmit data)

If the feature adds or changes a field that must reach a **sink** — a DB write, a queue/topic publish, an HTTP response body, a file — map the full path from where the value originates to where it lands, and name the file at every hop:

```
source → contract/DTO → handler/consumer → use case → repository/publisher → sink
```

Two failure modes this prevents (both have shipped silently):

1. **Skipped hop.** A field set on a domain object but never forwarded by the repository's explicit `build(...)` / insert payload. The schema default (e.g. `0`/`null`) then fills the DB, so the deploy "succeeds" and every row is wrong. Walk the actual writer — grep the insert/`build`/publish call and confirm the new field is listed there, not just in the type.
2. **Mock-hidden hop.** A unit test that stubs the repository/publisher and asserts the argument passed *into* it. That proves wiring, not persistence. **The last hop to the sink must have at least one test that does NOT mock the writer** — a real in-memory DB round-trip, or a publisher contract assertion on the actual emitted payload.

Add an explicit task for the writer hop (repository/publisher) and an explicit task for the non-mocked round-trip test. Never let "use case sets the field" be the last word.

**Activation wiring.** A correct field is still inert if the switch that makes it live is missing — a new env var not wired into the running service, an index never created, a queue/topic subscription not added, a feature flag never enabled, infrastructure (IaC) not applied. If the change needs any such activation to take effect, add a task for it. Code that compiles and tests that pass do not prove the path is reachable in the deployed environment.

## Bite-Sized Task Granularity

**Each step is one verifiable action** — sized by its verification point
(test run, gate command, commit), not by wall-clock minutes:
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

**Detail budget:** test code, contract/DTO shapes, commands, and expected
results are exact and complete — they encode the requirements. Routine
implementation steps may use a focused diff sketch (anchor + changed lines)
instead of full file content; the Plan Drift Protocol absorbs mechanical
mismatch at execution time.

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use the execute-plan skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Plan code was written before implementation — when reality differs (API mismatch, wrong signature), adapt, update the step in place, and add a `> Drift:` note (see execute-plan's Plan Drift Protocol). The plan file is the as-built source of truth.

**Goal:** [One sentence describing what this builds]

**Spec:** [Path to the interview spec file, e.g. `docs/specs/<TICKET-ID>/spec.md`. No interview? Synthesize a minimal numbered spec (D1., D2., … from the given requirements, each with a `Check:` line) at that path first — tasks' `Implements:` and the Test matrix need stable decision IDs, and the review gate needs a spec to check conformance against.]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

## Architecture constraints (extracted from the repo — subagents see only this file)

- Layering: [e.g. handler → use case → repository; never call repositories from handlers]
- Error handling: [e.g. custom error classes from `src/errors/`, no bare throw]
- Naming/conventions: [e.g. project base classes, import conventions]
- Canonical helpers to reuse: [name them with paths — prevents bespoke duplicates]
- Test setup: [exact test command form, fixture/factory locations]

---
```

The **Architecture constraints** block is mandatory: parallel or fresh subagents executing tasks see only the plan file, so repo layering, DI style, error-handling patterns, and canonical helpers must live in it, not in the planner's memory. Extract them from the repo (AGENTS.md, existing neighbours of the touched files) while planning.

## Task Structure

````markdown
### Task N: [Component Name]

**Implements:** D3, D7 (decision numbers from the spec; "—" only for pure plumbing)
**Depends on:** Task 2 (or "none")

`Depends on:` and `Files:` are what execute-plan schedules on: each wave takes every task whose dependencies are ticked and whose `Files:` are disjoint from its wave-mates. Declare real dependencies only — a defensive `Depends on: Task 1` on an independent task silently serializes the plan. Both fields are load-bearing on every task; omitting them anywhere forces the whole plan sequential.

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_returns_total_of_line_items():
    result = order_total([LineItem(price=3, qty=2), LineItem(price=4, qty=1)])
    assert result == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_returns_total_of_line_items -v`
Expected: FAIL with "order_total not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def order_total(items):
    return sum(item.price * item.qty for item in items)
```

**Minimal means general — never hardcode the expected value** (`return 10` is a plan failure, not TDD). The implementation must compute the answer from its inputs; if a single hardcoded return would pass the test, the test is too weak — strengthen it (second case, different values) in the same step.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_returns_total_of_line_items -v`
Expected: PASS. Sanity-check the test has teeth: mentally (or actually) break the behavior — would the test fail? If not, fix the test before committing.

- [ ] **Step 5: Commit**

Run: `git add tests/path/test.py src/path/file.py && git commit -m "feat(scope): add specific feature [T<N>]"`
Expected: commit succeeds; pre-commit hooks pass (re-stage and amend if hooks modify files)

Every commit step in a plan MUST stage explicit paths (or use your repo's commit helper) — never `git add .` / `git add -A`. The `[T<N>]` suffix ties the commit to its plan task, closing the traceability chain `D<n> → Task <N> → commit [T<N>] → test`. When execute-plan dispatches the task to a subagent, the **orchestrator** runs this commit step after its own gate check — task subagents never commit.

A task's **gate** is the command in its final run-and-verify step (Step 4
above) plus that step's expected result — execute-plan re-runs exactly this
before ticking the task.
````

(The `pytest` / Python snippets above are illustrative; use whatever language and test runner the target repo uses.)

**Shared test fixtures: quote before you edit.** Show a fixture's current
contents, read from the file, in any step that changes one. "Remove X, leaving Y
intact" without evidence Y exists silently drops coverage for whatever else
reads that fixture.

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Test Matrix (carries the interview's coverage bar into the plan)

Every plan ends with a **Test matrix** section: a table mapping each spec decision and each accepted business edge scenario to the named test that proves it.

```markdown
## Test matrix

| Decision / scenario | Test name | Task |
|---|---|---|
| D3 concurrent update loses neither write | test_concurrent_update_merges_both | T4 |
| D7 deleted-mid-flow returns 409 | test_delete_mid_flow_conflict | T5 |
```

- A decision with no test row needs either a test or an explicit "not unit-testable because <reason>, verified by <manual step / functional test>".
- The plan's coverage task runs the repo's coverage command (e.g. `make test`, `npm test`) so "maximum coverage" is measured, not asserted.
- If the spec set a performance budget (interview checklist item 11), add a task that measures it (load script, timing assertion, or profiler run) — a budget nobody measures is decoration; if none downstream, mark it Non-goal in the spec instead.

## Final Task — Review Gate (mandatory)

Every plan's **last task** is the review gate. As a checkboxed task it survives
session resume, context summarization, and blocker exits — execute-plan's Step 4
prose alone does not. **execute-plan runs this task itself in its Step 4**
(after the data-path trace and full test suite) — it is never dispatched to a
task subagent. Append it after the coverage task, verbatim structure:

````markdown
### Task N: Review gate

**Implements:** — (quality gate)
**Depends on:** all previous tasks

- [ ] **Step 1: Spawn the reviewer** — read-only subagent running the
  **thermo-nuclear-code-quality-review** skill on the branch diff, model
  pinned per that skill's "Pinned review model" section (the single source of
  truth for the slug — never the session model, even when the session runs
  on auto).
- [ ] **Step 2: Record the verdict** — append the reviewer's 3-line rollup,
  the model used, the full-suite command + result, `reviewed @ <HEAD SHA>`
  and `base @ <base SHA>`, and the subagent link to this plan's `## Review`
  section.
- [ ] **Step 3: Loop until `Verdict: ship`** — accepted findings become
  remediation tasks inserted before this gate (template below); fix via
  execute-plan's Step 3 loop, re-run the full test suite, untick this gate's
  Steps 2–3 and re-run the reviewer on changed areas, add one `## Review`
  entry per cycle (max 3 cycles, then escalate).
````

**Remediation task template** — accepted review findings enter the plan as
full tasks, never bare checkboxes (bare checkboxes lose files, gates, and the
commit trace). **Insert them immediately before the review gate task**,
numbered `N.1`, `N.2`, … so the gate keeps its number and stays the last
task — the gate depends on the fixes, never the reverse (a fix that depends
on the gate deadlocks the plan):

````markdown
### Task N.k: Fix review finding <n>

**Implements:** review finding <n>, cycle <c> (from `## Review`)
**Depends on:** <the task that introduced the finding, or the previous remediation task>

**Files:**
- Modify: `<path from the finding>`

- [ ] **Step 1: Fix** — <the finding's fix, restated concretely>
- [ ] **Step 2: Verify** — re-run the owning task's gate command; expected PASS
- [ ] **Step 3: Commit** — `git add <paths> && git commit -m "fix(<scope>): <finding summary> [T<N.k>]"` (or your repo's commit helper)
````

## Remember
- Exact file paths always
- Every code step shows code — tests/contracts complete, routine implementation full or focused diff sketch
- Exact commands with expected output
- Commits stage explicit paths (or your repo's commit helper), tagged `[T<N>]` — never `git add .` / `git add -A`
- DRY, YAGNI, TDD, frequent commits

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Data-path completeness:** For every new/changed field that must reach a sink, can you point to (a) the task that adds it to the actual writer (repository insert / `build` / publish payload), and (b) a task with a test that reaches the sink WITHOUT mocking the writer? If either is missing, add it. A field present in the schema and use case but absent from the writer ships zeros/nulls to production.

**5. Test-matrix completeness:** Every spec decision and accepted edge scenario has a row in the Test matrix pointing at a named test in a task (or an explicit justified exception). Every test in the matrix exists in some task's code block.

**6. Dependency sanity:** Every task declares `Depends on:` and `Files:`; no cycles; no task uses a symbol defined in a task it doesn't (transitively) depend on. Tasks marked `none` with overlapping file sets are a lie — fix the declaration. Then read the graph as waves (each round = all tasks whose dependencies are met and whose files are disjoint): if it comes out as a single chain, check whether the dependencies are genuine or just the order you happened to write them in.

**7. Fake-green scan:** No implementation step's code block returns a hardcoded test-expected value or branches on test-specific input. If one does, generalize it and strengthen the test.

**8. Review-gate presence:** The plan's last task is the Review gate task (see "Final Task — Review Gate"). A plan without it is incomplete — add it.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, tell the user:

**"Plan complete and saved to `docs/plans/<TICKET-ID>/<scope>-implementation-plan.md`. Run `/execute-plan` (or say "execute") to implement it task-by-task. Promote to `docs/features/<TICKET-ID>/` when ready to commit."**

The next step in the workflow is the **execute-plan** skill. Do not start implementing here — writing the plan and executing it are separate phases so the user can review the plan first.

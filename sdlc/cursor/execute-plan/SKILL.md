---
name: execute-plan
description: Use when you have a written implementation plan (from write-plan or interview-plan) and the user says "execute" / "implement it". Loads the plan, reviews it critically, opens a per-ticket worktree so the user's checkout stays untouched, executes ready tasks in parallel waves, and stops to ask when blocked.
---

# Execute Plan

## Overview

Load plan, review critically, execute ready tasks in waves inside the
ticket worktree, run the verifications the plan specifies, report when complete.

**Announce at start:** "I'm using the execute-plan skill to implement this plan."

## The Process

### Step 1: Load and Review Plan

1. Read the plan file (the one produced by **write-plan** or **interview-plan**).
   Infer `<TICKET-ID>` from the plan path first, then an existing ticket
   worktree, then the current branch, then ask once — the user's checkout
   may be on `main` or another ticket.
   If the user did not say which file, search in this order:
   - already-listed worktree for this ticket (it is live — prefer it)
   - `docs/features/<TICKET-ID>/` (tracked)
   - `docs/plans/<TICKET-ID>/` (gitignored WIP)
   - Legacy flat `docs/plans/*.md` or `docs/PLAN_*.md`
   If both tracked and WIP copies exist in the same checkout, diff them; if
   they diverge, ask which is active — never silently prefer the promoted
   copy over newer WIP.
   Record the **absolute path of the user's checkout** — Step 2 copies from
   there only when the worktree does not already have the WIP docs.
2. Review it critically — identify any questions, gaps, or concerns before
   touching code. A plan whose header links a spec but carries no
   `**Audit:** clean` line may be un-audited interview output (generation
   interrupted before the Audit Pass) — confirm with the user before
   executing.
3. If concerns: raise them with the user before starting. Resume / stash /
   TodoWrite wait until Step 2 has the live plan.

### Step 2: Open the worktree (the execution venue)

**Execution always happens in a dedicated worktree for this `<TICKET-ID>`,
never in the user's checkout.** The user's checkout is theirs — it may be
dirty, on any branch, running a dev server; none of that concerns this run.
One worktree per ticket is also what lets several tickets execute in parallel
on the same repo.

Do not ask which branch to use, do not offer to switch branches, and do not
gate on the user's tree being clean — those questions belong to a workflow
that edits the checkout in place, which this one does not.

1. Run the **git-worktrees** skill with the ticket ID. It detects existing
   isolation, reuses or creates the worktree at `.worktrees/<branch>` (branch
   `<TICKET-ID>-<slug>`, per that skill's naming), and runs the project's
   install + baseline check. Consent is implied by `/execute-plan` — it does
   not re-ask. Already inside a linked worktree for this ticket → it reports
   and continues; nothing is created.
2. **Live plan.** The WIP tiers (`docs/plans/`, `docs/specs/`) are gitignored,
   so a *fresh* worktree does not contain the plan or spec. Run this **from
   inside the worktree**. Copy only when the destination does not already
   exist — a prior run's worktree copy is live; overwriting it from the origin
   checkout destroys ticks, drift notes, blockers, and review entries:

   ```bash
   for d in docs/plans/<TICKET-ID> docs/specs/<TICKET-ID>; do
     if [ -d "<origin-checkout>/$d" ] && [ ! -d "$d" ]; then
       mkdir -p "$(dirname "$d")" && cp -R "<origin-checkout>/$d" "$d"
     fi
   done
   ```

   The worktree copy (or the tracked `docs/features/<TICKET-ID>/` already on
   the branch) is now the live plan. Never write the origin checkout's copy
   mid-run.
3. **Resume on the live plan, in this worktree.** Reconcile checkboxes
   against `git log` here (this is the ticket branch): a ticked task with no
   `[T<N>]` commit → untick and redo; a `[T<N>]` commit with its task
   unticked → re-run the gate and tick without redoing. If `## Blockers`
   holds an unresolved stash OID, `git stash apply <OID>` **here**, then
   mark it resolved. Checkboxes are the source of truth; TodoWrite is a
   session mirror. Every task ticked but no `## Review` with `Verdict: ship`
   at current HEAD → jump to Step 4. Stale `reviewed @` SHA (code commits
   after it, docs-only excepted) → re-run Step 4.
4. Confirm the worktree is clean (`git status --porcelain` empty) aside from
   gitignored WIP docs. A reused worktree that is dirty is leftover work —
   reconcile against `## Blockers` before Task 1.
5. Create a TodoWrite list from the live plan and proceed.

Report the worktree path before Task 1 so the user knows where the work is
landing.

### Step 3: Execute Tasks

**Tasks run in waves: every task that legally can run now is dispatched as a
fresh subagent in one message; this session acts as orchestrator.** Waves are
the default, not an optimization to opt into — a plan whose tasks are
independent should finish in as many rounds as its dependency graph is deep,
not as many rounds as it has tasks. All subagents in a wave share the Step 2
worktree; isolation between them comes from the disjoint-files rule below, not
from separate directories.

Inline execution is fine for small or tightly coupled plans where one context
comfortably holds the work — task count alone is not the trigger.

#### Wave scheduling

Each round, build the **ready set** from the unticked tasks. A task joins the
current wave only if all four hold:

1. **`Depends on:` satisfied** — every named task is already ticked. A task
   declaring `none` is ready immediately. **If the plan omits `Depends on:`
   metadata entirely, treat every task as depending on the one before it** and
   run the whole plan sequentially — an absent declaration is unknown, not
   independent.
2. **`Files:` disjoint** from every other task already in this wave. Two
   subagents editing one file in one worktree overwrite each other; there is no
   merge step to catch it. A task with no `Files:` list does not join a wave
   with others — unknown overlap. (The Review gate has no `Files:` and is
   excluded by rule 4 anyway.)
3. **Gate commands do not contend** — tasks whose verifications write the same
   build output, coverage file, fixture database, or bind the same port go in
   different waves even when their `Files:` are disjoint. Shared *read-only*
   test infrastructure is fine.
4. **Not the Review gate task** — see the exception below.

Dispatch the whole ready set in a single message (parallel tool calls), then
wait for all of them before fanning in. Do not start the next wave early:
a later task's `Depends on:` is only satisfied once its predecessor is
**ticked**, which happens in fan-in after the orchestrator's own gate run.

Width is whatever the ready set allows — there is no cap beyond rules 2 and 3.
Record the wave composition in your progress notes (`wave 1: T1, T3, T5`) so a
resumed session can tell which tasks were in flight together.

**Subagent contract — the prompt MUST contain all of:**

- the **absolute worktree path** from Step 2, and the instruction to work
  only inside it — a subagent given a repo-relative path resolves it against
  the user's checkout and silently edits the wrong tree;
- the plan file path and the task number (the plan's **Architecture
  constraints** section is the subagent's conventions source — it sees nothing
  else);
- the spec file path from the plan header (so decisions are checkable, not
  hearsay);
- the repo quirks doc path when it exists (e.g. `docs/quirks.md`);
- the task's gate/verification command(s) verbatim;
- the 5-attempt cap and the instruction to report a blocker instead of
  grinding;
- the Plan Drift Protocol below. **Dispatched subagents return a proposed
  `> Drift:` line; they do not write the plan.** The orchestrator applies it
  at fan-in. Only inline execution amends the plan in place;
- **edit and test only — never commit, never write the plan file** (git index
  and plan md are orchestrator-owned state, sequential or parallel): skip the
  task's commit step and return changed paths, drift notes, and gate output
  instead — the orchestrator commits after its own checks (substeps 5–7).

**Trust but verify:** subagents overclaim. Before ticking a task's checkbox,
the orchestrator **re-runs the task's gate command itself** and confirms the
expected output. A subagent "done" summary is a claim, not evidence.

**Exception — the Review gate task:** the plan's final Review gate task is
NEVER dispatched to a task subagent (a task subagent cannot spawn the
read-only reviewer, and an implementer must not review its own diff). The
orchestrator executes it itself as Step 4.4 — after the data-path trace,
full-suite run, and spec promotion — and ticks its checkboxes when the
`## Review` entry records `Verdict: ship`. Skip over it in the Step 3 loop.

#### Per task

Substeps 1–3 are the task work — done by the subagent in dispatch mode, by
this session inline. Substeps 4–8 are **always the orchestrator's**, and in a
wave they run **serially, in task-number order, after every subagent in that
wave has returned**: the git index and the plan file are single-writer state
no matter how wide the wave was.

1. Mark the todo `in_progress`.
2. Follow each step exactly — the plan has bite-sized steps (write failing test
   → run red → minimal impl → run green → commit). When reality contradicts a
   step, apply the Plan Drift Protocol — do not silently diverge and do not
   stop for trivial mismatches.
3. Run the verifications the step specifies. Do not skip them. Do not invent your
   own success criteria when the plan gave one.
4. **Before the task's commit step, run substeps 5–6 first** — the commit
   must be able to include synced doc paths, and gate findings are cheaper to
   fix pre-commit than post-commit. Apply each returned `> Drift:` note to the
   plan here too; subagents never write it.
5. **Per-task check (orchestrator, cheap):** re-run the gate command (see
   above), then skim the task's diff against the plan's Architecture
   constraints — layering respected, canonical helpers used, no hardcoded
   test-expected values. For a task that changes a **contract or persisted
   data** (API/event shape, schema, migration), have a fresh read-only
   subagent do this skim instead — the implementer must not check its own
   contract change. Findings → fix now, before the next task builds on it.
6. **Feature-docs sync:** if your repo has a feature-docs sync flow and
   `docs/features/<TICKET-ID>/` exists, run it when the task changed
   decisions, contracts, deploy, or QA; skip for behavior-preserving fixes.
   The edited doc paths join the task's commit below.
7. When the plan step says "commit", commit code + synced doc paths together —
   stage explicit paths (or use the repo's commit helper); never `git add .`.
   Keep the plan's `[T<N>]` task tag in the message.
8. **Tick the task's checkboxes (`- [x]`) in the plan file** after the
   orchestrator's own gate run passes — the plan file tracks progress, not the
   session. If the plan file is tracked (`docs/features/` tier), tick before
   the step-7 commit and include the plan path in it — uncommitted checkbox
   edits dirty the tree and block the review gate. Then mark the todo
   `completed`.

**When one task in a wave fails.** A blocked or failing subagent does not void
its siblings. Fan in the tasks that passed their gate normally — commit and
tick each one — then handle the failure on its own terms: retry within the
5-attempt cap, or append a `## Blockers` entry and stop. Do not open the next
wave while a blocker is unresolved; its tasks may depend on the failed one, and
resuming from a half-applied wave is exactly what the plan file's checkboxes
exist to prevent.

### Plan Drift Protocol (plan meets reality)

Plan code was written before implementation; minor mismatch is normal, not a
blocker. When a step's code or command doesn't match reality (renamed symbol,
different signature, moved file, API mismatch):

1. **Adapt** — implement what the step *intends* against the real code.
2. **Record the drift** — dispatched: return `> Drift: <what differed and why>`
   to the orchestrator (do not write the plan). Inline: amend the step in place
   and append that line under it. The plan file stays the as-built source of
   truth; a plan that lies about what was built is worse than no plan.
3. **Escalate instead** when the drift changes a spec **decision**, a
   contract, invalidates a later task, or would make you delete, narrow, or
   invert an assertion covering behavior the plan never set out to change —
   that is a plan gap or a regression, not drift. Flipping such an assertion
   makes the test match the bug.
   Stop and ask (see below). If the user approves the change, update the spec
   **immediately** — record the new decision with `supersedes D<n>` and strike
   the old one — before continuing. The review gate reads the spec and must
   not judge the diff against a stale decision.

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
3. **Promote the spec before the review:** copy
   `docs/specs/<TICKET-ID>/spec.md` to
   `docs/features/<TICKET-ID>/design.md` (or merge into an existing one) and
   commit — in a multi-repo setup where another repo owns the shared
   `design.md`, merge there instead and record that path. The read-only
   reviewer may run from a context that cannot see gitignored WIP paths, and
   a missing spec caps its verdict at `fix-first`.
   Then confirm the tree is clean (`git status --porcelain` empty): the
   review's Step 0 refuses a dirty tree because uncommitted changes silently
   escape the diff.
4. **Run the review gate:** invoke **thermo-nuclear-code-quality-review** as a
   read-only subagent **with this worktree as its working directory** (or
   equivalent `git -C <worktree>`) on the branch diff, passing the spec and
   plan **absolute** paths in the prompt. A reviewer launched from the user's
   checkout diffs the wrong branch. A fresh-context reviewer cannot find
   gitignored WIP paths on its own. This step IS the plan's final Review gate
   task (write-plan appends one to every plan) — tick that task's checkboxes
   here; never run the review once in the Step 3 loop and again here.
   - **Pinned review model:** launch the reviewer subagent with the model
     named in thermo-nuclear-code-quality-review's "Pinned review model"
     section — that skill is the single source of truth for the slug; do not
     hardcode it here. Never the session's own model (auto included). If the
     slug is unavailable, stop and ask the user — never silently substitute.
   - **Record evidence:** append the reviewer's 3-line rollup (Verdict / Top
     issue / Net), the model used, the full-suite command + result at that
     SHA, `reviewed @ <HEAD SHA>` and `base @ <base SHA>`, and the subagent
     link to the plan file under a `## Review` section — one entry per review
     cycle. This is what the Step 2 resume check looks for; a review that
     leaves no `## Review` entry did not happen.
   - Accepted findings are inserted into the plan as structured remediation
     tasks **before the review gate task** (write-plan's remediation
     template); fix them via the same Step 3 loop, then have the reviewer
     re-check the changed areas. **Before
     accepting a `ship` verdict after any fix cycle, re-run the full test
     suite at the final HEAD** — targeted gate commands alone do not qualify.
     Repeat until the verdict is `ship` (the review skill caps cycles at 3,
     then escalates).
5. **As-built reconciliation:** re-read the plan file end to end — every
   checkbox ticked or explained, every `> Drift:` note in place, the
   `## Review` section's last entry reads `Verdict: ship` at the current HEAD,
   `## Blockers` entries resolved or still-open-and-flagged (`## Deferred
   suggestions` stays for the user — it does not block); confirm
   superseded spec decisions were marked at escalation time (Drift Protocol
   step 3). Then promote the plan to `docs/features/<TICKET-ID>/` (the spec
   was already promoted in substep 3) and commit, or ask the user if
   promotion is premature. Docs-only commits after the reviewed SHA that
   leave spec decisions unchanged do not invalidate the ship verdict.
6. Report what was implemented, which verifications passed, and anything
   skipped — and state the **worktree path and branch** so the user knows
   where to look.
7. Hand back to the user for manual testing. Do not open a PR or merge unless the
   user asks. **Leave the worktree in place**: it holds the branch, the
   as-built plan, and any still-gitignored WIP docs. Removing it is
   git-worktrees Step 4, run only after merge or on explicit user say-so.

## When to Stop and Ask for Help

**STOP executing immediately when:**

- You hit a blocker (missing dependency, failing test you can't trivially fix,
  unclear instruction).
- The plan has a critical gap that prevents starting a task.
- You don't understand a step.
- **A verification fails 5 times (hard cap).** On the 5th failure: STOP, append
  the blocker to a `## Blockers` section at the end of the plan file (task number,
  what fails, what was tried), and escalate to the user. Never grind past the cap.
- **A verification cannot be run as written** — it hangs, it is already red for
  unrelated reasons, or it needs access you cannot obtain. Append a `## Blockers`
  entry and ask what counts as ship evidence. Never tick the step, and never
  silently substitute a narrower command — a gate downgraded inside a `> Drift:`
  note is invisible to the reviewer.

**Leave a clean tree when blocked.** Before escalating, park the partial work so
resume doesn't inherit a dirty workspace:
`git stash push -u -m "T<N>-blocked" -- <task's changed paths>` (default) —
scoped to the task's paths so the user's unrelated work is never swept up,
`-u` so untracked new files are not left behind. Record the stash OID
(`git rev-parse stash@{0}`) in the `## Blockers` entry. Alternative: a wip
commit on the feature branch if the user prefers history — record which was
done.

Ask for clarification rather than guessing.

## When to Revisit the Plan

Return to Step 1 (review) when:

- The user updates the plan based on your feedback.
- The fundamental approach needs rethinking.

Don't force through blockers — stop and ask.

## Subagent-driven execution

Subagent-per-task, dispatched in **waves** of everything currently legal to
run, is the default (see Step 3). Each task gets a fresh context, which
prevents context rot on long plans; the plan file (checkboxes + `## Blockers`)
carries all state between tasks, so any session — or a replacement session —
can resume from it. Because state lives in the plan and the git index, both
single-writer and both orchestrator-owned, widening a wave never widens the
blast radius.

A subagent that hits the 5-attempt cap reports the blocker back; the
orchestrator writes it to the plan file and stops. Inline execution remains
fine for small or tightly coupled plans where one context comfortably holds
the work.

## Remember

- Review the plan critically first.
- Follow plan steps exactly; don't skip verifications.
- Commit with explicit paths only (or the repo's commit helper); never `git add .`.
- Stop when blocked — don't guess.
- Execute in the ticket's worktree, never in the user's checkout; the
  worktree's plan copy is the live one.
- Dispatch every legal task in a wave; fan in serially — commit, sync docs,
  tick, one task at a time.

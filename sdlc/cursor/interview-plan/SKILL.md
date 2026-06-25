---
name: interview-plan
description: >-
  Interview the user one question at a time to produce an ambiguity-free
  implementation plan across three lenses — business requirements,
  backward compatibility, and technical. The model actively investigates
  the codebase first (Discovery Phase), confronts the user with what it
  found, and pushes back with alternatives — it does not transcribe the
  user's words. After the interview, it hands the assembled spec to the
  write-plan skill, which authors the on-disk plan, then runs an Audit Pass
  over that file so it is self-contained for a fresh model or engineer.
  Use only when the user explicitly invokes "interview-plan" or asks to
  "interview me" / "stress-test the plan" about a plan or design.
disable-model-invocation: true
---

# Plan Interview

Produce **one ambiguity-free implementation plan** by interviewing the user
**one question at a time**. The crucial goal is a plan with **no ambiguity**
across three lenses:

- **Business requirements** — what problem, measurable success, who, why not
  simpler.
- **Backward compatibility** — every consumer, stored record, in-flight
  message, and deployed client affected, **enumerated from the actual code**.
- **Technical** — behaviour, edge cases, data model, contracts, testing,
  rollout.

The model **discovers and interrogates** — it reads the codebase first,
confronts the user with findings, and pushes back with alternatives. It does
**not** prepare a plan from the user's words alone. A plan built only from
what the user said is the failure mode this skill exists to prevent.

The single output is **one plan markdown file written to disk** — authored by
the **write-plan** skill from the spec this interview assembles, then verified
by this skill's Audit Pass. It must be complete enough that a fresh reader can
implement it without a follow-up question.

The goal is not "minimum questions to start coding". It is "no ambiguity
left that would bite us at code-review or in production".

## Rules

1. **One question per turn.** Never bundle multiple questions, sub-questions,
   or "while we're at it" asides. If you catch yourself writing "and also" —
   delete it and save it for the next turn. (Batch-confirmations of clearly
   out-of-scope checklist items are not bundled questions; see "Using the
   Checklist Efficiently".)
2. **Discover before asking.** Run the Discovery Phase first. Any fact that
   the codebase, configs, docs, or git history can answer — read it, don't
   ask. Questions of *intent* ("should we retry on this error?", "is partial
   success acceptable?", "do we need an audit log?") must always be asked;
   the code tells you what *is*, not what *should be*. Every question you do
   ask should be grounded in something you read, not in the user's framing.
3. **Walk the decision tree depth-first.** Resolve a decision's dependencies
   before moving to the next sibling. Don't jump branches until the current
   one is settled.
4. **Always recommend an answer.** For every question, propose your
   recommended answer with a one-sentence reason. The user can accept,
   override, or refine — this prevents stall.
5. **Tag the type of decision.** Mark each question as `[technical]`,
   `[product]`, `[compat]`, or `[scope]` so the user knows whether they're
   being asked an engineering tradeoff, a business call, a backward-compat
   call, or a boundary call.
6. **Maintain an internal decision log.** Track each agreed answer, explicit
   non-goal, and open risk so the final plan is complete and does not rely on
   memory alone. Also track the **consumer list** from Discovery so the
   backward-compat lens can be closed item by item.
7. **Push back with code-grounded findings, not just questions.** When you
   spot a simpler design, a non-obvious risk, a broken consumer, or a more
   idiomatic approach for *this* codebase — surface it on your own turn.
   Ground it in something you actually read. Use this format:

   ```
   Observation: <what you found in the code, with file:line>
   Alternative: <what you would consider instead>
   Tradeoff: <one sentence on what each side costs>
   ```

   Then ask if the user wants to switch. If you finish an interview without
   at least one code-grounded finding, you under-investigated — that is a
   failure, not a clean run.

## Question Format

```
Q[n] [type]: <single question>
Found: <the file:line / consumer / fact that prompted this, when applicable>
Recommendation: <your suggested answer>
Why: <one sentence>
```

## First Turn (always) — Calibration

Before anything, ask exactly one calibration question:

> "Before I start: are there domain quirks in this codebase or product
> that a generic reviewer would miss but matter here? (Examples: hidden
> idempotency contracts, filters that the UI applies but the backend
> doesn't, account/location/tenant scoping rules, timezone gotchas,
> protected code sections, in-flight migrations.)"

Treat the answer as permanent context for the rest of the interview —
every subsequent question, finding, and alternative is filtered through it.

## Discovery Phase (always — before Q1)

After calibration, **investigate before questioning**. Do not ask the user
anything answerable from the repo. Read, then report. Produce a short
**Findings** block in chat (not a wall of text):

1. **Touched code & patterns** — read the files the change will modify and
   the existing patterns there (naming, layering, error handling).
2. **Consumers** — grep the repo for every caller of any function, field,
   route, event, or contract the change touches. List them with `file:line`.
   This list *is* the backward-compat surface.
3. **Stored / in-flight data** — records written under the old contract,
   queued messages, deployed clients that will outlive the deploy.
4. **Existing tests** — tests that pin current behaviour and would break.

Output the Findings as a compact list, then drive questions from it. Each
finding is either:

- **silent-logged** (obvious, no decision needed), or
- **turned into a pointed question** (`Q[n]` with a `Found:` line).

Example of discovery-driven questioning (vs transcribing):

> Found: `tagLookup` read in `sales/.../x.ts:42` and `workflow/.../y.ts:88`;
> sales reads `legacyTarget`, which your change removes.
> Q3 [compat]: Break sales, migrate it, or dual-write `legacyTarget` for one
> release?
> Recommendation: dual-write one release, then drop — zero-downtime.
> Why: sales deploys on a different cadence; a hard break strands it.

If Discovery reveals the codebase contradicts a user assumption, surface it
immediately as an Observation/Alternative (Rule 7) before continuing.

## Three Lenses (must all be cleared)

The interview cannot stop until **each lens** is fully resolved:

- **Business requirements** — problem, measurable success, target user/role,
  why a simpler/cheaper option was rejected.
- **Backward compatibility** — **every** item on the Discovery consumer list
  is Decided / Non-goal / Open-accepted. This list is derived from grep, not
  from memory. This is the lens that bites hardest at review — never close it
  on "should be fine".
- **Technical** — the Coverage Checklist below.

## Coverage Checklist (the technical + business bar)

Before producing the plan, every item below must be **Decided**,
**Non-goal**, or **Open risk — accepted**. Never leave one as "didn't think
about it".

**Technical:**

1. Functional behaviour — happy path, expected inputs/outputs.
2. Edge cases and failure modes — empty/null/duplicate/concurrent inputs,
   partial failure, timeouts, retries that arrive after success.
3. Data model & schema changes — new fields, migrations, backfill, indexing,
   schema versioning. **Schema presence is not persistence:** for each new
   field, confirm the actual writer (repository insert / `build` / publish
   payload, not just the domain type) carries it, and that a test reads it back
   WITHOUT mocking the writer. A field with a schema default that the writer
   omits ships zeros/nulls and looks deployed — must-resolve, not obvious-skip.
4. API / event contract — request/response shape, status codes, versioning.
5. Backward compatibility — deployed clients, in-flight messages, stored
   records written under the old contract. (Cross-check the Discovery list.)
6. Idempotency & retries — idempotency key, dedup window.
7. Authn / authz — who can call this, required permissions, cross-tenant
   exposure prevention.
8. Observability — logs, metrics, traces, alerts; what a support engineer
   sees when this breaks at 3am.
9. Testing strategy — unit/integration/functional, coverage bar, must-test
   scenarios.
10. Rollout & rollback — feature flag, staged release, kill switch, order of
    operations across services, revert without data loss. **Activation:** what
    switch makes this take effect (env var wired to the Lambda, index created,
    SNS/SQS subscription added, flag enabled, CDK applied) — and what would
    leave it silently inert despite green tests.
11. Performance & scale — volume, latency budget, cost ceiling, burst load.
12. UX / accessibility / i18n — if user-facing.
13. Documentation — README, AGENTS.md, runbook, API spec, ADR/DECISIONS.md.
14. Dependencies — new libs/services, version pins, failure mode if down.

**Business / domain:**

15. Business intent — problem solved, measurable success, simpler
    alternatives considered and why rejected.
16. Domain-specific edge cases — idempotency-on-replay, scope-boundary
    (account vs location vs user vs tenant), time-window/filter-semantics
    mismatches between layers, state drift between subsystems, domain
    event-ordering races. Use the calibration answer to enumerate the
    specific quirks for *this* codebase.
17. User personas / roles — does behaviour differ by role, tier, app, or
    feature flag.
18. Operational impact — what support sees, runbook/alert needed, who's
    paged, manual recovery path.
19. Compliance / data handling — PII, retention, audit trail, cross-tenant
    exposure, regulatory scope.

## Using the Checklist Efficiently

The checklist is the **coverage bar**, not a literal question list. Asking
all 19 mechanically is a failure mode. For each item:

- **Obvious from code/context → silent log.** Record it silently and move
  on. Don't burn a turn confirming the obvious.
- **Clearly out of scope → batch-confirm.** Combine adjacent N/A items into
  one confirmation turn: *"Assuming internal-only — no UX, no i18n, no public
  API surface, no PII. Confirm?"* Not a Rule 1 violation; each item is binary.
- **Material and non-obvious → real `Q[n]` turn.** Only items where the
  answer is both non-obvious AND would materially change the plan.

This is the difference between a 12-turn high-signal interview and a 25-turn
mechanical one.

## Stopping Condition

Stop only when **all** are true:

- All three lenses are cleared (business, backward-compat, technical).
- Every Coverage Checklist item is Decided / Non-goal / Open-risk-accepted.
- Every consumer on the Discovery list is handled.
- No remaining question would, if answered differently, materially change
  the plan.
- You can produce the plan without the phrase "to be decided".

Or: the user says "enough" / "stop" / "good" / "let's go" / equivalent.

When stopping, run the Self-Critique Gate. Do **not** ask "are we done?" — judge
that yourself. But **before authoring anything**, ask the user one explicit
confirmation to proceed to write-plan (see "Output" Step 2). Only after the user
confirms do you invoke write-plan, then run the Audit Pass against the file it
produced.

## Self-Critique Gate (run silently before handing off to write-plan)

Anything that fails becomes one more turn, not a buried gap.

1. **Skipped questions** — what three questions did I almost ask but skip?
   If any skip-reason is weaker than "explicit non-goal" or "unambiguous from
   code", ask now.
2. **Most-likely review flag** — the single most likely thing a reviewer will
   flag that I have not raised? Raise it now.
3. **Soft answers** — was I answered with "yeah, sure" / "we'll see" /
   "probably"? Not decisions. Re-ask with a sharper recommendation, force a
   yes/no.
4. **Silent disagreement** — what would I have designed differently from
   scratch? Surfaced as an Observation/Alternative? If not, surface it now.
5. **Untouched consumer** — is any consumer from the Discovery list still
   unhandled? If so, that's an open backward-compat gap — ask.

## Output: Hand off to write-plan (the plan author)

This skill does **not** author the plan file itself. When the Stopping
Condition is met, it assembles the interview result into a **spec** and hands
that spec to the **write-plan** skill, which authors the comprehensive plan.
The division of labour:

- **interview-plan** owns: Discovery, the one-question interview, the three
  lenses, the Coverage Checklist, the Self-Critique Gate, and the **Audit Pass**.
- **write-plan** owns: turning the resolved spec into the on-disk plan file
  (file structure, bite-sized tasks, full-code steps, its own Self-Review,
  execution handoff).

### Step 1 — Assemble the spec (in chat, before invoking write-plan)

Compile everything resolved during the interview into a single spec block so
write-plan has zero ambiguity and needs no chat history:

- **Goal & business intent** — problem, measurable success, target user/role.
- **Decisions** — every resolved answer from the decision log, numbered.
- **Discovery findings** — touched code & patterns, the **consumer list**
  (`file:line`), stored/in-flight data, existing tests that pin behaviour.
- **Coverage Checklist status** — each item Decided / Non-goal / Open-accepted.
- **Non-goals, open risks (accepted), alternatives rejected.**
- **`Verify first:` items** — anything not actually inspected, with the
  verification command.

### Step 2 — Confirm, then invoke write-plan

**Ask the user to confirm before authoring the plan.** Post the assembled spec
summary and ask exactly one question:

> "Interview complete. Spec assembled above. Ready for me to write the plan with
> write-plan? (yes / keep interviewing / edit the spec first)"

Do not author anything until the user answers `yes` (or equivalent). If they
say keep interviewing or want spec edits, return to the interview loop and
re-run the Self-Critique Gate before asking again.

Once confirmed, read the **write-plan** skill (`write-plan/SKILL.md`, installed
at `~/.cursor/skills/write-plan/SKILL.md`)
and follow it as the source of truth for authoring the plan, passing the
assembled spec as its input. Follow its full workflow — scope check, file
structure, data-path trace, bite-sized tasks, no-placeholders rule, Self-Review.

**Suppress write-plan's Execution Handoff.** When write-plan runs as this
sub-step, do **not** emit its "Plan complete… run /execute-plan" message — the
plan is not done until interview-plan's Audit Pass clears. interview-plan owns
the single final handoff (Audit Pass "Report and gate" below).

Default WIP path (gitignored), inferred from the branch name (`PRTD-8154`,
`AS-1234`) or asked once:

`docs/superpowers/plans/<JIRA-ID>/<scope>-implementation-plan.md`

Promote stable docs to `docs/features/<JIRA-ID>/` (tracked). See **write-plan**
Documentation layout and your repo's `docs/features/README.md` for the convention.

### Step 3 — Run the Audit Pass

After write-plan saves the file, **do not** stop at write-plan's own handoff —
run the Audit Pass below against the written file before returning the path.
The Audit Pass is interview-plan's contribution on top of write-plan: it closes
every traceability gap (decision↔task, every consumer handled) with the user
still in the loop.

## Audit Pass (mandatory before returning the path)

The point is to close every gap *with the user still in the loop*. Run all
passes against the **written file** (re-read it; do not trust memory).

### Pass 1 — Matrix (traceability; the omission-catcher)

The syntactic scan catches bad phrasing; this catches **omissions** — the
thing that was never written. Build the Coverage Matrix in chat by mapping the
interview decision log + Discovery list against the **`### Task N`** headers in
the write-plan-authored file:

- Every **Decision** (from the interview decision log) maps to at least one
  **Task** (`### Task N`). A decision with no task = an unimplemented decision
  = gap.
- Every **Task** maps back to a Decision. A task with no decision = scope
  creep — flag it.
- Every **Coverage Checklist item** is Decided / Non-goal / Open-accepted.
- Every **consumer** from the Discovery list is handled by a task or
  explicitly marked unaffected.

Any orphan or unhandled consumer → surface as an open gap.

### Pass 2 — Fresh-eyes review

Re-read the plan **cold**, as a reviewer with zero chat history. Write the
**three questions** such a reviewer would ask first. Answer each in the plan,
or surface it as an open gap. This runs the user's own review step *before*
handoff — it is the pass that catches what they currently catch after.

### Pass 3 — Edge-hunt (per task)

For each task ask: **what breaks this task? what precondition is unstated?
what is the reverse/rollback operation?** Add an edge bullet to the task, or
surface as an open gap.

### Pass 4 — Trimmed syntactic scan

Re-read for these only (secondary, fast):

| Pattern | Means |
|---|---|
| `TODO`, `FIXME`, `XXX` | unresolved gap |
| `...` inside a code block (not prose) | hand-waved code |
| "as needed", "as appropriate", "handle this", "etc." | vague behaviour |
| acceptance check that is a sentence, not a runnable command | not verifiable |
| any field name / route / env var / column / function NOT backed by `file:line` or `Verify first:` | unevidenced assertion |

Fix anything fixable from existing context in one rewrite pass (replace
ellipses with a diff anchor or concrete sketch, sentences with commands,
guesses with `Verify first:`).

### Report and gate

Post a compact audit table in chat:

```
Audit pass on <path>:
  matrix         : <d> decisions, <s> steps, <o> orphan decisions, <c> creep steps, <u> unhandled consumers
  fresh-eyes     : 3 cold questions → <answered> answered, <open> open
  edge-hunt      : <tasks> tasks → <covered> with edge notes, <open> gaps
  syntactic scan : <n> hits → <fixed> fixed, <open> open
```

**If any open count > 0**, list each as `section <n>: <one-line gap>` and ask
the user to resolve. Do not return the path yet. Fold answers in (one rewrite
pass), re-run Passes 1–4. Repeat until every open count is 0.

**If all open counts are 0**, return:

> Plan ready at `<absolute path>`
> Audit: clean.
> Run `/execute-plan` (or say "execute") to implement task-by-task.

Do **not** paste the file contents back into chat — the file is the
deliverable; pasting wastes tokens and forks the source of truth.

## Anti-patterns

- **Transcribing instead of discovering.** Building the plan from the user's
  words without reading the codebase first. The Discovery Phase is mandatory.
- **Closing backward-compat from memory.** The consumer list must come from
  grep, and every entry must be handled. "Should be fine" is not a decision.
- Bundling real decisions into one turn (batch-confirming clearly-N/A items
  is allowed).
- Asking the user what the repo already answers (file paths, patterns,
  current behaviour, naming).
- Staying neutral instead of recommending — the user invoked this to be
  pushed, not surveyed.
- Finishing with zero code-grounded findings (Rule 7) — means passive
  interview.
- Treating "I can technically start coding" as the stopping bar. The bar is
  three lenses + checklist + handled consumers + Self-Critique Gate.
- Authoring the plan file directly instead of handing the assembled spec to
  the write-plan skill — write-plan owns the on-disk plan; this skill owns the
  interview, the spec, and the Audit Pass.
- Stopping at write-plan's own execution handoff and skipping this skill's
  Audit Pass — the Audit Pass is the omission-catcher and must run last.
- Asserting field names, routes, env vars, or library functions not actually
  seen — use `Verify first:` callouts.
- Returning the path before running the Audit Pass, or reporting "clean"
  without re-reading the written file.
- Reporting "audit clean" while a matrix orphan or unhandled consumer
  remains — the matrix pass is the omission-catcher; do not skip it.

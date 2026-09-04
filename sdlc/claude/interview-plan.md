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
   override, or refine — this prevents stall. When the user overrides a
   recommendation, record the decision as
   `D<n>. <decision> (overrides recommendation: <user's reason>)`. Pushback
   with no reason → ask once for the reason before recording; never silently
   flip. Code-grounded findings remain facts regardless of the user's framing.
5. **Tag the type of decision.** Mark each question as `[technical]`,
   `[product]`, `[compat]`, or `[scope]` so the user knows whether they're
   being asked an engineering tradeoff, a business call, a backward-compat
   call, or a boundary call.
6. **Write the decision log to disk as you go.** Append each agreed answer,
   explicit non-goal, and open risk to
   `docs/specs/<TICKET-ID>/spec.md` **at the moment it is decided**
   (create the file from the **Spec File Template** below on the first
   decision). Every behavioral decision carries a `Check:` line — a runnable
   command or named test that proves it (or `manual QA: <step>`). Cannot
   write one = decision too vague; sharpen it in the same turn before
   recording. Long interviews degrade chat recall; the file cannot forget. The
   end-of-interview spec assembly (Output Step 1) organizes this file — it
   does not reconstruct decisions from memory. Also track the **consumer
   list** from Discovery in the same file so the backward-compat lens can be
   closed item by item. **On every append, check the new decision against the
   existing decisions and non-goals** — if it contradicts one, surface both
   immediately and ask which wins; do not record two conflicting decisions.
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

## Resume Protocol (check before anything else)

If `docs/specs/<TICKET-ID>/spec.md` already exists for this branch,
this is a **resumed interview**, not a fresh one:

1. Read the spec file. Post a two-line status: `<d> decisions, <n> non-goals,
   <o> open items` and the list of open items.
2. Do **not** re-ask decided items. Resume from the first open item
   (open risks, unresolved checklist entries, unhandled consumers).
3. Re-run Discovery only for areas the spec marks unexplored or that the code
   has changed since (check `git log` from the spec's recorded Discovery
   baseline SHA).
4. If the user's new framing contradicts a recorded decision, surface the
   conflict (Rule 6) instead of silently overwriting.
5. If an implementation plan for this `<TICKET-ID>` also exists (WIP or
   promoted), the interview likely already completed — confirm intent before
   re-opening. New decisions then flow into the spec **and** a plan
   amendment; never leave the two contradicting.

Only when no spec file exists do you start at Calibration below.

## First Turn (always) — Calibration

**Resolve `<TICKET-ID>` first:**
`git branch --show-current | grep -oE '[A-Z]+-[0-9]+'` (adjust the pattern to
your tracker's key format). No match → ask for the ticket ID as part of the
calibration turn (administrative, not a decision — not a Rule 1 violation).
Rule 6 writes the spec to `docs/specs/<TICKET-ID>/spec.md` at the first
decision, so the ID must exist before Q1. If the project does not use ticket
IDs, use a short kebab-case slug for the feature.

**Then read the project quirks doc if one exists** (e.g. `docs/quirks.md` —
hard-learned domain gotchas) and list the entries relevant to this feature so
the user sees what is already covered. **Do not ask the user to enumerate
quirks here.** A cold recall question asked before Discovery has read anything
is the transcription failure this skill exists to prevent, and it asks for
negative knowledge — what would a generic reviewer miss? — which nobody can
produce on demand. Unknown quirks are surfaced as grounded candidates in
Discovery step 7 instead.

Treat the quirks doc entries as permanent context for the rest of the
interview — every subsequent question, finding, and alternative is filtered
through them, and step 7's accepted candidates join them.

## Discovery Phase (always — before Q1)

After calibration, **investigate before questioning**. Do not ask the user
anything answerable from the repo. Read, then report. Produce a short
**Findings** block in chat (not a wall of text):

1. **Touched code & patterns** — read the files the change will modify and
   the existing patterns there (naming, layering, error handling).
2. **Consumers** — grep for every caller of any function, field, route, event,
   or contract the change touches. List them with `file:line`. This list *is*
   the backward-compat surface. **For API/event/contract changes, the grep MUST
   span every repo/package that consumes the contract** — prefix each entry
   with the repo/package name. **When the change removes a field or stops writing
   one, include same-repo readers that *derive* behavior from it** — audit diffs,
   changed-field labels, conditional logs, cache keys. These break silently: the
   field is simply never there, so nothing throws.
3. **Stored / in-flight data** — records written under the old contract,
   queued messages, deployed clients that will outlive the deploy.
4. **Existing tests** — tests that pin current behaviour and would break.
5. **Product context** — read the repo README, `docs/features/` entries for
   adjacent tickets, and any product docs touching this domain. Business
   rules often live in docs, not code — a discovery that reads only code
   misses them.
6. **Business scenario hunt (generative, not confirmatory).** From the facts
   gathered above, **generate 5–10 candidate edge scenarios** the user has
   not mentioned, then present them as one batch for accept/reject (each is
   binary — this is not a Rule 1 violation). Mine these axes:
   - **actor × state × timing** — two users mutating the same entity; the
     entity deleted/archived mid-flow; a retry landing after success.
   - **abuse / misuse** — quota exhaustion, oversized input, repeated calls,
     a caller from the wrong tenant/role.
   - **money / counting** — rounding, currency, off-by-one on limits,
     double-counting on replay.
   - **lifecycle** — feature toggled off mid-operation, account downgraded,
     entity re-created with the same natural key.
   - **failed write** — the mutation rejects: does local state revert to the
     server value, or does the user keep seeing an unsaved value as if it
     were stored?
   Each accepted scenario becomes a Decision (how it must behave) — propose
   the expected outcome with the batch and confirm it before recording the
   D-number; acceptance without defined behavior is not a decision. Each
   accepted scenario later becomes a test in the plan's test matrix; each
   rejected one is recorded as a Non-goal. Presenting zero generated
   scenarios = under-investigation, same failure as finishing with zero
   code-grounded findings.
7. **Quirk sweep (generative, not confirmatory).** From the code read above,
   **generate the divergences a generic reviewer would miss** and present them
   as one batch for accept/reject. Never ask the user to recall quirks from
   memory — every candidate cites `file:line` and proposes a reading. Mine
   these axes:
   - **scope boundary** — account vs location vs user vs tenant enforced in
     one layer and not another.
   - **filter / time-window semantics** — two call sites reading the same
     source with different filters, boundaries, or timezone handling.
   - **hidden contracts** — idempotency keys, dedup windows, event ordering
     relied on but not enforced.
   - **protected sections** — code whose comments, tests, or git history warn
     against the obvious change; in-flight migrations.
   Format each as `Found: <file:line> — <the divergence> | quirk (intentional)
   or bug?` with a recommendation. Zero candidates is a valid outcome — say so
   explicitly rather than inventing one. Accepted candidates become permanent
   interview context; the ones that recur across tickets are the quirks doc's
   input (graph-retro Step 5 routes them there).

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
    switch makes this take effect (env var wired into the running service,
    index created, a queue/topic subscription added, feature flag enabled,
    infra (IaC) applied) — and what would leave it silently inert despite
    green tests.
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
    event-ordering races. Use the Discovery step 7 quirk sweep to enumerate
    the specific quirks for *this* codebase.
17. User personas / roles — does behaviour differ by role, tier, app, or
    feature flag.
18. Operational impact — what support sees, runbook/alert needed, who's
    paged, manual recovery path.
19. Compliance / data handling — PII, retention, audit trail, cross-tenant
    exposure, regulatory scope.
20. Scope & phasing — which parts are must-have vs nice-to-have; can the work
    split into phases or separate plans, and what ships first. Ask this
    **once, explicitly** — write-plan's Scope Check can only react; the split
    decision belongs in the interview.

## Using the Checklist Efficiently

The checklist is the **coverage bar**, not a literal question list. Asking
all 20 mechanically is a failure mode. For each item:

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

Or: the user signals completion — "enough" / "good" / "let's go" /
equivalent. "stop" / "pause" is cancellation, not completion: save the spec
state and exit without the Self-Critique Gate or the write-plan confirmation.

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
6. **Decision conflicts** — walk the decision log pairwise (and against the
   non-goals): does any later decision contradict, narrow, or silently
   supersede an earlier one? A late decision that reverses an early one must
   be marked `supersedes D<n>` in the spec, with the loser struck — never
   leave both standing.
7. **Deferred material check** — does `## Verify first` hold anything a plan
   task would be written around (API shape, field name, signature, path)?
   Verify it now; Verify-first is for environment-only checks.

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

### Step 1 — Assemble the spec (organize the spec file, before invoking write-plan)

Organize `docs/specs/<TICKET-ID>/spec.md` (built incrementally per
Rule 6) into the **Spec File Template** below, and post a summary in chat.
write-plan reads the spec **file** — zero ambiguity, no chat history needed.

#### Spec File Template (deterministic layout — write-plan depends on it)

```markdown
# <TICKET-ID> — <one-line goal>

## Goal & business intent
Problem, measurable success, target user/role.

## Decisions
D1. <one line>          (mark `supersedes D<n>` when a decision replaces one;
                         mark `(overrides recommendation: <reason>)` when the
                         user overrode the recommended answer)
    Check: <runnable command / named test / `manual QA: <step>`>
D2. ...

## Non-goals
NG1. <one line — includes rejected business scenarios from the scenario hunt>

## Consumers (from Discovery — the backward-compat surface)
| # | repo:file:line | contract touched | status (Decided Dn / Non-goal / Open-accepted) |

## Discovery findings
Baseline: <repo> @ <short SHA> (per repo — resume diffs `git log` from here).
Touched code & patterns, stored/in-flight data, tests that pin behaviour,
product-doc facts.

## Business edge scenarios
Accepted (each → a D-number) and rejected (each → an NG-number).

## Coverage Checklist status
1–20, each: Decided D<n> / Non-goal / Open-accepted.

## Open risks (accepted) / Alternatives rejected

## Verify first
Environment-only checks that cannot run from here (deployed config, external
service state), each with its command. Material unknowns a plan task would be
written around — API shapes, field names, signatures, paths — must be
verified during the interview, never deferred here.
```

**Spec lifecycle:** the spec is the contract for the whole chain — write-plan
links it in the plan header, execute-plan and the review skill check the diff
against its numbered decisions, graph-retro attributes failures against it.
When the plan is promoted to `docs/features/<TICKET-ID>/`, promote the spec
with it (as `design.md`, or merge into an existing `design.md`) so the
decision record survives the gitignored WIP directory.

### Step 2 — Confirm, then invoke write-plan

**Ask the user to confirm before authoring the plan.** Post the assembled spec
summary and ask exactly one question:

> "Interview complete. Spec assembled above. Ready for me to write the plan with
> write-plan? (yes / keep interviewing / edit the spec first)"

Do not author anything until the user answers `yes` (or equivalent). If they
say keep interviewing or want spec edits, return to the interview loop and
re-run the Self-Critique Gate before asking again.

Once confirmed, read the **write-plan** skill (`write-plan/SKILL.md`, wherever
your tool installs skills)
and follow it as the source of truth for authoring the plan, passing the
assembled spec as its input. Follow its full workflow — scope check, file
structure, data-path trace, bite-sized tasks, no-placeholders rule, Self-Review.

**Suppress write-plan's Execution Handoff.** When write-plan runs as this
sub-step, do **not** emit its "Plan complete… run /execute-plan" message — the
plan is not done until interview-plan's Audit Pass clears. interview-plan owns
the single final handoff (Audit Pass "Report and gate" below).

Default WIP path (gitignored), inferred from the branch name (e.g. `PROJ-123`)
or asked once:

`docs/plans/<TICKET-ID>/<scope>-implementation-plan.md`

Promote stable docs to `docs/features/<TICKET-ID>/` (tracked). See **write-plan**
Documentation layout and your repo's own docs convention.

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
  creep — flag it. **Exception:** tasks marked `Implements: —` (pure
  plumbing, the coverage run, and the mandatory final Review gate task from
  write-plan) — verify the justification in parentheses instead of flagging.
- Every **Coverage Checklist item** is Decided / Non-goal / Open-accepted.
- Every **consumer** from the Discovery list is handled by a task or
  explicitly marked unaffected.
- **No two Decisions conflict**, and no Task implements a Non-goal — the
  pairwise check from Self-Critique Gate item 6, re-run against the written
  file.

Any orphan, unhandled consumer, or unresolved conflict → surface as an open
gap.

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

**If all open counts are 0**: record `**Audit:** clean @ <date>` in the plan
file directly under its header, then return:

> Plan ready at `<absolute path>`
> Audit: clean.
> Run `/execute-plan` (or say "execute") to implement it.
> write-plan already ran — do not re-invoke it on this file.

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

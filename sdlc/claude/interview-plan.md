# Plan Interview

Produce **one ambiguity-free implementation plan** by interviewing the user
**one question at a time**. The crucial goal is a plan with **no ambiguity**
across three lenses:

- **Business requirements** — what problem, measurable success, who, why not simpler.
- **Backward compatibility** — every consumer, stored record, in-flight message, and deployed client affected, **enumerated from the actual code**.
- **Technical** — behaviour, edge cases, data model, contracts, testing, rollout.

The model **discovers and interrogates** — it reads the codebase first, confronts the user with findings, and pushes back with alternatives. It does **not** prepare a plan from the user's words alone. A plan built only from what the user said is the failure mode this skill exists to prevent.

The single output is a **compact plan markdown file** (always written to disk) — short enough that every line carries signal, complete enough that a fresh reader can implement it without a follow-up question. Compactness is how gaps stay visible; volume hides omissions.

The goal is not "minimum questions to start coding". It is "no ambiguity left that would bite us at code-review or in production".

## Rules

1. **One question per turn.** Never bundle multiple questions, sub-questions, or "while we're at it" asides. If you catch yourself writing "and also" — delete it and save it for the next turn. (Batch-confirmations of clearly out-of-scope checklist items are not bundled questions; see "Using the Checklist Efficiently".)
2. **Discover before asking.** Run the Discovery Phase first. Any fact that the codebase, configs, docs, or git history can answer — read it, don't ask. Questions of *intent* ("should we retry on this error?", "is partial success acceptable?", "do we need an audit log?") must always be asked; the code tells you what *is*, not what *should be*. Every question you do ask should be grounded in something you read, not in the user's framing.
3. **Walk the decision tree depth-first.** Resolve a decision's dependencies before moving to the next sibling. Don't jump branches until the current one is settled.
4. **Always recommend an answer.** For every question, propose your recommended answer with a one-sentence reason. The user can accept, override, or refine — this prevents stall.
5. **Tag the type of decision.** Mark each question as `[technical]`, `[product]`, `[compat]`, or `[scope]` so the user knows whether they're being asked an engineering tradeoff, a business call, a backward-compat call, or a boundary call.
6. **Write the decision log to disk as you go.** Append each agreed answer, explicit non-goal, and open risk to `docs/specs/<TICKET-ID>/spec.md` **at the moment it is decided** (create the file on the first decision). Long interviews degrade chat recall; the file cannot forget — the final plan is assembled from this file, not from memory. Also track the **consumer list** from Discovery in the same file so the backward-compat lens can be closed item by item. **On every append, check the new decision against the existing decisions and non-goals** — if it contradicts one, surface both immediately and ask which wins; do not record two conflicting decisions. A decision that replaces an earlier one is marked `supersedes D<n>`, with the loser struck.
7. **Push back with code-grounded findings, not just questions.** When you spot a simpler design, a non-obvious risk, a broken consumer, or a more idiomatic approach for *this* codebase — surface it on your own turn. Ground it in something you actually read. Use this format:

   ```
   Observation: <what you found in the code, with file:line>
   Alternative: <what you would consider instead>
   Tradeoff: <one sentence on what each side costs>
   ```

   Then ask if the user wants to switch. If you finish an interview without at least one code-grounded finding, you under-investigated — that is a failure, not a clean run.

## Question Format

```
Q[n] [type]: <single question>
Found: <the file:line / consumer / fact that prompted this, when applicable>
Recommendation: <your suggested answer>
Why: <one sentence>
```

## Resume Protocol (check before anything else)

If `docs/specs/<TICKET-ID>/spec.md` already exists for this branch, this is a **resumed interview**, not a fresh one:

1. Read the spec file. Post a two-line status: `<d> decisions, <n> non-goals, <o> open items` and the list of open items.
2. Do **not** re-ask decided items. Resume from the first open item (open risks, unresolved checklist entries, unhandled consumers).
3. Re-run Discovery only for areas the spec marks unexplored or that the code has changed since (check `git log` since the spec's last entry).
4. If the user's new framing contradicts a recorded decision, surface the conflict (Rule 6) instead of silently overwriting.

Only when no spec file exists do you start at Calibration below.

## First Turn (always) — Calibration

**First, read the project quirks doc if one exists** (e.g. `docs/quirks.md` — hard-learned domain gotchas). List the entries relevant to this feature so the user sees what is already covered. Then ask exactly one calibration question:

> "I loaded the quirks doc — entries […] look relevant here. Beyond those (or if there is no quirks doc): are there domain quirks for *this* change that a generic reviewer would miss? (Examples: hidden idempotency contracts, filters one layer applies and another doesn't, account/location/tenant scoping rules, timezone gotchas, protected code sections, in-flight migrations.)"

Treat quirks doc + answer as permanent context for the rest of the interview — every subsequent question, finding, and alternative is filtered through it.

## Discovery Phase (always — before Q1)

After calibration, **investigate before questioning**. Do not ask the user anything answerable from the repo. Read, then report. Produce a short **Findings** block in chat (not a wall of text):

1. **Touched code & patterns** — read the files the change will modify and the existing patterns there (naming, layering, error handling).
2. **Consumers** — grep for every caller of any function, field, route, event, or contract the change touches. List them with `file:line`. This list *is* the backward-compat surface. **For API/event/contract changes, the grep MUST span every repo/package that consumes the contract** — prefix each entry with the repo/package name.
3. **Stored / in-flight data** — records written under the old contract, queued messages, deployed clients that will outlive the deploy.
4. **Existing tests** — tests that pin current behaviour and would break.
5. **Product context** — read the repo README, `docs/features/` entries for adjacent tickets, and any product docs touching this domain. Business rules often live in docs, not code — a discovery that reads only code misses them.
6. **Business scenario hunt (generative, not confirmatory).** From the facts gathered above, **generate 5–10 candidate edge scenarios** the user has not mentioned, then present them as one batch for accept/reject (each is binary — this is not a Rule 1 violation). Mine these axes: **actor × state × timing** (two users mutating the same entity; the entity deleted/archived mid-flow; a retry landing after success), **abuse / misuse** (quota exhaustion, oversized input, repeated calls, a caller from the wrong tenant/role), **money / counting** (rounding, currency, off-by-one on limits, double-counting on replay), **lifecycle** (feature toggled off mid-operation, account downgraded, entity re-created with the same natural key). Each accepted scenario becomes a Decision (how it must behave) and later a test in the plan's test matrix; each rejected one is recorded as a Non-goal. Presenting zero generated scenarios = under-investigation, same failure as finishing with zero code-grounded findings.

Output the Findings as a compact list, then drive questions from it. Each finding is either:

- **silent-logged** (obvious, no decision needed), or
- **turned into a pointed question** (`Q[n]` with a `Found:` line).

Example of discovery-driven questioning (vs transcribing):

> Found: `tagLookup` read in `sales/.../x.ts:42` and `workflow/.../y.ts:88`; sales reads `legacyTarget`, which your change removes.
> Q3 [compat]: Break sales, migrate it, or dual-write `legacyTarget` for one release?
> Recommendation: dual-write one release, then drop — zero-downtime.
> Why: sales deploys on a different cadence; a hard break strands it.

If Discovery reveals the codebase contradicts a user assumption, surface it immediately as an Observation/Alternative (Rule 7) before continuing.

## Three Lenses (must all be cleared)

The interview cannot stop until **each lens** is fully resolved:

- **Business requirements** — problem, measurable success, target user/role, why a simpler/cheaper option was rejected.
- **Backward compatibility** — **every** item on the Discovery consumer list is Decided / Non-goal / Open-accepted. This list is derived from grep, not from memory. This is the lens that bites hardest at review — never close it on "should be fine".
- **Technical** — the Coverage Checklist below.

## Coverage Checklist (the technical + business bar)

Before producing the plan, every item below must be **Decided**, **Non-goal**, or **Open risk — accepted**. Never leave one as "didn't think about it".

**Technical:**

1. Functional behaviour — happy path, expected inputs/outputs.
2. Edge cases and failure modes — empty/null/duplicate/concurrent inputs, partial failure, timeouts, retries that arrive after success.
3. Data model & schema changes — new fields, migrations, backfill, indexing, schema versioning. **Schema presence is not persistence:** for each new field, confirm the actual writer (repository insert / `build` / publish payload, not just the domain type) carries it, and that a test reads it back WITHOUT mocking the writer. A field with a schema default that the writer omits ships zeros/nulls and looks deployed — must-resolve, not obvious-skip.
4. API / event contract — request/response shape, status codes, versioning.
5. Backward compatibility — deployed clients, in-flight messages, stored records written under the old contract. (Cross-check the Discovery list.)
6. Idempotency & retries — idempotency key, dedup window.
7. Authn / authz — who can call this, required permissions, cross-tenant exposure prevention.
8. Observability — logs, metrics, traces, alerts; what a support engineer sees when this breaks at 3am.
9. Testing strategy — unit/integration/functional, coverage bar, must-test scenarios.
10. Rollout & rollback — feature flag, staged release, kill switch, order of operations across services, revert without data loss. **Activation:** what switch makes this take effect (env var wired into the running service, index created, a queue/topic subscription added, feature flag enabled, infra (IaC) applied) — and what would leave it silently inert despite green tests.
11. Performance & scale — volume, latency budget, cost ceiling, burst load.
12. UX / accessibility / i18n — if user-facing.
13. Documentation — README, AGENTS.md, runbook, API spec, ADR/DECISIONS.md.
14. Dependencies — new libs/services, version pins, failure mode if down.

**Business / domain:**

15. Business intent — problem solved, measurable success, simpler alternatives considered and why rejected.
16. Domain-specific edge cases — idempotency-on-replay, scope-boundary (account vs location vs user vs tenant), time-window/filter-semantics mismatches between layers, state drift between subsystems, domain event-ordering races. Use the calibration answer to enumerate the specific quirks for *this* codebase.
17. User personas / roles — does behaviour differ by role, tier, app, or feature flag.
18. Operational impact — what support sees, runbook/alert needed, who's paged, manual recovery path.
19. Compliance / data handling — PII, retention, audit trail, cross-tenant exposure, regulatory scope.
20. Scope & phasing — which parts are must-have vs nice-to-have; can the work split into phases or separate plans, and what ships first. Ask this **once, explicitly** — the plan's Scope Check can only react; the split decision belongs in the interview.

## Using the Checklist Efficiently

The checklist is the **coverage bar**, not a literal question list. Asking all 20 mechanically is a failure mode. For each item:

- **Obvious from code/context → silent log.** Record it silently and move on. Don't burn a turn confirming the obvious.
- **Clearly out of scope → batch-confirm.** Combine adjacent N/A items into one confirmation turn: *"Assuming internal-only — no UX, no i18n, no public API surface, no PII. Confirm?"* Not a Rule 1 violation; each item is binary.
- **Material and non-obvious → real `Q[n]` turn.** Only items where the answer is both non-obvious AND would materially change the plan.

This is the difference between a 12-turn high-signal interview and a 25-turn mechanical one.

## Stopping Condition

Stop only when **all** are true:

- All three lenses are cleared (business, backward-compat, technical).
- Every Coverage Checklist item is Decided / Non-goal / Open-risk-accepted.
- Every consumer on the Discovery list is handled.
- No remaining question would, if answered differently, materially change the plan.
- You can produce the plan without the phrase "to be decided".

Or: the user says "enough" / "stop" / "good" / "let's go" / equivalent.

When stopping, run the Self-Critique Gate, then write the plan file and run the Audit Pass. Do **not** ask "are we done?" — judge it yourself.

## Self-Critique Gate (run silently before writing the plan)

Anything that fails becomes one more turn, not a buried gap.

1. **Skipped questions** — what three questions did I almost ask but skip? If any skip-reason is weaker than "explicit non-goal" or "unambiguous from code", ask now.
2. **Most-likely review flag** — the single most likely thing a reviewer will flag that I have not raised? Raise it now.
3. **Soft answers** — was I answered with "yeah, sure" / "we'll see" / "probably"? Not decisions. Re-ask with a sharper recommendation, force a yes/no.
4. **Silent disagreement** — what would I have designed differently from scratch? Surfaced as an Observation/Alternative? If not, surface it now.
5. **Untouched consumer** — is any consumer from the Discovery list still unhandled? If so, that's an open backward-compat gap — ask.
6. **Decision conflicts** — walk the decision log pairwise (and against the non-goals): does any later decision contradict, narrow, or silently supersede an earlier one? A late decision that reverses an early one must be marked `supersedes D<n>` in the spec, with the loser struck — never leave both standing.

## Output: Compact Plan (always written to disk)

When the Stopping Condition is met, write **one** markdown file. Default WIP path (gitignored):

`docs/plans/<TICKET-ID>/design.md` — compact interview output, or
`<scope>-implementation-plan.md` when the interview produced an execute-ready plan.

Infer `<TICKET-ID>` from branch name (e.g. `PROJ-123`) or ask once. Promote stable docs to `docs/features/<TICKET-ID>/` (tracked).

The plan file MUST be:

- **Compact.** Target ~100–300 lines. Every line carries signal. No glossary bloat, no re-explaining context the steps already make clear, no full file skeletons unless the change is a brand-new non-obvious file.
- **Self-contained enough for a fresh reader.** Inline file paths + per-step acceptance checks so a different model/engineer can implement without chat history.
- **Traceable.** Includes the Coverage Matrix (below) so every decision maps to a step and every consumer is accounted for.
- **Honest about unknowns.** Anything depending on a real prod schema, env value, or token you have not actually inspected is a `Verify first:` callout with a verification command — never invented.
- **Markdown only.** No HTML/JSON/YAML sidecars unless asked.

The plan's structure:

```
0. Header         — goal + execute-plan pointer
1. Context        — what + domain quirks + hard rules (bullets)
2. Decisions      — numbered, one line each
3. Coverage matrix — table: every checklist item + every consumer →
                     Decided / Non-goal / Open-accepted + which task/step
4. Steps          — checkbox tasks (`- [ ]`); File(s) | terse change | runnable acceptance check
5. Test matrix    — table: each decision / accepted edge scenario → named test → task
6. Non-goals / Open risks / Alternatives rejected — one-liners
```

### Steps section shape (borrow from write-plan)

- **Bite-sized granularity** — each `- [ ]` item is one 2-5 minute action, not a paragraph of intent.
- **Traceable tasks** — each task declares `Implements: D<n>` and `Depends on: Task <n> | none`; tasks with `none` and disjoint file sets are safe for parallel dispatch by execute-plan. Commit messages carry the `[T<N>]` tag.
- **No placeholders** — no `TBD` / "handle as appropriate". Every step names the file(s), the concrete change, and a runnable command with expected output.
- **TDD where testable** — prefer a failing-test step before implementation when the change has a unit/integration test surface.
- **Checkbox steps** — every executable action uses `- [ ]` so execute-plan can track and tick them off.
- **Explicit-path commits** — commit steps stage explicit paths (or use the repo's commit helper), never `git add .` / `git add -A`.

After the file is written, run the Audit Pass below before returning the path.

## Audit Pass (mandatory before returning the path)

Run all passes against the **written file** (re-read it; do not trust memory).

### Pass 1 — Matrix (traceability; the omission-catcher)

- Every **Decision** maps to at least one **Task**. A decision with no task = an unimplemented decision = gap.
- Every **Task** maps back to a Decision. A task with no decision = scope creep — flag it.
- Every **Coverage Checklist item** is Decided / Non-goal / Open-accepted.
- Every **consumer** from the Discovery list is handled by a task or explicitly marked unaffected.
- **No two Decisions conflict**, and no Task implements a Non-goal — the pairwise check from Self-Critique Gate item 6, re-run against the written file.

Any orphan, unhandled consumer, or unresolved conflict → surface as an open gap.

### Pass 2 — Fresh-eyes review

Re-read the plan **cold**, as a reviewer with zero chat history. Write the **three questions** such a reviewer would ask first. Answer each in the plan, or surface it as an open gap.

### Pass 3 — Edge-hunt (per task)

For each task ask: **what breaks this task? what precondition is unstated? what is the reverse/rollback operation?** Add an edge bullet to the task, or surface as an open gap.

### Pass 4 — Trimmed syntactic scan

| Pattern | Means |
|---|---|
| `TODO`, `FIXME`, `XXX` | unresolved gap |
| `...` inside a code block (not prose) | hand-waved code |
| "as needed", "as appropriate", "handle this", "etc." | vague behaviour |
| acceptance check that is a sentence, not a runnable command | not verifiable |
| any field name / route / env var / column / function NOT backed by `file:line` or `Verify first:` | unevidenced assertion |

Fix anything fixable from existing context in one rewrite pass.

### Report and gate

Post a compact audit table in chat:

```
Audit pass on <path>:
  matrix         : <d> decisions, <s> steps, <o> orphan decisions, <c> creep steps, <u> unhandled consumers
  fresh-eyes     : 3 cold questions → <answered> answered, <open> open
  edge-hunt      : <tasks> tasks → <covered> with edge notes, <open> gaps
  syntactic scan : <n> hits → <fixed> fixed, <open> open
  length         : <n> lines (target 100–300)
```

**If any open count > 0**, list each as `section <n>: <one-line gap>` and ask the user to resolve. Do not return the path yet. Fold answers in (one rewrite pass), re-run Passes 1–4. Repeat until every open count is 0.

**If all open counts are 0**, return:

> Plan ready at `<absolute path>`
> Audit: clean. Length: `<n>` lines.
> Run `/execute-plan` (or say "execute") to implement task-by-task.

Do **not** paste the file contents back into chat — the file is the deliverable; pasting wastes tokens and forks the source of truth.

## Anti-patterns

- **Transcribing instead of discovering.** Building the plan from the user's words without reading the codebase first. The Discovery Phase is mandatory.
- **Closing backward-compat from memory.** The consumer list must come from grep, and every entry must be handled. "Should be fine" is not a decision.
- Bundling real decisions into one turn (batch-confirming clearly-N/A items is allowed).
- Asking the user what the repo already answers (file paths, patterns, current behaviour, naming).
- Staying neutral instead of recommending — the user invoked this to be pushed, not surveyed.
- Finishing with zero code-grounded findings (Rule 7) — means passive interview.
- Treating "I can technically start coding" as the stopping bar. The bar is three lenses + checklist + handled consumers + Self-Critique Gate.
- Writing a long plan that re-explains context — volume hides omissions. Compact is the gap-detection mechanism, not a style preference.
- Asserting field names, routes, env vars, or library functions not actually seen — use `Verify first:` callouts.
- Returning the path before running the Audit Pass, or reporting "clean" without re-reading the written file.
- Reporting "audit clean" while a matrix orphan or unhandled consumer remains — the matrix pass is the omission-catcher; do not skip it.

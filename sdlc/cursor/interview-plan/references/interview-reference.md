# interview-plan — reference lists

Read once at the start of Discovery; re-read § Anti-patterns before the
Audit Pass. Procedure lives in `SKILL.md`; this file holds the lists it
points at: scenario axes, quirk axes, Coverage Checklist items, syntactic
scan patterns, anti-patterns, Spec File Template. The spec file on disk
mirrors the first three (`## Business edge scenarios`, `## Coverage Checklist
status`, its own layout), so after a context compaction the spec is the
working copy — re-read this file only when a list itself is needed again.

## Scenario axes (Discovery step 6 — business scenario hunt)

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

## Quirk axes (Discovery step 7 — quirk sweep)

- **scope boundary** — account vs location vs user vs tenant enforced in
  one layer and not another.
- **filter / time-window semantics** — two call sites reading the same
  source with different filters, boundaries, or timezone handling.
- **hidden contracts** — idempotency keys, dedup windows, event ordering
  relied on but not enforced.
- **protected sections** — code whose comments, tests, or git history warn
  against the obvious change; in-flight migrations.

## Coverage Checklist items (the technical + business bar)

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
8. Observability — derived, not brainstormed, from three sources:
   (a) **the path** — structured info events at entry and outcome, one per
   external call (status, latency), one per material branch (cache hit/miss,
   fallback taken, dual-write path), all carrying the correlation/request id
   so one transaction can be traced end to end in prod logs;
   (b) **the feature's metrics** — the measurable success from item 15,
   volume, success rate, latency histogram (11); bounded labels only;
   (c) **failures** — each accepted scenario, failure mode (2), dedup hit (6),
   authz denial (7), activation switch (10), pager (18): one signal each.
   Every signal names the 3am question it answers; no signal without a
   question, no per-step debug, never PII or tokens. Each becomes a `D<n>`
   whose `Check:` is a test asserting emission; use the repo's existing
   logger/metrics helper.
9. Testing strategy — unit/integration/functional, coverage bar, must-test
   scenarios. **E2E:** none / local / sandbox-dev / prod — which env, what it
   proves, who runs it. Prod e2e is read-only or synthetic-data unless the
   user approves mutation per run.
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

## Syntactic scan patterns (Audit Pass 4)

| Pattern | Means |
|---|---|
| `TODO`, `FIXME`, `XXX` | unresolved gap |
| `...` inside a code block (not prose) | hand-waved code |
| "as needed", "as appropriate", "handle this", "etc." | vague behaviour |
| acceptance check that is a sentence, not a runnable command | not verifiable |
| any field name / route / env var / column / function NOT backed by `file:line` or `Verify first:` | unevidenced assertion |

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

## Spec File Template (deterministic layout — write-plan depends on it)

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

---
name: prepare-plan
description: >-
  Turn an idea or ticket into a decision spec and a task plan, grounded in the
  codebase. Use when the user invokes prepare-plan or asks to plan or spec a
  change (sdlc-lite chain). Do not use to implement.
disable-model-invocation: true
---

# Prepare Plan

Produce two files, then stop for approval:

- `docs/specs/<TICKET-ID>/spec.md` — numbered decisions, each provable.
- `docs/plans/<TICKET-ID>/implementation-plan.md` — tasks implement-plan can schedule.

Both are gitignored WIP. `<TICKET-ID>` comes from the branch
(`git branch --show-current | grep -oE '[A-Z]+-[0-9]+'`); no match → ask once;
no tracker → short kebab-case slug.

## Invariants

- Read the code before asking. Never ask what the repo answers; ask about intent.
- Every question carries a recommendation and a one-line reason.
- "Probably", "sure", "we'll see" are not decisions — re-ask with a sharper
  recommendation and force a yes / no.
- Every decision has a `Check:` — runnable command, named test, or
  `manual QA: <step>`. Cannot write one → the decision is too vague; sharpen it.
- Backward compatibility is closed from grep results, never from memory.
- Every symbol, path, field, route, or env var the plan names cites `file:line`
  or was verified during planning. Never guess a name.
- Append decisions to `spec.md` the moment they are made. After a context
  compaction, re-read this file and `spec.md` — the files are the truth.
- No plan until the user approves the spec (short lane: one approval for
  both); no code until they approve the plan.

## 1. Discover

If `spec.md` exists, this is a resume: report decided / open items (Decisions,
Consumers, Coverage) and continue from the first open one. If only
`design.md` exists, carry its decisions in as `D<n>` with `Check:` lines.

Idea spans independent subsystems → propose the split and plan the first
piece only. Read, then post a compact Findings list:

- Files the change touches and their patterns (layering, errors, naming).
- Every consumer of each touched function, field, route, event, or contract,
  with `repo:file:line`, across every repo that consumes it. When a field is
  removed or no longer written, include readers that derive behaviour from it
  (audit diffs, logs, cache keys) — they break silently.
- Stored and in-flight data written under the old contract.
- Tests that pin current behaviour.
- README, adjacent `docs/features/` entries, and the `docs/quirks.md` entries
  relevant here — they filter every later question.

Findings must include at least one code-grounded pushback (simpler design,
broken consumer, hidden risk) with `file:line`, and a batch of edge scenarios
the user did not mention — concurrent mutation, entity deleted mid-flow, retry
after success, wrong tenant or role, limits / rounding / double counting,
feature toggled off mid-operation, failed write leaving stale local state —
each with a proposed behaviour to accept or reject. Zero findings means you
did not look.

Also post a quirk batch: divergences a generic reviewer would miss, as
`Found: file:line — <divergence> | quirk or bug? Recommend: <reading>`. Mine
scope enforced in one layer but not another (account / location / user /
tenant), two call sites reading one source with different filters, time
windows, or timezones, hidden contracts (idempotency keys, dedup, event
ordering), and code whose comments, tests, or history warn against the
obvious change. Zero candidates is valid — say so. Accepted quirks become
decisions or findings.

A real design choice → present 2–3 approaches with tradeoffs, recommended
first, before step 3.

## 2. Pick the lane

State the lane and why; the user may override.

- **short** — ≤2 files, ~50 lines, no new decision, no observable behaviour
  change, not money / auth / deploy / migration / alerting. Spec holds 1–3
  decisions and one batch-confirmed Coverage line; plan is one task plus the
  review gate.
- **standard** — default.
- **full** — changes a contract or persisted data, touches money or auth, or
  spans repos.

## 3. Resolve decisions

Ask related questions in small batches (≤4), dependencies first. Tag each
`[product]`, `[technical]`, `[compat]`, or `[scope]`:

```
Q3 [compat]: Break sales, migrate it, or dual-write `legacyTarget` for one release?
Found: sales/x.ts:42 reads `legacyTarget`, which this change removes.
Recommend: dual-write one release. Why: sales deploys on a different cadence.
```

- Override → record `(overrides recommendation: <user's reason>)`; no reason
  given → ask once.
- New decision contradicts an old one → surface both, ask, then mark the
  winner `supersedes D<n>` and strike the loser.
- Silent-log what the code makes obvious; batch-confirm clear non-goals.

Done when every consumer is Decided / Non-goal / Accepted risk, and each of
these is decided or a non-goal: business intent with measurable success and
why the simpler option lost; behaviour by role, tier, or flag; behaviour and
failure modes; data/schema (the actual writer carries each new field);
contract and compat; authz and tenant scope; idempotency and retries;
observability (each signal answers a real on-call question); operational
impact (what support sees, who is paged, manual recovery); PII, retention,
audit trail; performance and volume; UX, accessibility, i18n; new
dependencies and their failure mode; docs and runbook; rollout, activation
switch, rollback; testing including the E2E environment; scope and phasing
(ask once, explicitly). Track each in the spec's `## Coverage Checklist
status`. Nothing reads "TBD".

## 4. Write the files

Finish `spec.md` first, then post its summary — goal, decisions, non-goals,
accepted risks — and ask: *write the plan? (yes / keep going / edit spec)*.
Write the plan only on yes; otherwise return to step 3. Short lane skips this
stop — step 6 approves both files at once.

`spec.md` (same layout the v1 chain uses, so either reviewer can read it):

```markdown
# <TICKET-ID> — <one-line goal>
## Goal & business intent
## Decisions
D1. <one line>
    Check: <command / test / manual QA: step>
## Non-goals
NG1. <one line — rejected scenarios land here>
## Consumers
| # | repo:file:line | contract touched | Decided Dn / Non-goal / Accepted risk |
## Coverage Checklist status
<done-list item> | D<n> / NG<n> / accepted risk / open
## Discovery findings
Baseline: <repo> @ <short SHA>
## Open risks (accepted)
```

`implementation-plan.md`:

```markdown
# <TICKET-ID> — <goal> Implementation Plan
**Spec:** docs/specs/<TICKET-ID>/spec.md
**Lane:** short | standard | full — <reason>
**Architecture constraints:** layering, error handling, canonical helpers
(with paths), test command form — subagents see only this file.

### Task 1: <name>
**Implements:** D1, D3
**Depends on:** none
**Files:** `src/a.py`, `tests/test_a.py`
**Tests:** `test_x` — <input> → <expected>
**Contract:** <exact shape, when the task defines one>
**Gate:** `pytest tests/test_a.py -q` → passes
**Edges:** <what breaks it, unstated precondition, how to reverse it>
- [ ] done

### Task N: Review gate
**Implements:** — (quality gate)
**Depends on:** all previous tasks
- [ ] `Verdict: ship` at HEAD (implement-plan step 4)

## Test matrix
| Decision / scenario | Test | Task |
## E2E — run with the user after hand-back
<step> | <env> | pass / fail: <observed>
## Review
## Blockers
```

Task rules:

- `Depends on:` real dependencies only (`none` if independent) — a false
  dependency serializes the plan. `Files:` as paths — tasks sharing a file
  never run in parallel.
- No implementation code. Specify what the executor cannot guess: test cases
  (input → expected), exact contract / schema shapes, files, gate.
- Data that reaches a sink (DB, queue, HTTP response, file): one task changes
  the actual writer, and one test reaches the sink without mocking it.
  Activation (env var, flag, index, subscription, IaC) gets its own task.
- Every `D<n>` and accepted scenario has a Test matrix row, or a stated reason
  plus manual / E2E check. E2E steps run with the user after build, never by
  the agent.
- The last task is always the Review gate.

## 5. Check the written files

Re-read both files, do not trust memory: every decision maps to a task; every
task maps to a decision (or `—` with reason); every consumer is handled; no
task implements a non-goal; no placeholders; dependencies acyclic; no
Coverage item left `open`.

Then critique yourself; each miss becomes one more question, not a buried gap:
the question you almost asked but skipped for a reason weaker than "non-goal"
or "obvious from code"; the most likely review flag not yet raised; what you
would have designed differently from scratch, not yet surfaced as pushback.

**Standard and full lanes:** dispatch a read-only subagent given only the two
paths and ask for the three questions a reviewer would ask first. Answer each
in the plan or put it to the user.

## 6. Hand off

Post a short summary — lane, decision count, tasks, expected waves — and ask
for approval. On yes:

> Plan ready at `<absolute path>`. Run `/implement-plan`.

Do not paste the files into chat.

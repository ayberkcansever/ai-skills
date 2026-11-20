---
name: prepare-plan
description: >-
  Turn an idea or ticket into a decision spec and a task plan, grounded in the
  codebase. Use when the user invokes prepare-plan or asks to plan or spec a
  change (sdlc-lite chain). Do not use to implement.
argument-hint: "[plan name or TICKET-ID] [ticket link or idea]"
disable-model-invocation: true
---

# Prepare Plan

Interview the user into a spec of provable decisions, then write a plan
implement-plan can schedule. Stop for approval after each.

Input: $ARGUMENTS

**Reads:** the ticket and its linked docs, the code, `docs/quirks.md`, any
existing spec or plan for the ticket.
**Writes:** `<root>/docs/plans/<plan>/spec.md` and `plan.md`.

Later skills and resumed sessions see only these files, never this chat —
whatever they need goes in a file. `<plan>` is the plan's name: the name or
ticket key in the input, else the branch's ticket key
(`git branch --show-current | grep -oE '[A-Z]+-[0-9]+'`), else a short
kebab-case name you propose and the user confirms. Announce it once set:
`/implement-plan` later in this session uses it without arguments. `<root>`
is the main checkout,
`root="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"`,
even when this session runs in a linked worktree — every skill finds the
folder there and it outlives worktree removal. The folder is never
committed: unless already ignored, add `docs/plans/` to
`"$(git rev-parse --git-common-dir)/info/exclude"` (review-build refuses
untracked files; `.gitignore` is tracked).

## Invariants

- Read the ticket before asking anything, and the code before asking anything
  it could answer. Ask only what would change the plan.
- Ask through `AskUserQuestion`, written as *Asking* below: up to 4
  questions per call whose answers don't depend on each other — a question
  that reshapes the others goes alone. Free-form answers arrive through the
  built-in "Other".
- An unanswered question stays open. "Probably", "sure", "we'll see" are not
  decisions — re-ask with a sharper recommendation and force a yes / no.
- Every decision has a `Check:` — runnable command, named test, or
  `manual QA: <step>`. Every `[product]` decision also has an `Example:` with
  real values, an edge value included. Cannot write them → the decision is too
  vague; sharpen it.
- Backward compatibility is closed from grep results, never from memory. Every
  symbol, path, field, route, or env var the plan names cites `file:line` or
  was verified during planning. Never guess a name.
- Backward compatible by default. During a rolling deploy old and new code
  run side by side, and a rollback runs old code over data the new code
  wrote — both must keep working. Schema and contract changes are additive
  (expand), readers move next, removals (contract) ship later as a
  `## Release` follow-up. Anything else is a `[compat]` decision the user
  approves explicitly, marked `(breaking — approved <date>)`.
- Write to `spec.md` the moment something is decided, assumed, or asked.
  Decisions are append-only: a change is a new `D<n>` marked
  `supersedes D<m>`, with the old one struck.
- Approvals live in the spec's `**Status:**` line. No plan before
  `spec-approved` (short lane: one approval for both); no code before
  `plan-approved`. Changing a decision after an approval sets it back to
  `draft`.
- After a context compaction, re-read the spec and plan — the files are the
  truth.

## Asking

The user should get each question on the first read, and does not read the
code. The dialog can hide the chat, so a question stands on its own. The
code trail (tag, `file:line`, symbols) goes in the spec, never in the
dialog.

- **question** — two parts, in this order:
  1. The situation in plain words: what happens today, or would after the
     change, who it affects and when. Behaviour, not code: say "the sales
     service's old target field", not `legacyTarget`.
  2. One decision, asked directly, ending in `?`. Don't list the options in
     it; the buttons do that.
  Short enough to take in at one read, about 40 words. No file paths, no
  code symbols, no `[tag]`, no `D<n>` / `NG<n>` / `Q<n>` ids, no `|` or `→`
  as grammar. Explain a term the user may not share (dual-write, idempotent,
  expand/contract) or don't use it.
- **header** — the topic in plain words, ≤12 chars (`Old field`,
  `Double pay`). Never the tag.
- **options** — 2–4. Label: the outcome the user is picking, 2–5 words, not
  how it's built. Description: what happens and what it costs. Recommended
  first, labelled `(Recommended)`, and its description says why and what it
  assumes about the business. If you would be guessing, recommend none and
  say so.
- Before sending, reread each question as someone who skipped Discovery. If
  it takes a second read, cut code detail or split it in two.

A decision (step 5):

```
header: Old field
question: The sales service still uses the old target field, which this
  change removes, and sales deploys on its own schedule. What should
  happen to sales?
options:
  - Keep both fields one release (Recommended) — write old and new, drop
    the old one once sales has moved; nothing breaks mid-deploy
  - Update sales in this change — both repos must deploy together
  - Let sales break — only if sales is being retired
```

Not: `[compat] Found: sales/x.ts:42 reads legacyTarget, which this change
removes. Break sales, migrate it, or dual-write for one release?`

The other two shapes follow the same rules:

- An edge scenario (step 4): "Today, if someone presses Pay twice before the
  first request finishes, they are charged twice. What should happen
  instead?" — Charge once (Recommended) / Disable the button while paying /
  Out of scope for now.
- A quirk (step 4): "The dashboard counts orders by the day they were
  created, the CSV export by the day they were paid, so the totals differ.
  Is that on purpose?" — On purpose, keep both (Recommended) / Bug, fix it
  here / Bug, fix it later.

## 1. Start or resume

- `<root>/docs/plans/<plan>/spec.md` exists: resume.
  Report Status, open questions, and open Coverage items, and continue from the
  first. Run `git log <baseline>..HEAD -- <touched paths>` and refresh findings
  the code has outdated. A plan with ticked tasks is amended, never rewritten.
- Only a v1 `docs/specs/<plan>/design.md` → carry its decisions in as
  `D<n>` with `Check:` lines.
- Otherwise read the ticket (tracker CLI or connector when available) and its
  linked docs and designs.

## 2. Frame and pick the lane

Restate in a few lines: problem, who it affects, trigger, desired outcome, how
success is measured. Then, unless it is a plain fix, challenge it as
questions before reading deeply — discovery aimed at the wrong problem is
wasted: the intent the ticket leaves open, what happens if nothing is built,
the smallest version that still delivers the outcome, and the number,
measured where, that shows it worked. Independent subsystems → propose the
split and plan the first piece only.

State the lane and why, and record it in the spec's `**Lane:**`; the user
may override.

- **short** — small (about two files, ~50 lines), nothing for the user to
  decide beyond confirming the fix, behaviour changes only back to what the
  spec, docs, or tests already define, not money / auth / deploy / migration
  / alerting.
  Skips step 4 and the step-8 subagent. Spec holds 1–3 decisions and one
  batch-confirmed Coverage line; plan is one task plus Release checks and
  the review gate.
- **standard** — everything else.

A decision that later hits a short-lane exclusion moves the work to standard;
say so.

**Light finish** — only when the user asks (`light finish`, "skip heavy
checks"): the release checks and the review are skipped, unless the user
also asks for a review (implement-plan § Checks). Record
it on the `**Lane:**` line and in the plan's `**Checks:**`. A change that
hits a short-lane exclusion or a path the repo names as risky → ask once
whether to skip anyway. Never propose it yourself.

## 3. Discover

Read, then write the findings under the spec's `## Discovery findings`,
with `file:line` for each — later steps and reviewers need the trail:

- Files the change touches and their patterns (layering, errors, naming).
- Every reader and writer of each touched function, field, route, event,
  table, or contract, as `repo:file:line`, across every repo that uses it.
  Include readers that derive behaviour from a field (audit diffs, logs, cache
  keys) — they break silently — and writers off the main path (admin tools,
  imports, jobs, migrations, other services) — they bypass new rules.
- Stored and in-flight data written under the old contract, and existing
  records in each state the change touches.
- Domain: what each term the ticket uses means in the code (a term with two
  meanings is a question), and each touched entity's states, transitions,
  and the invariants the code enforces on them.
- Tests that pin current behaviour.
- How the repo checks a change: its test commands and when each runs (per
  task, fast, before release) from `AGENTS.md` / `CLAUDE.md` and the CI
  config, with run times where stated. They fill the plan's `**Checks:**`.
- README, adjacent `docs/features/` entries, and relevant `docs/quirks.md`
  entries — they filter every later question.

Then post a short summary in chat, in the same plain language as *Asking*
— no file paths or code names: what the change touches, as behaviour; who
else depends on it (services, teams, jobs, admin tools) and what would
happen to each; existing data it has to live with; and anything surprising.

Push back wherever the code supports it — simpler design, broken consumer,
hidden risk — saying what you found and why it matters, in those same plain
words; the `file:line` goes in the spec. If nothing warrants it, say so. A
real design choice → the realistic approaches with tradeoffs, recommended
first; settle it before step 4, because the scenarios depend on it.

## 4. Scenarios and quirks

For the chosen approach:

- **Edge scenarios** the user did not raise, generated from: actor (role,
  tenant, abuse — repeated, oversized, out-of-order calls); entity state
  (each Discovery state × each action the change adds); timing (concurrent
  change, retry after success, deleted mid-flow, replay); data (empty, one,
  max, duplicate, legacy-format record); money and counting (rounding,
  currency, limits off by one); time (timezone, DST, period boundaries);
  lifecycle (flag off mid-operation, downgrade, re-created with the same key);
  failure (partial write, dependency slow or down, stale local state after a
  rejected write). Then a pre-mortem: *it shipped, and a month later it
  caused an incident or a support ticket — what happened?* Keep those that
  really apply — a standard change usually has several; if you find few, say
  why. Each is its own question in the edge-scenario shape (*Asking*) —
  proposed behaviour (Recommended), the strongest alternative, out of scope.
  A behaviour → `D<n>`; out of scope → `NG<n>`.
- **Quirks** a generic reviewer would miss, each a divergence found at a
  `file:line` with your reading of it: scope enforced in one layer only, call
  sites reading one source with different filters or time windows, hidden
  contracts (idempotency, dedup, ordering), code whose comments or history
  warn against the obvious change. Zero is a valid answer. Record each with
  its `file:line` under `## Discovery findings`, then ask them in batches in
  the quirk shape (*Asking*). Accepted quirks become decisions or findings.

## 5. Resolve decisions

Ask in batches as the invariants describe, dependencies first, in the
decision shape (*Asking*). Tag each in the spec — `[product]`,
`[technical]`, `[compat]`, or `[scope]` — not in the question. After each
batch, play back what you recorded — each decision in one plain line with
its example — and ask what the answers opened up before moving on.

- Override → record `(overrides recommendation: <user's reason>)`; no reason
  given → ask once.
- A new decision contradicts an old one → surface both, ask, then supersede.
- A fact the code makes obvious needs no question; if it shapes behaviour, log
  it under `## Assumptions` so the user sees it at approval.
- Only someone else can answer (PM, another team, production config) → log it
  under `## Open questions` as `[external: <who>]`. Before approval it is
  answered, or becomes an accepted risk on an explicit yes.
- The user says "enough" with items open → name each one; it becomes an
  accepted risk only on an explicit yes.

Done when every Consumers row is Decided / Non-goal / Accepted risk,
`## Open questions` is empty, and each Coverage item is decided, a non-goal,
or an accepted risk — nothing reads "TBD". The list is the floor, not the
whole interview — raise whatever else this change needs:

1. Business intent: problem, measurable success, why the simpler option lost.
2. Behaviour by role, tier, or flag.
3. Behaviour and failure modes, accepted scenarios included.
4. Data and schema: the actual writer carries each new field; existing
   records backfilled or deliberately left as-is.
5. Contract and compatibility, every Consumers row: the mixed-version
   window, rollback over data the new code wrote, clients and messages that
   outlive the deploy.
6. Authz and tenant scope.
7. Idempotency and retries.
8. Observability: each signal answers a named on-call question.
9. Operations: what support sees, who is paged, manual recovery.
10. PII, retention, audit trail.
11. Performance, volume, cost: expected numbers and a budget; hot paths,
    queries and their indexes, migration locks and backfill time on the
    largest table.
12. UX, accessibility, i18n; user-visible text (errors, emails, empty states)
    decided verbatim or owned by a named person.
13. New dependencies and their failure mode.
14. Docs and runbook.
15. Rollout: activation switch and its default, deploy order, who sees it
    first, the signal that says it is broken, rollback, and when temporary
    code (dual-write, flag) is removed.
16. Testing, including the E2E environment.
17. Scope and phasing (ask once, explicitly), including what a stakeholder
    might assume is bundled — each confirmed as a non-goal.

## 6. Approve the spec

First critique the spec cold, from the file: the questions you almost
asked but skipped (a reason weaker than "non-goal" or "obvious from code" →
ask now), any soft answer still recorded as a decision, and the first thing
a reviewer or the on-call engineer would raise. Each becomes a question,
not a note.

Then post its summary — goal, decisions, non-goals, accepted risks, every
`## Assumptions` entry, and Coverage items closed as non-goals, in plain
language without file paths or code names — and ask:
*write the plan? (yes / keep going / edit spec)*. On yes set
`**Status:** spec-approved <date>`; otherwise return to step 5. Short lane
skips this stop — step 9 approves both files at once.

`spec.md` (the v1 layout plus Status, Assumptions, and Open questions, so
either chain's reviewer can read it):

```markdown
# <plan> — <one-line goal>
**Status:** draft | spec-approved <date> | plan-approved <date>
**Lane:** short | standard — <reason>
## Goal & business intent
## Decisions
D1 [<tag>]. <one line>
    Example: <input> → <outcome>          ([product] decisions)
    Check: <command / test / manual QA: step>
## Non-goals
NG1. <one line — rejected scenarios land here>
## Assumptions
A1. <inferred without asking> — <evidence>
## Open questions
Q<n> [<tag>] <question> — asked <date> [external: <who>]
## Consumers
| # | repo:file:line | reads / writes | contract touched | Decided Dn / Non-goal / Accepted risk |
## Coverage Checklist status
<n>. <item> | D<n> / NG<n> / accepted risk / open
## Discovery findings
Baseline: <repo> @ <short SHA>
## Open risks (accepted)
<risk> — accepted by <who> on <date>
```

## 7. Write the plan

```markdown
# <plan> — <goal> Implementation Plan
**Spec:** <root>/docs/plans/<plan>/spec.md (absolute)
**Architecture constraints:** layering, dependency injection, error handling,
canonical helpers (with paths), test command form — from the touched files'
neighbours; subagents see only this file and the spec.
**Checks:** (implement-plan § Checks; from the repo's instructions, else its defaults)
- task: <how one task's own tests run>
- fast: `<command>` (~<time>) — after each wave
- release: `<command>`; `<command>` — once, before push, started together
- light finish: no | yes (<date>, the user's words; review: skipped | asked for)

### Task 1: <name>
**Implements:** D1, D3
**Depends on:** none
**Files:** `src/a.py`, `tests/test_a.py`
**Tests:** `test_x` — <input> → <expected>; existing `test_y` changes: <old> → <new> (D<n>)
**Contract:** <exact shape, when the task defines one>
**Gate:** `pytest tests/test_a.py -q` → passes
**Edges:** <what breaks it, unstated precondition, how to reverse it>
- [ ] done

### Task N−1: Release checks
**Implements:** — (release gate)
**Depends on:** every code task
**Gate:** the `release:` checks → green (light finish: skipped, recorded)
**Covers:** <each slow or environment check a task needs, with its task number>
- [ ] done (implement-plan step 4, alongside the first review cycle)

### Task N: Review gate
**Implements:** — (quality gate)
**Depends on:** all previous tasks
- [ ] `Verdict: ship` at HEAD (implement-plan step 4)

## Test matrix
| Decision / scenario | Test | Task |
## E2E — run with the user after hand-back
<step> | <env> | pass / fail: <observed>
## Release
<step: deploy order, activation, signal to watch, rollback> | <owner> | <result>
Follow-ups: <ticket removing temporary code>
## Review
## Deferred suggestions
## Blockers
```

Task rules:

- `Depends on:` real dependencies only (`none` if independent) — a false
  dependency serializes the plan. `Files:` as paths — tasks sharing a file
  never run in parallel.
- No implementation code. Specify what the executor cannot guess: test cases
  (input → expected, the decision's `Example:` among them), existing tests a
  decision changes, exact contract / schema shapes, files, gate.
- Data that reaches a sink (DB, queue, HTTP response, file): one task changes
  the actual writer, and one test reaches the sink without mocking it.
  Activation (env var, flag, index, subscription, IaC) gets its own task.
- A migration or backfill is its own task: additive, safe to re-run, and
  deployable before the code that reads it. A performance budget gets a task
  or `Check:` that measures it.
- Every `D<n>` and accepted scenario has a Test matrix row, or a stated reason
  plus manual / E2E check. E2E steps run with the user after build, never by
  the agent.
- A task's `Gate:` is its task check: the tests that prove that task, in
  seconds to a minute. The whole suite, a database, an e2e stack, or any
  check the repo runs only before release never goes in a task `Gate:`;
  list it under Release checks `Covers:` with the task number, and give the
  task the narrow equivalent the repo offers (one spec, one test file).
- `## Release` comes from the rollout decisions; implement-plan reports it and
  never runs it.
- The last two tasks are always Release checks, then the Review gate.

## 8. Check the written files

Re-read both files, do not trust memory: every decision maps to a task and a
Test matrix row; every task maps to a decision (or `—` with reason); every
Consumers row is handled; no task implements a non-goal; no placeholders;
dependencies acyclic; no Coverage item left `open`; every `Gate:` is a task
check, and every release-only check sits under Release checks `Covers:`.

**Standard lane:** dispatch a fresh Agent-tool subagent
(`subagent_type: Plan` — read-only; never a fork of this conversation) given
only the two absolute paths. Ask
for the first questions an engineering reviewer, the product owner, and the
on-call engineer would raise, and for any decision whose `Example:` or
`Check:` it could not act on. Answer each in the files or put it to the user —
a fresh context catches what self-review misses.

## 9. Hand off

Post a short summary — lane, decision count (naming any added or superseded
since spec approval), tasks, expected waves, the release checks (or light
finish) — and ask for approval. Mention that `/view-plan <plan>` draws the
plan as pictures if they want to see it first; never run it unasked. On yes
set `**Status:** plan-approved <date>` and say:

> Plan `<plan>` ready at `<absolute folder path>`. Start a fresh session
> (`/clear`) and run `/implement-plan <plan>` — the files carry everything,
> and implementation runs best on a clean context.

Do not paste the files into chat.

# Thermo-Nuclear Code Quality Review

Review **current branch changes** through five lenses, in order.
Phases 0–3 are **review-first**: report findings, change code only if the user says "fix".
Phase 4 (docs) is **always applied** where a feature-docs flow exists.

**Maker/checker is unconditional for agent-authored diffs:** if any part of
the diff was written by an agent in any session (execute-plan or otherwise —
resumed agent-authored branches included), run the review as a **read-only
subagent** — the reviewer must not
share the implementer's context or be able to edit. Manual invocation on a
human-authored diff may run inline. Number every finding
`N | file:line | severity | problem | fix` so accepted findings can be appended
to the plan file as structured remediation tasks (see the review loop below).

**Pinned review model:** the reviewer subagent is launched with a **pinned
review model** — record your chosen slug here (pick the strongest
reasoning/thinking model available in your tool) — never inherit the
implementer session's model (auto included). If the slug is unavailable, stop
and ask the user; never silently substitute. **This section is the single
source of truth for the slug** — write-plan and execute-plan reference it
instead of hardcoding it; when the model changes, update it here only.

**Persist the verdict:** when a plan file exists for the branch, the
**invoking session (orchestrator)** appends the 3-line rollup, the model used,
the full-suite command + result, `reviewed @ <HEAD SHA>` and `base @ <base
SHA>` (both captured in Step 0), and the reviewer subagent link to the plan
under a `## Review` section (one entry per cycle) — the reviewer subagent is
read-only and cannot write the plan; on standalone inline runs the session
itself appends. A review that leaves no `## Review` entry did not happen —
execute-plan's resume check depends on it.
**A `ship` verdict is valid only for its recorded HEAD and base SHAs** — any
later commit invalidates it and requires a new cycle, except commits touching
only `docs/` paths that leave spec decisions unchanged (doc sync, plan/spec
promotion, `## Review` entries). A docs commit that edits decisions in
`spec.md` / `design.md` un-reviews the code; if the base branch moved,
re-review before merge.

**Step 0 — preconditions, then the diff.**

1. **Re-run guard:** if the plan's last `## Review` entry records
   `Verdict: ship` at the current HEAD (or differing from it only by
   docs-only commits that leave spec decisions unchanged), report "already
   reviewed at this commit" and stop — re-review only if the user explicitly
   forces it.
2. **Clean tree required:** `git status --porcelain` must be empty. Staged,
   unstaged, and untracked changes are invisible to `git diff <base>...HEAD`
   and would silently escape review. Dirty tree → stop and report; have the
   work committed first.
3. **Quirks doc:** read the project quirks doc when one exists (e.g.
   `docs/quirks.md` — hard-learned domain gotchas) — its entries feed
   Phase 0's semantic-drift sweep and Phase 3.
4. **Base & anchor:** resolve the base (`git symbolic-ref refs/remotes/origin/HEAD` or `main`/`master`), then capture `git rev-parse HEAD` and `git rev-parse <base>` — both go into the `## Review` entry.
5. Review `git diff <base>...HEAD`. Lenses below reconcile cleanly: **Phase 0 checks the diff does what was decided; Phase 1 removes what should not exist; Phase 2 restructures what remains.**

**Start the report with a 3-line rollup:**

```
Verdict: ship | fix-first | block
Top issue: <one line, or "none">
Net: -N lines possible | Lean already
```

**Verdict rules (deterministic):**

- `block` — any Phase 3 CRITICAL RISK, or a spec decision `missing` /
  unapproved `drift` in Phase 0.
- `fix-first` — no blockers, but accepted findings remain open (Phase 0
  semantic nits, Phase 1 cuts, Phase 2 structure). Also the cap when a
  ticket branch has no findable spec/plan (see Phase 0).
- `ship` — no open accepted findings AND the full test suite is green at the
  reviewed SHA, evidenced by the suite command + result recorded in the
  `## Review` entry (the orchestrator re-runs it after the last fix; a
  targeted gate command alone does not qualify). No recorded evidence →
  cap at `fix-first`.

**Review loop (when verdict is not `ship`):** accepted findings are inserted
into the plan **before the review gate task** as **structured remediation
tasks** (write-plan's remediation template — Files / fix / gate / commit,
never bare checkboxes); the executor
fixes them (execute-plan Step 3 loop); then **re-review only the changed
areas** — re-run Phase 0 for touched decisions plus the phases that produced
the findings, not the full battery — except the cycle that grants `ship`,
which re-runs the full Phase 0 decision sweep. Repeat until `ship`. Each
cycle re-states the rollup so drift across cycles is visible.
**Autonomous runs** (gate fired by execute-plan, no user in the loop):
required findings — Phase 3 CRITICAL RISKS and Phase 0 `missing`/`drift` —
are auto-accepted as remediation tasks; Phase 1–2 findings and SUGGESTIONS
are advisory: parked under the plan's `## Deferred suggestions` for the
user — never silently dropped, never silently fixed (`## Blockers` stays
reserved for non-ship state). **Cycle cap: 3** — a third non-`ship` verdict
stops the loop, records the open findings under `## Blockers`, and escalates
to the user.

## Phase 0 — Spec conformance (does the code do what was decided?)

Locate the ticket docs for this branch's `<TICKET-ID>`:
`docs/specs/<TICKET-ID>/spec.md` (or promoted
`docs/features/<TICKET-ID>/design.md`) and the implementation plan
(`docs/features/<TICKET-ID>/` or `docs/plans/<TICKET-ID>/`).

- Branch has a ticket key but no spec — or, for execute-plan-driven reviews,
  no plan — found in either tier → **finding, not a skip**: report
  `spec/plan missing for <TICKET-ID>` and cap the verdict at `fix-first`.
  Likely cause: the file sits unpromoted in the gitignored WIP tier
  (`docs/specs/` / `docs/plans/`) where a fresh reviewer (worktree, cloud,
  other machine) cannot see it — the orchestrator promotes it or passes
  explicit paths and re-runs.
- Branch has no ticket key and no docs → report "no spec/plan — conformance
  not checkable" and move to Phase 1.

- **Decision sweep** — for each numbered decision (`D<n>`) in the spec: point
  to the diff hunk(s) implementing it — unchanged pre-existing code that
  already satisfies a decision counts (cite `file:line`), as does a justified
  Test-matrix exception (manual QA / functional test) — or flag
  `not implemented`. Flag
  **semantic drift** — code that does something subtly different from the
  decision (wrong default, wrong scope, filter applied in one layer but not
  the other) — this is the highest-value finding this phase produces.
- **Edge-scenario sweep** — each accepted business edge scenario in the spec
  has its behavior implemented and its Test-matrix test present in the diff
  (or its recorded exception verified).
- **Non-goal sweep** — nothing in the diff implements a declared non-goal
  (scope creep caught at review, not in prod).
- **Drift-note sweep** — every `> Drift:` note in the plan is behavior-neutral
  with respect to the spec decisions; a drift that changed a decision without
  a spec update is a finding.

Output: one line per decision — `D<n> | implemented @ file:line | conforms /
drift: <one line> / missing`.

## Phase 1 — Simplify (YAGNI / over-engineering)

Hunt code to **delete**, not rearrange. One line per finding: `location: tag: what to cut → replacement`.

- `delete:` dead code, speculative feature, unused flexibility → nothing replaces it.
- `stdlib:` hand-rolled thing the standard library ships → name the function.
- `native:` dependency or code the platform already covers → name the feature (e.g. `<input type="date">`, `Intl`, `Array.flatMap`).
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller → inline until a second caller exists.
- `shrink:` same behavior, fewer lines → show the shorter form.

Never flag (these are not over-engineering): trust-boundary validation, error handling that prevents data loss, security, accessibility, and the one smoke/assert self-check a non-trivial change leaves behind.

End with `net: -N lines possible` — or `Lean already. Ship.` if there is nothing to cut.

## Phase 2 — Maintainability

- Do not push a file from under 700 lines to over 700 without strong reason — decompose first.
- No spaghetti: no ad-hoc conditionals bolted onto unrelated flows; extract policy / helper / module.
- Direct code over magic wrappers, casts, and pass-through abstractions.
- Reuse canonical helpers; keep logic in the right layer.
- Bias toward cleaner structure when behavior is unchanged.
- **Architecture conformance** — dependency direction respected (e.g. handler →
  use case → repository; domain never imports infrastructure); new code
  follows the established pattern of its neighbours, not a parallel bespoke
  one; check against the plan's **Architecture constraints** section when a
  plan exists. SOLID violations that hurt here: a class taking on a second
  responsibility, a new case bolted into a conditional where the codebase
  dispatches polymorphically, a concrete dependency instantiated where
  siblings inject it.

## Phase 3 — Merge safety

Risk tolerance: **low** — override by typing `Risk Tolerance: critical|high|medium|low` in the prompt. Generic checks, every repo:

- **Production safety** — crashes, data corruption, wrong data rendered, broken auth token.
- **Scale & resources** — N+1, blocking calls, memory or connection leaks.
- **Error handling** — swallowed exceptions, missing fallback, observability gaps.
- **Backward compatibility** — API signature change, model field removal, renamed contract or translation key, new required field on a deserialized payload.
- **Test coverage** — missing tests for complex or changed logic.
- **Security & tenant isolation** — no hardcoded credentials or tenant IDs, no PII or tokens in logs.

Stack specifics live in each repo's `AGENTS.md` / `CLAUDE.md` + rules — apply
them, do not duplicate here. Typical examples: frontend data-fetching cache keys
and invalidation, state-store selector identity, route/RBAC guards, i18n key
reuse; backend layering (handler → use case → repository), message/queue contract
integrity, resource-name limits; service-layer envelope parsing, module-level
caches, and any protected client/transport settings.

Output:

- **CRITICAL RISKS** (uncapped — report every one; if 7 exist, list 7) — would block merge, or "No critical risks found."
- **SUGGESTIONS** (0–3) — high-ROI, low-effort; no speculative items.
- **PRAISE** (0–3).

## Phase 4 — Feature docs sync (mandatory where present)

If the active repo has a feature-docs sync flow (a skill or script that keeps
`docs/features/<TICKET-ID>/` in sync with code), follow it. If absent → report
"no feature-docs flow" and stop. That flow owns `<TICKET-ID>` resolution,
drift detection, in-repo edits, and any cross-repo doc-ownership rule.

**Who edits:** a read-only reviewer subagent never edits docs — it reports doc
drift as `docs:` findings; the **orchestrator** (or the session, on inline
runs) applies the edits. Code is already committed at review time, so doc
edits land in a **separate `docs(<scope>)` commit** — never amend pushed
commits (docs-only commits do not invalidate the ship verdict, see "Persist
the verdict"). Standalone runs: commit only if the user explicitly asked.
Execute-plan-driven runs: the orchestrator commits the doc sync before the
final `ship` verdict is recorded — open doc drift is not `ship`.

Always emit:

```
Feature docs sync (<TICKET-ID>):
- Doc impact: yes | no
- Files updated: …
- Committed: yes | no
```

## Pre-commit

If the repo runs a feature-docs staged-check script, warn when code is staged without corresponding `docs/features/<TICKET-ID>/` updates (and respect any strict-mode flag that blocks the commit).

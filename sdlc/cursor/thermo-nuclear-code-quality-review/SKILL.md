---
name: thermo-nuclear-code-quality-review
description: >-
  Branch-diff review in five lenses — spec conformance, simplify (YAGNI /
  over-engineering), maintainability, merge safety, then mandatory
  feature-docs sync. Use /thermo-nuclear-code-quality-review after a dev
  session, before a PR. Repo-agnostic.
disable-model-invocation: true
---

# Thermo-Nuclear Code Quality Review

Review **current branch changes** through five lenses, in order.
Phases 0–3 are **review-first**: report findings, change code only if the user says "fix".
Phase 4 (docs) is **always applied** where a feature-docs flow exists.

**Maker/checker is unconditional for agent-authored diffs:** if any part of
the diff was written by an agent in the current session (execute-plan or
otherwise), run the review as a **read-only subagent** — the reviewer must not
share the implementer's context or be able to edit. Manual invocation on a
human-authored diff may run inline. Number every finding
`N | file:line | severity | problem | fix` so accepted findings can be appended
to the plan file as new task checkboxes.

**Step 0 — get the diff.** Resolve the base (`git symbolic-ref refs/remotes/origin/HEAD` or `main`/`master`), then review `git diff <base>...HEAD`. Lenses below reconcile cleanly: **Phase 0 checks the diff does what was decided; Phase 1 removes what should not exist; Phase 2 restructures what remains.**

**Start the report with a 3-line rollup:**

```
Verdict: ship | fix-first | block
Top issue: <one line, or "none">
Net: -N lines possible | Lean already
```

**Review loop (when verdict is not `ship`):** findings the user accepts are
appended to the plan file as new task checkboxes; the executor fixes them
(execute-plan Step 3 loop); then **re-review only the changed areas** —
re-run Phase 0 for touched decisions plus the phases that produced the
findings, not the full battery. Repeat until `ship`. Each cycle re-states the
rollup so drift across cycles is visible.

## Phase 0 — Spec conformance (does the code do what was decided?)

Locate the ticket docs for this branch's `<TICKET-ID>`:
`docs/specs/<TICKET-ID>/spec.md` (or promoted
`docs/features/<TICKET-ID>/design.md`) and the implementation plan
(`docs/features/<TICKET-ID>/` or `docs/plans/<TICKET-ID>/`). If
neither exists → report "no spec/plan — conformance not checkable" and move
to Phase 1.

- **Decision sweep** — for each numbered decision (`D<n>`) in the spec: point
  to the diff hunk(s) implementing it, or flag `not implemented`. Flag
  **semantic drift** — code that does something subtly different from the
  decision (wrong default, wrong scope, filter applied in one layer but not
  the other) — this is the highest-value finding this phase produces.
- **Edge-scenario sweep** — each accepted business edge scenario in the spec
  has its behavior implemented and its Test-matrix test present in the diff.
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

If the active repo has a feature-docs sync flow (a skill or script that keeps `docs/features/<TICKET-ID>/` in sync with code), follow it. If absent → report "no feature-docs flow" and stop. That flow owns `<TICKET-ID>` resolution, drift detection, in-repo edits, and any cross-repo doc-ownership rule. Commit only if the user explicitly asked.

Always emit:

```
Feature docs sync (<TICKET-ID>):
- Doc impact: yes | no
- Files updated: …
- Committed: yes | no
```

## Pre-commit

If the repo runs a feature-docs staged-check script, warn when code is staged without corresponding `docs/features/<TICKET-ID>/` updates (and respect any strict-mode flag that blocks the commit).

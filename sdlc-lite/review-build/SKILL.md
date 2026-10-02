---
name: review-build
description: >-
  Strict review of the branch diff against the ticket spec. implement-plan
  runs it as the review gate; invoke directly after a dev session or before a
  PR (sdlc-lite chain).
disable-model-invocation: true
---

# Review Build

## Setup

- **Independence:** any agent-written diff is reviewed by a read-only subagent
  with fresh context — it never shares the implementer's context and cannot
  edit. The same model is fine; independence comes from the context. No
  subagent facility → tell the user; run inline only on their say-so and
  record `reviewer: inline`.
- **Model:** the strongest reasoning model available. Pin one here if needed:
  `review-model:` (unset). A pinned model that cannot launch → ask, never
  substitute silently.
- **Clean tree:** `git status --porcelain` must be empty — uncommitted
  changes escape the diff. Dirty → stop and report.
- **Diff:** base = `git symbolic-ref refs/remotes/origin/HEAD` (else
  `main`); review `git diff <base>...HEAD`.
- **Context:** spec at `docs/specs/<TICKET-ID>/spec.md` or
  `docs/features/<TICKET-ID>/design.md`; plan likewise; `docs/quirks.md` and
  the repo's `AGENTS.md` / `CLAUDE.md` when present.
- **Re-run guard:** last `## Review` entry already says `Verdict: ship` at
  this HEAD (or only docs commits since, with no decision edits) → report
  "already reviewed" and stop.

## Lenses

1. **Conformance** — one line per decision:
   `D<n> | file:line | conforms / drift: <how> / missing / unverifiable: <why>`.
   Unchanged code that already satisfies a decision counts. Semantic drift —
   wrong default, wrong scope, a filter applied in one layer but not another —
   is the most valuable finding here. A decision whose test would still pass
   with the behaviour broken (hardcoded value, asserts only on mocks) is
   drift. Also: one `Goal | …` line — every decision can conform while the
   spec's goal and measurable success are still missed; each accepted edge
   scenario and quirk is implemented and tested; no non-goal is implemented;
   every `> Drift:` note is behaviour-neutral.
2. **Simplify** — dead code, hand-rolled stdlib or platform features,
   single-use abstractions, config nobody sets, longer-than-needed code. Never
   flag trust-boundary validation, error handling that prevents data loss,
   security, or accessibility.
3. **Merge safety** — crashes, data corruption, N+1 / leaks / blocking calls,
   swallowed errors, backward compatibility (signatures, removed fields, new
   required payload fields), missing tests for changed logic, authz and tenant
   isolation, secrets or PII in logs, observability decisions present.

If the repo has a feature-docs sync flow, report doc drift as `docs:`
findings; the orchestrator applies them in a separate docs commit.

## Output

```
Verdict: ship | fix-first | block
Top issue: <one line, or none>
Net: -N lines possible | lean
```

Then the conformance lines, then findings:
`N | file:line | required or advisory | problem | fix`.

- **required** — merge-safety risks and conformance `missing` / `drift`.
  Everything else is advisory.
- **block** — data loss or corruption, security hole, compat break, or a
  decision missing or drifted.
- **fix-first** — required findings remain; or the ticket branch has no
  findable spec; or any decision is `unverifiable`.
- **ship** — no required findings, and the current `## Review` line shows a
  green `suite:` at the HEAD you reviewed. Missing or mismatched → fix-first,
  and say which.

A `ship` verdict holds only at its reviewed SHA. Any later non-docs commit, or
a docs commit that edits decisions, reopens the review. Follow-up cycles
re-check the changed areas and touched decisions; the cycle that grants `ship`
re-runs the full conformance sweep.

The invoking session writes the `## Review` entry — the reviewer is read-only.
Standalone with no plan: report in chat.

---
name: review-build
description: >-
  Strict review of the branch diff against the ticket spec. implement-plan
  runs it as the review gate; invoke directly after a dev session or before a
  PR (sdlc-lite chain).
argument-hint: "[TICKET-ID]"
disable-model-invocation: true
---

# Review Build

Input: $ARGUMENTS

**Reads:** the branch diff, the spec, the plan (including earlier `## Review`
cycles), `docs/quirks.md`, the repo's `AGENTS.md` / `CLAUDE.md`.
**Writes:** nothing — it returns a verdict and findings; the invoking session
records them.

## Setup

- **Independence:** any agent-written diff is reviewed by an Agent-tool
  subagent with fresh context, told to read only — it never shares the
  implementer's context and never edits. The same model is fine; independence
  comes from the context. Invoked directly as `/review-build` → spawn that
  subagent yourself, pointing it at `${CLAUDE_SKILL_DIR}/SKILL.md`.
- **Model:** the Agent tool's strongest offered model, unless pinned here:
  `review-model:` (unset). A pinned model that cannot launch → ask, never
  substitute silently.
- **Clean tree:** `git status --porcelain` must be empty — uncommitted
  changes escape the diff. Dirty → stop and report.
- **Diff:** base = `git symbolic-ref refs/remotes/origin/HEAD` (else
  `main`); review `git diff <base>...HEAD`.
- **Context:** spec at `docs/specs/<TICKET-ID>/spec.md` or
  `docs/features/<TICKET-ID>/design.md`; plan likewise; `docs/quirks.md` and
  the repo's `AGENTS.md` / `CLAUDE.md` when present. Earlier `## Review`
  cycles: confirm each prior `R` finding's fix removed its cause.
- **Re-run guard:** last `## Review` entry already says `Verdict: ship` at
  this HEAD (or only docs commits since, with no decision edits) → report
  "already reviewed" and stop.
- **Standalone, no plan:** run the full suite yourself; it stands in for the
  `## Review` line in the `ship` rule. Report in chat.

## Lenses

1. **Conformance** — one line per decision:
   `D<n> | file:line | conforms / drift: <how> / missing / unverifiable: <why>`.
   Unchanged code that already satisfies a decision counts. Semantic drift —
   wrong default, wrong scope, a filter applied in one layer but not another —
   is the most valuable finding here. A decision whose test would still pass
   with the behaviour broken (hardcoded value, asserts only on mocks), or a
   `[product]` decision whose `Example:` no test exercises, is drift. Also:
   one `Goal | …` line — every decision can conform while the spec's goal and
   measurable success are still missed; each accepted edge scenario and quirk
   is implemented and tested; no non-goal is implemented; every `> Drift:`
   note is behaviour-neutral; each `## Assumptions` entry the code relies on
   still holds.
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
`R<c>.<n> | file:line | required or advisory | problem | fix`, where `<c>` is
the open `## Review` cycle (standalone: 1). Report every real finding — the
required / advisory split does the filtering, not omission.

- **required** — merge-safety risks and conformance `missing` / `drift`.
  Everything else is advisory.
- **block** — data loss or corruption, security hole, compat break, or a
  decision missing or drifted. The orchestrator stops for the user before
  fixing.
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

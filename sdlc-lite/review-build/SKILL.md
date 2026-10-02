---
name: review-build
description: >-
  Strict review of the branch diff against the ticket spec. implement-plan
  runs it as the review gate; invoke directly after a dev session or before a
  PR (sdlc-lite chain).
argument-hint: "[plan name]"
disable-model-invocation: true
context: fork
agent: Plan
---

# Review Build

Input: $ARGUMENTS

**Reads:** the branch diff, the spec, the plan (including earlier `## Review`
cycles), `docs/quirks.md`, the repo's `AGENTS.md` / `CLAUDE.md`.
**Writes:** nothing — it returns a verdict and findings; the invoking session
records them.

## Setup

- **Independence:** you run in a fresh, read-only context — `/review-build`
  forks into a `Plan` subagent (frontmatter), and implement-plan launches a
  fresh `Plan` subagent on this file. You see no implementer conversation
  and never edit. The same model is fine; independence comes from the
  context.
- **Model:** the Agent tool's strongest offered model, unless pinned here:
  `review-model:` (unset). A pinned model that cannot launch → the launcher
  asks the user, never substitutes silently.
- **Plan:** the spec and plan absolute paths given; else
  `<root>/docs/plans/<plan>/` (`<root>` = the main checkout,
  `dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`) for
  the plan named in the input, else the current branch name or its ticket
  key. A branch that looks plan-driven but matches no folder → list
  `<root>/docs/plans/` and stop, asking to be re-run with a name.
- **Venue:** the plan's worktree, `<root>/.worktrees/<plan>` (by path, not
  branch — the branch may carry a slug), when a plan resolved; otherwise the
  current checkout. Run every git command there.
- **Clean tree:** `git status --porcelain` must be empty — uncommitted
  changes escape the diff. Dirty → stop and report.
- **Diff:** base = `git symbolic-ref refs/remotes/origin/HEAD` (else
  `main`); review `git diff <base>...HEAD`.
- **Context:** the spec and plan, `docs/quirks.md`, and the repo's
  `AGENTS.md` / `CLAUDE.md` when present. Earlier `## Review` cycles: confirm
  each prior `R` finding's fix removed its cause.
- **Re-run guard:** last `## Review` entry already says `Verdict: ship` at
  this HEAD (or only docs-only commits since) and no spec decision changed
  since → report
  "already reviewed" and stop.
- **Standalone** (no `## Review` line for this HEAD): run the full suite
  yourself; it stands in for that line in the `ship` rule. With a plan, end
  the report with `Record under ## Review in <plan.md absolute path>:` and the
  cycle line plus findings to append — the invoking session writes them.

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
3. **Design** — the plan's Architecture constraints and the neighbouring
   code: layering and dependency direction, dependencies instantiated where
   siblings inject them, a second responsibility added to a unit, a case
   bolted onto a conditional where the codebase dispatches polymorphically,
   a file pushed past ~700 lines, edits outside every task's `Files:`.
4. **Merge safety** — crashes, data corruption, swallowed errors, missing
   tests for changed logic, authz and tenant isolation, secrets or PII in
   logs, observability decisions present. Backward compatibility: signatures,
   removed or renamed fields, new required payload fields; old and new
   versions running side by side; rollback over data the new code wrote;
   migrations additive, re-runnable, and lock-safe on large tables; changed
   behaviour behind the decided switch and default. Performance: N+1,
   unbounded queries, a new query without an index, blocking calls on hot
   paths, leaks.

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

- **required** — merge-safety risks, conformance `missing` / `drift`, and a
  broken Architecture constraint. Everything else is advisory.
- **block** — data loss or corruption, security hole, compat break, or a
  decision missing or drifted. The orchestrator stops for the user before
  fixing.
- **fix-first** — required findings remain; or no spec can be found for a
  plan-driven branch; or any decision is `unverifiable`.
- **ship** — no required findings, and the current `## Review` line shows a
  green `suite:` at the HEAD you reviewed. Missing or mismatched → fix-first,
  and say which.

A `ship` verdict holds only at its reviewed SHA. Any later commit other than
a docs-only one, or a change to the spec's decisions, reopens the review. Follow-up cycles
re-check the changed areas and touched decisions; the cycle that grants `ship`
re-runs the full conformance sweep.

The invoking session writes the `## Review` entry — the reviewer is read-only.

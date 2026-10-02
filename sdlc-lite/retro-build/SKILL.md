---
name: retro-build
description: >-
  Post-merge retrospective on the sdlc-lite chain from one ticket's
  artifacts; proposes amendments and deletions to the skills. Use after merge
  and deploy, or when an escaped defect traces to a ticket. Not the next step
  after implement-plan.
argument-hint: "[plan name]"
disable-model-invocation: true
---

# Retro Build

Input: $ARGUMENTS

Judge the process, not the code. Never edit a skill file without per-item
approval. The skills live in `<skills>` =
`$(cd -P "${CLAUDE_SKILL_DIR}/.." && pwd)` — resolved, because the install
is per-folder symlinks. It must be inside a git repo so every change is a
revertible commit with its evidence — a copied install is not, so ask for
the skills repo path. `retro-log.md` is `<skills>/retro-log.md`; create it
on the first retro.

**Reads:** the plan's spec and plan, `retro-log.md`, `git log --grep 'retro('`.
**Writes:** approved skill edits, `retro-log.md`, and repo facts into
`docs/quirks.md` or `AGENTS.md`.

## 1. Collect

Read the plan and spec in `<root>/docs/plans/<plan>/` (`<root>` = the main
checkout; the plan named in the input, or the
plan from this session). Missing both → "nothing to retro", stop. Quote each
signal verbatim with its location: `> Drift:` notes, `## Blockers` entries, `R` findings from
cycles > 1, `(overrides recommendation: …)`, `supersedes D<n>`, `## E2E`
fails, `## Assumptions` entries proven wrong, accepted risks that
materialized, failed `## Release` steps, and any escaped production defect.
Print:

`metrics(<plan>): lane=<l> tasks=<n> gate-first-pass=<k>/<n> review-cycles=<c> drift=<d> blockers=<b> supersedes=<s> e2e-fail=<e> assumed-wrong=<a>`

## 2. Attribute

- Behaviour the spec never mentioned, a late-surfacing constraint, an
  overridden recommendation, a wrong assumption, or a symbol / path the plan
  got wrong that the repo could have answered → **prepare-plan**.
- Preflight or environment blocker, or a gate cap hit on a runnable command
  → **implement-plan**.
- Finding first caught in cycle > 1, or an escaped defect → **review-build**.
- E2E fail → **prepare-plan** if no decision covered the behaviour, else
  **review-build**.
- Genuinely unknowable environment state → no node, skip.
- Recurring domain fact (filter semantics, scoping, timezone, idempotency) →
  the repo's quirks doc. Repo tooling → that repo's `AGENTS.md`.

## 3. Gate additions

Each signal runs these in order; the first failure drops it:

1. **Recurs?** An earlier entry in `retro-log.md` or
   `git log --grep 'retro('` shows the same class.
2. **Not already a rule?** If a rule exists, the run violated it — louder
   wording changes nothing.
3. **Not already fixed** by committed code or config?
4. **Cross-repo process?** Otherwise it belongs in the repo's `AGENTS.md`.
5. **Fits an existing sentence?** Prefer editing a line to adding one.

## 4. Propose deletions

Rules cost tokens on every run, and stronger models need fewer of them. For
each sdlc-lite skill, list rules with no related signal in the last 5
`retro-log.md` entries as deletion candidates — never an `## Invariants`
bullet, which stays quiet because it works. A quiet rule may be working,
so a deletion is a trial: approved deletions are committed with `retro-prune`
in the message, and if the signal returns in a later retro, revert that commit
(`git log --grep retro-prune`).

## 5. Approve and apply

Present each survivor as:

```
Recommend: apply (<skill> → <section>) | repo-fact (<repo>/AGENTS.md) | delete (<skill> → <rule>)
Edit: <exact line to add, change, or remove>
Evidence: <verbatim quote + location>
Prevents: <failure class>   (deletions: Saves: <words>)
```

plus a drop table (`signal | gate failed`). Ask per item through
`AskUserQuestion` — apply / repo-fact / drop, recommended option first. Then:

- Apply minimal edits; append the drop table and metrics line to
  `retro-log.md` under `## <plan> — <date>`.
- Commit explicit paths: `retro(<plan>): <summary>` (add `retro-prune`
  when it deletes), with evidence, the metrics line, and `wc -w` before → after
  per skill file in the body.

Zero signals and zero deletion candidates is a clean run: append the metrics
line and stop.

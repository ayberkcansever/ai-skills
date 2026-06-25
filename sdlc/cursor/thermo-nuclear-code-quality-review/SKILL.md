---
name: thermo-nuclear-code-quality-review
description: >-
  Branch-diff review in four lenses — simplify (YAGNI / over-engineering),
  maintainability, merge safety, then mandatory feature-docs sync. Use
  /thermo-nuclear-code-quality-review after a dev session, before a PR. Repo-agnostic.
disable-model-invocation: true
---

# Thermo-Nuclear Code Quality Review

Review **current branch changes** through four lenses, in order.
Phases 1–3 are **review-first**: report findings, change code only if the user says "fix".
Phase 4 (docs) is **always applied** where a feature-docs flow exists.

**Step 0 — get the diff.** Resolve the base (`git symbolic-ref refs/remotes/origin/HEAD` or `main`/`master`), then review `git diff <base>...HEAD`. Lenses below reconcile cleanly: **Phase 1 removes what should not exist; Phase 2 restructures what remains.**

**Start the report with a 3-line rollup:**

```
Verdict: ship | fix-first | block
Top issue: <one line, or "none">
Net: -N lines possible | Lean already
```

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

## Phase 3 — Merge safety

Risk tolerance: **low** — override by typing `Risk Tolerance: critical|high|medium|low` in the prompt. Generic checks, every repo:

- **Production safety** — crashes, data corruption, wrong data rendered, broken auth token.
- **Scale & resources** — N+1, blocking calls, memory or connection leaks.
- **Error handling** — swallowed exceptions, missing fallback, observability gaps.
- **Backward compatibility** — API signature change, model field removal, renamed contract or translation key, new required field on a deserialized payload.
- **Test coverage** — missing tests for complex or changed logic.
- **Security & tenant isolation** — no hardcoded credentials or tenant IDs, no PII or tokens in logs.

Stack specifics live in each repo's `AGENTS.md` + rules — apply them, do not duplicate here:

- frontend: React Query (queryKey / enabled / invalidation / rollback), Zustand selector identity, RBAC `routePermissions`, i18n `General.*` reuse.
- backend: handler → usecase → repository, SNS/SQS contract intact, Lambda name ≤ 64 chars.
- llm-service: SQS→SNS envelope parsing, `use_case_cache` module-level, Vertex `api_transport="rest"` protected.

Output:

- **CRITICAL RISKS** (0–3) — would block merge, or "No critical risks found."
- **SUGGESTIONS** (0–3) — high-ROI, low-effort; no speculative items.
- **PRAISE** (0–3).

## Phase 4 — Feature docs sync (mandatory where present)

Read `.cursor/skills/maintain-feature-docs/SKILL.md` in the active repo and follow it. If absent → report "no feature-docs flow" and stop. It owns the `<JIRA-ID>` resolution, drift detection, in-repo edits, and the backend-owns-`design.md` cross-repo rule. Commit only if the user explicitly asked.

Always emit:

```
Feature docs sync (<JIRA-ID>):
- Doc impact: yes | no
- Files updated: …
- Committed: yes | no
```

## Pre-commit

Backend and llm-service run `scripts/check-feature-docs-staged.sh` — warns when code is staged without `docs/features/<JIRA-ID>/`. `FEATURE_DOCS_STRICT=1` blocks.

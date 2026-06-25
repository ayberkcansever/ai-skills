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

Output:

- **CRITICAL RISKS** (0–3) — would block merge, or "No critical risks found."
- **SUGGESTIONS** (0–3) — high-ROI, low-effort; no speculative items.
- **PRAISE** (0–3).

## Phase 4 — Feature docs sync (mandatory where present)

Check if a `maintain-feature-docs` skill or equivalent doc-sync flow exists in the active repo (look for `docs/features/` structure or a skill file). If present, follow it — detect drift between code changes and feature docs, update in-repo docs, and report. If absent → report "no feature-docs flow" and stop.

Always emit:

```
Feature docs sync:
- Doc impact: yes | no
- Files updated: …
- Committed: yes | no
```

## Pre-commit

If the repo runs a feature-docs staged check script (e.g. `scripts/check-feature-docs-staged.sh`), warn when code is staged without corresponding feature docs.

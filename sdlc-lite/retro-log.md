# Retro log

## track-account-portfolio — 2026-10-03
metrics(track-account-portfolio): lane=standard tasks=6 gate-first-pass=5/6 review-cycles=2 drift=4 blockers=0 supersedes=3 e2e-fail=0 assumed-wrong=0

| signal | gate failed |
|---|---|
| Plan T3 test prescribed stubbing `_init_account_from_db` + `runtime_context.get` → R1.1 (test passed with init removed); related: param-versioning "mocked-writer test would still pass" | user dropped (proposed prepare-plan sink-bullet edit) |
| T1 commit swept T5's staged `git rm` — `git commit` commits the whole index, not only the paths just added | 1 — first occurrence (user dropped) |
| Overrides "keep it minimal" (D7, D8, D9, D12) | 2 — already a rule (global CLAUDE.md Simplicity) |
| D2/D5/D6 superseded during planning | 1 — first occurrence |
| T1 drift: `plan_migration` "shared with" `run_migration` contract wrong | 1 — first occurrence |
| T5 drift: `rg` unavailable (RTK hook calls missing `rg` binary; shell `rg` is a function) | no node — machine env |
| T4 drift: StartLimit* keys omitted | not a failure |

Deletions: none proposed — 0 prior entries, no 5-retro history.

## mobile-backend — 2026-11-20
metrics(mobile-backend): lane=standard tasks=22 gate-first-pass=22/22 review-cycles=3 drift=28 blockers=0 supersedes=14 e2e-fail=0 assumed-wrong=1

| signal | gate failed |
|---|---|
| D47–D70: 24 decisions added by the plan's fresh-context check after spec approval, 13 superseding approved ones (spec `**Status:**`: "D47–D70 added from the plan review") | applied — prepare-plan: the fresh-context check moved before spec approval (recurs: track-account-portfolio D2/D5/D6) |
| Task 20 drift: "Subagent briefly used git stash in the shared worktree (restored intact)" | applied — implement-plan: stash added to the no-stage limit (recurs: track-account-portfolio T1 staged `git rm`) |
| T3 drift: `get_open_order` returns `(-1, -1)`, not None; T7/T16 drift: dependency pins found only at build time | user dropped — low damage, "never guess a name" already points this way (recurs: track-account-portfolio T1 contract) |
| D71–D86: 16 decisions added during the build (four verbatim texts, edge cases, exchange errors, a timing window) | 1 — first occurrence |
| 14 overridden recommendations (D1, D5, D13, D21, D24, D25, D35, …), mostly "the beta is small" | 3 — fixed 2026-11-16: a recommendation says what it assumes about the business |
| Reviewer found one instance of a mechanism per cycle: restart loop R1.1 → R2.3 → R3.1; stale watcher before the reconciler acts R1.2 → R2.1 (block) | 1 — first occurrence |
| R2.2: a decision added mid-build (D77) had no test until cycle 2 | 1 — first occurrence (since fixed: a new decision needs its Test matrix row) |
| R1.11, T6 drift: setup-only edits to tests outside the tasks' `Files:` | 1 — first occurrence (since fixed: fan-in status check) |
| A security finding classed advisory, where the skill says block | 1 — first occurrence |
| Task 20 carried over from Tasks 5 and 12 by a money-path review | 1 — first occurrence |
| A15 amended after R1.3 (reconnect while the old unit still runs) | 1 — first occurrence |
| `## E2E` and `## Release` results never written into the plan (user, 2026-11-20: all passed, release smooth, no later defect) | 1 — first occurrence |
| T17 drift: parity script absent from the checkout; 7 suite errors need a local DB | no node — machine env |

Deletions: none proposed — 1 prior entry, no 5-retro history.

## abc-wallet — 2026-11-20
metrics(abc-wallet): lane=standard tasks=33 gate-first-pass=30/30 review-cycles=4 drift=50 blockers=0 supersedes=3 e2e-fail=0 assumed-wrong=0

| signal | gate failed |
|---|---|
| Cycle 2 verdict: "R1.5 tick fixed / startup not (R2.2)" — a finding named one place, the fix covered it, the next cycle found the same mechanism elsewhere | applied — review-build: a finding lists every place its mechanism occurs; implement-plan: fix the cause wherever the mechanism runs (recurs: mobile-backend R1.1 → R2.3 → R3.1, R1.2 → R2.1) |
| T3 drift and every cycle line: 7 errors in `tests/database/test_kline_repository.py`, no `crypto_test` DB on 9432, same on main | applied — repo-fact: abc-crypto CLAUDE.md (recurs: mobile-backend) |
| D33–D47: 15 decisions added by the plan's fresh-context check after spec approval | 3 — fixed by retro(mobile-backend): the check runs before spec approval |
| D55–D66: 12 decisions added during the build, 5 of them verbatim texts and labels | 2 — already a rule: text is decided verbatim or owned by a named person, and the owner approved each mid-build (recurs: mobile-backend D71–D86) |
| R2.3, R4.2, R4.6: a mid-build decision left unconfirmed, unrecorded, or with its Check not amended | 2 — already a rule: a new decision is recorded in prepare-plan's format with its Test matrix row (recurs: mobile-backend R2.2) |
| R1.14, T12 drift: edits outside every task's `Files:` | 3 — fixed 2026-11-16: fan-in status check (recurs: mobile-backend R1.11) |
| 3 overridden recommendations (D6, D7, D15) | 3 — fixed 2026-11-16: a recommendation says what it assumes about the business |
| `## E2E` and `## Release` results never written into the plan (user, 2026-11-20: all went fine, no later defect) | user dropped 2026-11-20 (recurs: mobile-backend) |
| Orchestrator wrote code itself at least five times ("orchestrator fix", "orchestrator commit", "orchestrator-added") | 1 — first occurrence |
| R1.6: a decision's Check (the smoke test) was not run before the first review; run afterwards, it failed | 1 — first occurrence (since fixed: release checks start with the first review cycle) |
| "R1.3 fixed (new risk R2.1)": a fix introduced a new required finding | 1 — first occurrence |
| D48–D54, Tasks 14–22: the owner added a test lab and a test pyramid after plan approval, withdrawing an accepted risk | 1 — first occurrence |
| T13, T22 drift: `.claude/` is behind a hook in the worktree; edits delivered as a patch the owner approved | 1 — first occurrence |
| Cycle 1: one live-data test failed when the DB tunnel dropped; passed alone | no node — machine env |

Deletions: none proposed — 2 prior entries, no 5-retro history.

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

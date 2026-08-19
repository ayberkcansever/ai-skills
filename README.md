# ai-skills

![ai-skills — agent skills for Cursor & Claude Code](assets/banner.png)

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Made for Cursor](https://img.shields.io/badge/made%20for-Cursor-4b8bf5.svg)](https://cursor.com)
[![Made for Claude Code](https://img.shields.io/badge/made%20for-Claude%20Code-d97757.svg)](https://claude.com/product/claude-code)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ayberkcansever/ai-skills/pulls)

Reusable AI agent skills/commands I use day-to-day, organized by category.
Each category holds the same skills in both **Cursor** and **Claude Code**
formats so you can drop them into whichever tool you use.

## Quick start

**Cursor** — copy all skills into your skills directory:

```bash
git clone https://github.com/ayberkcansever/ai-skills.git
cp -r ai-skills/*/cursor/* ~/.cursor/skills/
```

**Claude Code** — copy all commands:

```bash
git clone https://github.com/ayberkcansever/ai-skills.git
cp ai-skills/*/claude/*.md ~/.claude/commands/
```

Or install a single skill — each category section below lists its skills and
how they chain together.

## Categories

| Category | What it covers |
|----------|----------------|
| [`sdlc/`](#sdlc--software-development-lifecycle) | From fuzzy idea to merged, maintainable code — plan, execute, review, retro. |
| [`learning/`](#learning--continuous-learning-loop) | Decide what to learn next, then actually learn it — radar scans feeding topic briefs. |

---

## `sdlc/` — software development lifecycle

![sdlc — from fuzzy idea to merged, maintainable code](assets/banner-sdlc.png)

Agentic coding fails the same ways over and over. Each skill in this chain is
built around a counter:

- **Agents transcribe instead of discovering.** `interview-plan` reads the
  codebase *before* asking anything, then asks one code-grounded question at a
  time — a plan built only from the user's words is the exact failure mode it
  exists to prevent.
- **Agents overclaim.** `execute-plan`'s orchestrator re-runs every task's
  gate command itself before ticking a checkbox — a subagent's "done" is a
  claim, not evidence.
- **Reviews go stale.** `thermo-nuclear-code-quality-review` pins its verdict
  to the reviewed commit SHA; any later code commit re-opens the gate until
  the verdict is `ship` again at the new HEAD.
- **Agents never learn.** `graph-retro` mines each shipped ticket's plan for
  drift notes, blockers, and review findings, attributes each to the skill
  that should have prevented it, and proposes one-line amendments — applied
  only after human approval, committed to your skills repo with the evidence.

### Skills

| Skill | What it does |
|-------|--------------|
| `brainstorm` | Turns a fuzzy idea into an approved design through one-question-at-a-time dialogue, 2-3 proposed approaches, and a written spec — with an optional browser-based visual companion for mockups/diagrams. Gates on user approval before any implementation. |
| `interview-plan` | Interviews you one question at a time, reads the codebase first, and produces an **ambiguity-free** spec across business, backward-compat, and technical lenses. |
| `write-plan` | Turns the spec into a bite-sized, TDD-oriented implementation plan with exact files, code, and verification commands. |
| `execute-plan` | Executes the plan task-by-task (subagent-per-task by default), re-running each task's gate itself before ticking it, committing as it goes, then running the review gate until the verdict is `ship`. |
| `git-worktrees` | Sets up an isolated git worktree (detect → consent → create `.worktrees/<branch>` → baseline check) so plan execution never disturbs the user's checkout. Referenced by `write-plan` and `execute-plan`. |
| `thermo-nuclear-code-quality-review` | A strict five-lens review — checks the diff against the spec's decisions (conformance/semantic drift), then flags over-engineering, spaghetti growth, architecture violations, and merge risks before the PR merges. |
| `graph-retro` | Post-deploy retrospective on the skill chain itself — extracts every drift note, blocker, and review finding from a shipped ticket's plan, attributes each to the skill that should have prevented it, and proposes human-gated amendments so the chain improves with every ticket. |

### Flow

Start with **either** `brainstorm` or `interview-plan` (not both required):

```mermaid
flowchart LR
    B["/brainstorm<br/><i>fuzzy idea</i>"] --> W["/write-plan"]
    I["/interview-plan<br/><i>known scope</i>"] --> W
    W --> E["/execute-plan"]
    WT["git-worktrees<br/><i>isolated workspace</i>"] -.-> E
    E --> R["/thermo-nuclear-<br/>code-quality-review"]
    R -->|"verdict: ship"| PR(["PR ready"])
    R -->|"findings → remediation tasks"| E
    PR -.->|"merged + deployed"| G["/graph-retro"]
    G -.->|"approved amendments"| S[("skills repo")]
```

Pick the entry point that fits the task:

- **`brainstorm`** — fuzzy idea, no clear scope yet. Shapes it into an approved design.
- **`interview-plan`** — scope is roughly known. Stress-tests it into an ambiguity-free plan.

Use one, the other, or both (`brainstorm` to shape, then `interview-plan` to harden). `write-plan` onward is the same regardless of entry point.

After merge and deploy, `graph-retro` closes the loop: the chain's own
artifacts (drift notes, blockers, review findings) become proposals to improve
the skills themselves — the chain gets better with every ticket it ships.

### A taste

`interview-plan` doesn't ask generic questions — every question is grounded in
something it actually read in your codebase, always with a recommendation:

```
Q3 [compat]: Break sales, migrate it, or dual-write `legacyTarget` for one release?
Found: `tagLookup` read in `sales/.../x.ts:42` and `workflow/.../y.ts:88`;
       sales reads `legacyTarget`, which your change removes.
Recommendation: dual-write one release, then drop — zero-downtime.
Why: sales deploys on a different cadence; a hard break strands it.
```

Every decision lands in a spec file with a `Check:` line (a runnable command or
named test that proves it), every spec decision maps to a plan task, every task
commit carries a `[T<N>]` tag — a traceability chain from decision to diff.

### Notes

- These skills reference generic conventions (e.g. `docs/features/<TICKET-ID>/`,
  `docs/plans/<TICKET-ID>/`, `docs/specs/<TICKET-ID>/`, explicit-path commits).
  Adjust paths, ticket-key format, and commit tooling to match your own repo.
- `thermo-nuclear-code-quality-review` pins a dedicated **review model** so the
  reviewer never inherits the implementer session's model — fill in your chosen
  model slug in its "Pinned review model" section (write-plan and execute-plan
  reference that section instead of hardcoding a slug).
- Examples use Python/`pytest` and a `handler → use case → repository` layering
  purely as illustration — apply them to whatever stack your repo uses.
- `graph-retro` commits approved amendments to your skills directory — keep
  that directory a git repo (e.g. `git init ~/.cursor/skills`) so every skill
  change is a reviewed, revertible commit with its evidence in the message.
  Amendments land in the *installed* copy; periodically diff it against this
  repo and upstream the keepers, or the two will drift.
- `brainstorm` (Cursor variant) ships its **visual companion** — `visual-companion.md`
  plus a `scripts/` folder with a small local Node server for showing mockups in
  the browser. It writes session state under `.superpowers/brainstorm/` in your
  project; add `.superpowers/` to your `.gitignore`. The companion is optional —
  the skill works text-only without it.

---

## `learning/` — continuous learning loop

![learning — continuous learning loop](assets/banner-learning.png)

A chain aimed at the engineer rather than the ticket: decide **what** to learn
next, then actually learn it — with the output of one skill feeding the other
in both directions.

### Skills

| Skill | What it does |
|-------|--------------|
| `tech-radar` | Answers "what should I learn next?" for a principal software + AI engineer. A deterministic stdlib crawler (`scripts/scan_feeds.py`, driven by an editable `feeds.toml` registry of ~55 primary feeds — AI labs, cloud/platform, every major language, databases, famous framework releases, production engineering blogs, security, HN/Lobsters, endoflife.date) pulls the window into a dated intake file; the agent triages 100% of items (keeps + coded drops), confirms adoption evidence, merges a persistent watchlist with movement markers (new/rising/holding/fading), and ranks into Thoughtworks-style quadrants (Techniques / Platforms / Tools / Languages & Frameworks) with whole-landscape balance enforced. Outputs a ranked top-5 + quadrant map saved as a dated HTML scan. Supports full scans and quick watchlist-update scans. |
| `learn` | Learns one topic to a correct 101 level in minimal time. Researches recent primary sources, produces a brief (101 mental model, what changed, verdict) saved to a searchable HTML library, then offers a learn path, a run-and-observe hands-on lab (code ships complete and verified; you predict, run, and explain back), and a quiz. |

### Flow

The two share one library (`~/Documents/tech-briefs/`): briefs produced by
`learn` are the radar's dedupe memory, and each scan's ranked picks are the
learn skill's input queue. The radar also keeps a persistent watchlist between
scans (candidates too real to discard but not yet rankable), and rotates its
manual sources and wildcard searches based on the previous scan's coverage.

```mermaid
flowchart LR
    F[("feeds.toml<br/>~55 feeds")] -->|"scan_feeds.py<br/>(deterministic crawl)"| R["/tech-radar<br/><i>what to learn?</i>"]
    R -->|"ranked top-5"| B["/learn<br/><i>learn one topic</i>"]
    B -->|"brief + lab + quiz"| L[("brief library<br/>~/Documents/tech-briefs/")]
    L -.->|"dedupe memory +<br/>rotation"| R
    W[("watchlist.json<br/>movement markers")] -.-> R
    R -.-> W
```

### Notes

- Output goes to `~/Documents/tech-briefs/` (briefs, radar scans, intake files,
  watchlist, and a self-rebuilding `index.html`) — never into the current repo.
- The radar's coverage is a registry edit, not a prompt edit: add or drop a
  source by editing `feeds.toml`; the crawler and skill pick it up unchanged.
  Sources without machine-readable feeds are `type = "manual"` entries the
  agent covers with a search hint, so nothing is silently skipped.
- The Claude variants are text ports — their supporting files
  (`template.html`, `lab-template.html`, `notes-template.html`, `feeds.toml`,
  `scripts/`) ship in the matching `learning/cursor/<skill>/` folder; install
  the Cursor variant alongside or adjust the paths.
- `tech-radar` expects `learn` installed as a sibling
  (`~/.cursor/skills/learn/`) — install both together.

---

## Layout

```
<category>/                 # sdlc/, learning/
  cursor/<skill>/SKILL.md   # Cursor skill format (+ templates/scripts)
  claude/<skill>.md         # Claude Code command format
```

Adding a category is additive: a new folder, a new README section, a new
banner — existing categories stay untouched.

## Notes

- The Cursor and Claude variants are kept in sync but may differ slightly in
  formatting to match each tool's conventions.

## Credits

The planning/brainstorming skills are adapted from the open-source
[Superpowers](https://github.com/obra/superpowers) project (MIT). The visual
companion server scripts under `sdlc/cursor/brainstorm/scripts/` originate there.

## License

MIT — use, adapt, and share freely.

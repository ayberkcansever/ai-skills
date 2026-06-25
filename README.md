# ai-skills

Reusable AI agent skills/commands I use day-to-day, organized by category.
Each category folder holds the same skill in both **Cursor** and **Claude Code**
formats so you can drop them into whichever tool you use.

## Categories

### `sdlc/` — software development lifecycle

A chained workflow that takes a task from fuzzy idea to merged, maintainable code:

| Skill | What it does |
|-------|--------------|
| `brainstorm` | Turns a fuzzy idea into an approved design through one-question-at-a-time dialogue, 2-3 proposed approaches, and a written spec — with an optional browser-based visual companion for mockups/diagrams. Gates on user approval before any implementation. |
| `interview-plan` | Interviews you one question at a time, reads the codebase first, and produces an **ambiguity-free** spec across business, backward-compat, and technical lenses. |
| `write-plan` | Turns the spec into a bite-sized, TDD-oriented implementation plan with exact files, code, and verification commands. |
| `execute-plan` | Executes the plan task-by-task, running the verification each step defines and committing as it goes. |
| `thermo-nuclear-code-quality-review` | A strict maintainability review — flags spaghetti growth, oversized files, leaky abstractions, and pushes for structural simplification before the PR merges. |

Typical flow:

```
/brainstorm  ->  /interview-plan  ->  /write-plan  ->  /execute-plan  ->  /thermo-nuclear-code-quality-review
```

`brainstorm` and `interview-plan` overlap — `brainstorm` is for shaping a fuzzy
idea into a design; `interview-plan` is for stress-testing an already-scoped
change into an ambiguity-free plan. Use whichever the task needs (or both).

## Layout

```
sdlc/
  cursor/<skill>/SKILL.md   # Cursor skill format
  claude/<skill>.md         # Claude Code command format
```

## Install

### Cursor

Copy a skill folder into your Cursor skills directory:

```bash
cp -r sdlc/cursor/interview-plan ~/.cursor/skills/
```

Then invoke it in chat (e.g. `/interview-plan`) or let the agent pick it up by
description.

### Claude Code

Copy a command file into your Claude commands directory:

```bash
cp sdlc/claude/interview-plan.md ~/.claude/commands/
```

Then run `/interview-plan` in Claude Code.

## Notes

- These skills reference generic conventions (e.g. `docs/features/<TICKET-ID>/`,
  `docs/plans/<TICKET-ID>/`, explicit-path commits). Adjust paths, ticket-key
  format, and commit tooling to match your own repo.
- Examples use Python/`pytest` and a `handler → use case → repository` layering
  purely as illustration — apply them to whatever stack your repo uses.
- The Cursor and Claude variants are kept in sync but may differ slightly in
  formatting to match each tool's conventions.
- `brainstorm` (Cursor variant) ships its **visual companion** — `visual-companion.md`
  plus a `scripts/` folder with a small local Node server for showing mockups in
  the browser. It writes session state under `.superpowers/brainstorm/` in your
  project; add `.superpowers/` to your `.gitignore`. The companion is optional —
  the skill works text-only without it.

## Credits

The planning/brainstorming skills are adapted from the open-source
[Superpowers](https://github.com/obra/superpowers) project (MIT). The visual
companion server scripts under `sdlc/cursor/brainstorm/scripts/` originate there.

## License

MIT — use, adapt, and share freely.

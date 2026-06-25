# ai-skills

Reusable AI agent skills/commands I use day-to-day, organized by category.
Each category folder holds the same skill in both **Cursor** and **Claude Code**
formats so you can drop them into whichever tool you use.

## Categories

### `sdlc/` — software development lifecycle

A chained workflow that takes a task from fuzzy idea to merged, maintainable code:

| Skill | What it does |
|-------|--------------|
| `interview-plan` | Interviews you one question at a time, reads the codebase first, and produces an **ambiguity-free** spec across business, backward-compat, and technical lenses. |
| `write-plan` | Turns the spec into a bite-sized, TDD-oriented implementation plan with exact files, code, and verification commands. |
| `execute-plan` | Executes the plan task-by-task, running the verification each step defines and committing as it goes. |
| `thermo-nuclear-code-quality-review` | A strict maintainability review — flags spaghetti growth, oversized files, leaky abstractions, and pushes for structural simplification before the PR merges. |

Typical flow:

```
/interview-plan  ->  /write-plan  ->  /execute-plan  ->  /thermo-nuclear-code-quality-review
```

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

- These skills reference generic conventions (e.g. `docs/features/<JIRA-ID>/`,
  a `scripts/committer` helper). Adjust paths and commit tooling to match your
  own repo.
- The Cursor and Claude variants are kept in sync but may differ slightly in
  formatting to match each tool's conventions.

## License

MIT — use, adapt, and share freely.

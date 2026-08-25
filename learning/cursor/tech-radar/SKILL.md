---
name: tech-radar
description: Builds a Thoughtworks-style learning radar of what a principal software + AI engineer should learn next — crawl registry feeds, triage, confirm adoption, place Learn/Try/Watch/Skip blips, save dated HTML. Use when the user asks what to learn, scan the radar, recent topics worth learning, what is moving in tech, or wants learning recommendations without naming a topic. Not for briefing a named topic — that is the learn skill.
disable-model-invocation: true
compatibility: Requires Python 3.11+, network access, and write access to ~/Documents/tech-briefs
---

# Tech Radar

Goal: answer **"what should I learn next?"** for a principal software + AI engineer — a Thoughtworks-style radar, not a trends listicle. Every candidate lands on one of four **rings** in its quadrant, and the **Learn ring is the answer**. Every placement must survive: *"why this, why now, and why for someone at this level?"*

This skill finds topics; sibling **learn** (`~/.cursor/skills/learn/`) briefs them. Shared library: briefs are this skill's memory; this skill's Learn ring is that skill's input queue.

## The role lens

Apply ruthlessly. Principal software + AI engineer needs:

- **Decision leverage** — architecture choices, build-vs-buy, platform bets, how you review others' designs. Not "another framework that renders lists".
- **AI engineering depth** — agents, serving/inference economics, evals, retrieval, routing, AI-adjacent infra. Signal over demos. One strand of the lens, **not** the scan's default topic.
- **Durability** — still matters in 2 years. Hot repo, no production adoption → Watch, not Learn.
- **Force-multiplier** — upgrades how the team works, not personal trivia.
- **101-feasibility** — correct 101 in roughly a day via the learn loop. Semester-scale → recommend the entry slice.

Out of scope: junior fundamentals, certification chasing, single-vendor launch fluff, marketing-only evidence.

A scan whose pool is nearly all AI with no AI focus filter is a **skew bug**. Classify every candidate into a Thoughtworks quadrant:

- **Techniques** — ways of working (patterns, practices, approaches).
- **Platforms** — things you build on (clouds, runtimes, databases, inference platforms).
- **Tools** — software you use rather than build on.
- **Languages & Frameworks** — languages, major framework releases, SDKs, stdlib.

Rings (learning verbs, not Thoughtworks Adopt/Trial/Assess/Hold):

- **Learn** — start now. Production-grade; would start `/learn` this week. Selective; past ~8 you are not choosing.
- **Try** — cheap pass is enough (release notes / half-day skim), or second in queue.
- **Watch** — real signal, not rankable yet. Every Watch blip has a concrete *promote when:*.
- **Skip** — deliberately not spending time, plus what would move it back in.

Optional focus ("AI only", "infra only") narrows subjects; level stays principal.

## Architecture

Coverage is **deterministic first, search second**. Edit coverage in [feeds.toml](feeds.toml), not this file.

```
feeds.toml                 registry + [settings]
scripts/scan_feeds.py      crawler → reviewable set + drop ledger + feed health
scripts/test_scan_feeds.py drop-rule tests (no network)
scripts/validate_triage.py ledger arithmetic
references/                loaded per step, not at activate
assets/template.html       HTML renderer — fill at Step 8
```

Crawler pre-drops routine noise; agent judges the rest. Novelty (announcing / GA / x.0 / deprecated / open-sourced / preview) and security (CVE, vulnerability, supply-chain) **never auto-drop**.

Skill root is `~/.cursor/skills/tech-radar/`. Agent cwd is usually a project — run scripts with that prefix (the one allowed absolute).

## Storage

```
~/Documents/tech-briefs/radar/YYYY-MM-DD.html
~/Documents/tech-briefs/radar/intake/
~/Documents/tech-briefs/radar/feed_health.json
~/Documents/tech-briefs/radar/watchlist.json
~/Documents/tech-briefs/index.html
```

`mkdir -p ~/Documents/tech-briefs/radar` before writing. Same-day re-scan overwrites that date's file; never `YYYY-MM-DD-2.html`.

## Inputs

None required. Optional: focus filter, window override (default **90 days**), "include topics I already briefed" to disable dedupe.

**Cadence:** full scan every **2–4 weeks** against the 90-day window. Daily/twice-weekly full scans re-triage the same items — use **quick** for those.

**Mode:** **full** (default) or **quick** ("quick scan", "update the watchlist") — crawl + triage + watchlist + short chat summary; no confirm, no rings, no HTML. Quick never places blips (would violate the two-signal rule).

## Load order

Do not skip a linked file the current step names. Do not read later files early.

```
- [ ] Read [references/workflow.md](references/workflow.md) — Steps 1–4 always; Step 6 watchlist; Step 7 rings (full only)
- [ ] Step 1–2: memory, then crawl
- [ ] Step 3–4: manual sweep, 100% triage, validate_triage.py
- [ ] Quick → watchlist merge in workflow.md, chat summary, STOP. Do not read gates.md or output.md.
- [ ] Full Step 5: read [references/gates.md](references/gates.md), clear both gates before placing blips
- [ ] Full Step 7–9: rings, then [references/output.md](references/output.md) + [assets/template.html](assets/template.html)
```

## Principles

- **Why this, why now, why this level — or cut it.**
- **Learn/Try momentum = ≥2 independent dated signals.** Vendor launch + vendor blog = one signal.
- **Deterministic first, search second.** Adding a source is a [feeds.toml](feeds.toml) edit.
- **Disposition everything, in a file.** Crawler `drops.txt` + agent `triage.json` account for the whole crawl.
- **Whole landscape, not the AI corner.** Quadrant balance is a gate. Watch ≠ Learn.

## Handoff

Full scan ends with: *"Pick a blip number — I'll run the full brief (and lab) on it."* On a pick, invoke the **learn** skill on that topic.

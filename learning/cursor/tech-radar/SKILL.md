---
name: tech-radar
description: Discover what to learn next as a principal software + AI engineer. A deterministic crawler (scripts/scan_feeds.py, driven by feeds.toml) pulls ~55 primary feeds — AI labs, cloud/platform, every major language, databases, famous framework releases, production engineering blogs, security, HN/Lobsters gravity, endoflife.date — into a dated intake file; the agent triages 100% of items (keeps and logged drops), confirms adoption evidence, merges a persistent watchlist with movement markers, then places every candidate on a Thoughtworks-style radar — four quadrants (Techniques / Platforms / Tools / Languages & Frameworks) × four rings (Learn / Try / Watch / Skip — Thoughtworks geometry with learning-native names) rendered as an interactive SVG radar with numbered blips and per-blip writeups — with whole-landscape balance enforced, AI one strand not the default. Dedupes against the user's brief library; the Learn ring is the learn-next answer, each Learn blip runs via the learn skill (/learn). Supports full scans and quick watchlist-update scans. Use when the user asks "what should I learn", "scan the radar", "recent topics worth learning", "what's moving in tech/AI", or wants learning recommendations without naming a topic.
---

# Tech Radar

Goal: answer **"what should I learn next?"** for a principal software + AI engineer — a Thoughtworks-style radar, not a trends listicle. Every candidate lands on one of four **rings** in its quadrant, and the **Learn ring is the answer**. Every placement must survive the question: *"why this, why now, and why for someone at this level?"*

This skill finds the topics; the sibling **learn** skill (`~/.cursor/skills/learn/`) learns them (brief → learn path → lab → quiz). The two share one library: briefs produced there are this skill's memory, and this skill's output is that skill's input queue.

## The role lens

All ranking happens through this lens. It is the skill's identity — apply it ruthlessly.

A principal software + AI engineer needs topics that provide:

- **Decision leverage** — things that change architecture choices, build-vs-buy calls, platform bets, or how you review others' designs. Not "another framework that renders lists".
- **AI engineering depth** — the moving frontier: agent architectures, LLM serving/inference economics, evals and reliability, retrieval, model routing, AI-adjacent infra. Signal over demos.
- **Durability** — likely to still matter in 2 years. A hot repo with no production adoption is a *watch*, not a *learn-now*.
- **Force-multiplier potential** — knowledge that upgrades how the whole team works (tooling, patterns, platform capabilities), not just personal trivia.
- **101-feasibility** — learnable to a correct 101 in roughly a day via the learn loop. If a topic needs a semester, recommend its learnable entry slice instead.

Explicitly out of scope: junior-level fundamentals, certification chasing, single-vendor feature announcements dressed as trends, and anything whose only evidence is marketing.

**The lens is whole-landscape, Thoughtworks-Radar-wide.** Platforms, techniques/approaches, tools, and languages & frameworks all count as first-class scan subjects — AI engineering depth is one strand of the lens, not the scan's default topic. A scan whose candidates are nearly all AI when no AI focus filter was given is a skew bug, not a signal read. Every candidate is classified into one of four quadrants (same taxonomy as the Thoughtworks Radar):

- **Techniques** — ways of working: architecture patterns, engineering practices, approaches (e.g. threat modeling for agents, spec-driven development, cell-based architecture).
- **Platforms** — things you build on: clouds, runtimes, databases, model/inference platforms, infra products.
- **Tools** — software you use rather than build on: dev tools, CI/CD, observability, utilities, coding agents.
- **Languages & Frameworks** — languages, major framework releases, SDKs, standard-library movements.

**The rings (Thoughtworks geometry, learning-native names — Thoughtworks' Adopt/Trial/Assess/Hold are adoption advice for teams; a learning radar needs verbs about *your time*, so the rings are):**

- **Learn** — *start now.* Production-grade evidence; you would start the `/learn` loop this week. This ring is deliberately selective: only items you would actually start; if it grows past ~8, you are not choosing.
- **Try** — *the cheap pass is enough.* Clear value but second in the queue, or a half-day skim / the release notes are the whole 101.
- **Watch** — *track with a condition.* Real signal, not rankable yet; every Watch blip carries a concrete *promote when:* condition (from the watchlist).
- **Skip** — *deliberately not spending time.* Fading, contested, or no adoption evidence — with one line on what would move it back in.

Optional per-run focus narrows the lens ("AI only", "infra only", "what should I learn for the next quarter") — but the level stays principal.

## Architecture

Coverage is **deterministic first, search second**. A feed registry and a stdlib crawler do the wide sweep for free; agent searches are reserved for sources without machine-readable feeds, adoption confirmation, and a small wildcard slice.

```
feeds.toml            registry: ~55 feeds (rss/hn/lobsters/endoflife) + manual entries
scripts/scan_feeds.py stdlib crawler → intake JSON + compact titles view + feed health
intake/YYYY-MM-DD.*   every windowed item, indexed — the triage input
watchlist.json        persistent candidates across scans, with movement status
```

Editing coverage = editing `feeds.toml`. No skill-text change needed to add or drop a source.

## Storage

```
~/Documents/tech-briefs/radar/YYYY-MM-DD.html    # one file per scan, dated
~/Documents/tech-briefs/radar/intake/            # crawler output (JSON + titles.txt per date)
~/Documents/tech-briefs/radar/watchlist.json     # persistent watchlist, updated every scan
~/Documents/tech-briefs/index.html               # library index links to the latest scan
```

- `mkdir -p ~/Documents/tech-briefs/radar` before writing (the crawler creates `intake/` itself).
- One scan record per date: a same-day re-scan **updates that day's file in place**; a new day gets a new file. Never create `YYYY-MM-DD-2.html` variants — the index and rotation logic assume date-named files.
- Fill the `radar-*` `<meta>` tags in [template.html](template.html).
- **Rebuild the library index after every save**: `python3 ~/.cursor/skills/learn/scripts/build_index.py` — it links the newest scan in the header.
- Print the saved path plus `open ~/Documents/tech-briefs/radar/<date>.html`.

## Inputs

- None required.
- Optional: focus filter ("AI only", "infra/platform only"), window override (default **3 months**), "include topics I already briefed" to disable dedupe.
- Optional mode: **full** (default — everything below) or **quick** ("quick scan", "update the watchlist") — crawl + triage + watchlist update + a short movers summary in chat; no confirm pass, no ring placement, no HTML. Quick exists for cheap between-scan refreshes; ring placement without confirmed evidence would violate the two-signal rule, so quick never places blips.

## Workflow

```
- [ ] Step 1: Load memory — brief library, watchlist, previous scan
- [ ] Step 2: Intake crawl — run the script, read feed health
- [ ] Step 3: Manual sweep — agent-fetched sources + wildcard slice
- [ ] Step 4: Triage — 100% disposition of intake + watchlist
- [ ] Step 5: Confirm evidence, build candidate pool, clear the gates
- [ ] Step 6: Merge watchlist, place every candidate on a ring
- [ ] Step 7: Output the radar, save HTML, rebuild index, hand off   (quick mode stops after Step 4 + watchlist update)
```

### Step 1: Load memory

Read `~/Documents/tech-briefs/` before anything else:

- List existing briefs: topic, `brief-date`, `brief-verdict`, `brief-poc` status (meta tags in each HTML).
- **Already briefed and fresh** → excluded from recommendations; listed in the scan's "already covered" line so the user sees the dedupe worked.
- **Briefed but stale** (>180 days) or verdict was "Hold — revisit when X" and X may have happened → eligible again, flagged as *refresh* rather than *new*.
- **Lab done** topics indicate the user's strong areas — use them to spot *gaps* (e.g. lots of agent-framework briefs, nothing on serving/inference → inference economics ranks up).
- **Watchlist**: read `radar/watchlist.json` — every item on it must be dispositioned this scan (Step 6). Missing file = first scan, start empty.
- **Previous scan**: read the newest file in `~/Documents/tech-briefs/radar/` — its `radar-venues` meta lists which manual sources and wildcard queries were used; prefer different ones this scan.
- Empty library → say so and rank purely on the landscape.

### Step 2: Intake crawl

Run the crawler (one command — it is fast, parallel, and free):

```bash
python3 ~/.cursor/skills/tech-radar/scripts/scan_feeds.py
```

It reads [feeds.toml](feeds.toml), fetches every machine-readable feed (~55: AI labs, cloud/platform, all major language blogs, databases, famous framework `releases.atom`, production engineering blogs, security, InfoQ, HN ≥400 points, Lobsters, endoflife.date), window-filters, dedupes, drops noise keywords, and writes:

- `radar/intake/<date>.json` — full items with URLs + per-feed health + the manual-feed list
- `radar/intake/<date>.titles.txt` — compact `index|date|source|title` lines (**triage reads this**, not the JSON)

**Feed health rules (non-negotiable):**

- Any feed with `status: error` → run a `site:` fallback search for that source's recent posts in this scan. A broken feed never means silently skipped coverage.
- A feed erroring for a **second consecutive scan** → include a "registry fix needed" line in the scan output proposing a replacement URL (probe for one if quick to do).
- `empty` is usually fine (quiet feed) — flag only if a normally busy feed goes empty.

### Step 3: Manual sweep

The crawler's summary lists `manual` feeds — sources with no machine-readable feed. The agent covers each with its registry `hint` via `WebSearch`/`WebFetch` (parallel where independent). Currently: Anthropic engineering, MCP blog/SEPs, DeepMind, Shopify/Uber engineering, OWASP GenAI, the latest **Thoughtworks Technology Radar volume** (mine blips + themes — in scope even if published outside the window), in-season **trend surveys** (InfoQ Trends, DORA, StackOverflow, CNCF, State of JS, RedMonk — whichever is fresh), and **conference tracks** in window ±6 weeks (titles + official abstracts are enough for candidacy; never invent talk contents).

Add on top:

- **Discussion gravity**: a Reddit shortlist pass (`r/MachineLearning`, `r/LocalLLaMA`, `r/kubernetes`, `r/aws`, `r/devops`, `r/typescript` — high-upvote, deep comments, as pointers only).
- **Wildcard slice**: 2–3 open searches rotated per scan (recorded in `radar-venues` so the next scan varies them) — e.g. one AI-flavored and one deliberately generic: `"generally available" OR GA (agent OR inference OR gateway) 2026` / `"major release" (platform OR runtime OR database OR framework) 2026`.
- **Stack-adjacent**: if the user's stack is visible (workspace AGENTS.md, recent briefs — e.g. AWS/Bedrock/LangGraph/TypeScript/Python), one search keyed to that stack's recent releases.

**Trust rules (apply to every manually fetched source and every confirmation):**

- **Trustable =** primary vendor/project feeds, official standards bodies, established engineering blogs of companies that run things in production, recognized practitioners with a track record, peer venues (HN/Lobsters/major subreddits) *for pointers*, reputable tech press.
- **Never trustable as evidence:** SEO content farms, AI-spun aggregator sites, anonymous listicles, "top 10 tools" affiliate posts. No author + no date + reads like autocomplete = drop.
- **Vendor blogs** are trustable for facts about *their own* releases; superiority claims need independent confirmation.
- **Aggregators/newsletters** seed candidates, never serve as sole evidence.

### Step 4: Triage — 100% disposition

Read the **titles view** (`intake/<date>.titles.txt`) and disposition **every item** — nothing falls on the floor silently:

- **keep** → candidate for Step 5 (typically 30–50 from ~700 items). Reference items by index.
- **drop** → assign one reason code: `noise` (non-tech / off-lens), `minor` (patch releases, routine updates), `marketing` (launch fluff, no engineering substance), `dup` (same story as a kept item), `junior` (not principal-leverage).

The scan output reports drop counts per reason code plus keep count — the triage ledger. Anyone auditing the scan can see what was seen and why it was excluded. Items from the manual sweep join the keeps directly (they were hand-picked, they are already triaged).

Watchlist items get their disposition in Step 6 — but scan the titles for signals matching watchlist topics **now** and tag them while reading.

**Quick mode stops here**: update `watchlist.json` (Step 6's merge rules, using unconfirmed keep signals), report movers + feed health in chat, done.

### Step 5: Confirm + candidate pool

For each keep that could plausibly rank, run **one confirming search** for adoption evidence (`"X in production"`, `"migrating to X"`, `"X postmortem"`, `"X GA"`). Budget: **≤20 confirming searches** — spend them on likely Learn/Try material, not on obvious Skip blips. Total agent search budget per full scan (manual sweep + wildcard + confirm) is roughly **25–35 calls**; the crawl itself costs one command.

Collect **15–25 candidates**. For each record:

- name + one-line what-it-is;
- **quadrant** (`Techniques`, `Platforms`, `Tools`, `Languages & Frameworks`);
- category (brief-library taxonomy: `AI-ML`, `Infrastructure`, `Data`, `Security`, `Languages-Frameworks`, `DevTools`, `Web`, `Other`);
- **momentum evidence, dated** — at least 2 independent signals from different sources. One vendor launch is not momentum;
- maturity: research / early-adopter / production-adopted;
- which must-not-miss bucket(s) it satisfies.

**Window exception — continuing momentum:** a landmark from 3–6 months ago stays eligible if the window still shows migration posts, GA follow-through, conference tracks, or HN recurrence.

**Must-not-miss checklist (clear every bucket — ≥1 candidate or a one-line "cleared: quiet / not principal-leverage"):**

1. **Agent/tool protocols** — MCP, A2A, new wire-level agent standards
2. **Agent security threat models** — lethal trifecta / permission-hungry agents / structural mitigations
3. **Evals & release control** — agent evals, online evals, CI gating quality
4. **Inference / serving infra** — Gateway API Inference, vLLM/KServe, AI gateways, GPU scheduling
5. **Coding-agent harnesses** — Agent Skills, harness engineering, spec-driven agent workflows
6. **Agent memory / state** — production memory layers, not chat "memory" demos
7. **Model economics / routing** — multi-tier model strategy, open-weight vs closed tradeoffs
8. **Platform shifts (non-AI)** — famous platforms/runtimes shipping majors or GA primitives: K8s/CNCF graduations, edge/serverless, WASM, database engines, cloud primitives
9. **Techniques & practices** — architecture patterns and approaches with adoption evidence (Thoughtworks blips/themes, DORA findings, migration writeups)
10. **Languages & frameworks** — major language releases, framework majors, TC39/std-lib advancements, notable deprecations
11. **Stack-adjacent** — at least one candidate or clearance keyed to the user's visible stack

**Coverage gate:** every erroring feed got its fallback search; every manual feed was covered; ≥3 candidates in the pool come from sources other than the top HN stories (the registry exists so the pool is not just HN's front page). **Quadrant balance gate:** pool holds **≥3 candidates per quadrant** or documents a quadrant as genuinely quiet; without an AI focus filter, at most **half** the pool may be AI-ML and the Learn ring must span **≥3 quadrants**. Fail a gate → widen (more manual sources, second wildcard pass) and re-pass. Do not place blips until both gates pass.

### Step 6: Watchlist merge

`radar/watchlist.json` holds candidates that did not make a previous Learn ring but were too real to discard. Shape:

```json
{
  "updated": "YYYY-MM-DD",
  "items": [
    {
      "topic": "…", "quadrant": "Platforms", "category": "Infrastructure",
      "first_seen": "YYYY-MM-DD", "last_signal": "YYYY-MM-DD",
      "status": "new | rising | holding | fading",
      "scans_quiet": 0,
      "evidence": [{"d": "YYYY-MM-DD", "src": "feed-id or venue", "u": "URL"}],
      "note": "one line — what it is and what would promote it"
    }
  ]
}
```

Disposition every watchlist item, every scan:

- **promote** — new strong signal this window → joins the candidate pool (and possibly the Learn ring). Remove from watchlist if it reaches Learn; keep as `rising` if it stays Try/Watch.
- **hold** — new signal, still not Learn-grade → update `last_signal`, append evidence, status `rising` or `holding`, reset `scans_quiet`.
- **quiet** — no signal this window → `scans_quiet += 1`, status `fading` at 2.
- **expire** — `scans_quiet` reaches 3 → remove; list under "expired" in the scan output (visible, not silent).
- **briefed** — user briefed it since last scan → remove (it lives in the library now).

New this scan: pool candidates below the Learn ring with real momentum enter as `status: new`. Watchlist status maps 1:1 to the blip **movement marker** in the output: `new` → `▲ new`, `rising` → `↑ moved in`, `holding` → `→ no change`, `fading` → `▼ moved out`.

### Step 7: Ring placement

Score each candidate against the role lens (decision leverage, AI depth, durability, force-multiplier, 101-feasibility), then place it on a ring — **every candidate that survives triage gets a blip**, there is no fixed count:

- **Learn** — would start the `/learn` loop this week; production-grade, two-signal evidence. Selective: 3–8 blips typical; past ~8 you are not choosing. Must span ≥3 quadrants (unless a focus filter narrows the scan).
- **Try** — real value, second in queue, or the cheap pass suffices (release notes are the 101).
- **Watch** — tracked with a concrete *promote when:* condition carried from the watchlist.
- **Skip** — deliberately skipped: fading (moved out), contested, or evidence-free hype — with the condition that would move it back in.

Then apply memory:

- fresh already-briefed topics do not get blips (list them as covered in the audit);
- refresh candidates re-enter only when something material changed;
- boost topics that fill a visible gap in the library's coverage.

Tie-breaks favor: production adoption evidence > discussion volume; durable primitives > tools wrapping them; topics that unlock several others.

Items that are **not topics** stay off the radar as one-liners under their quadrant: artifacts of another blip ("the library of #N"), folded angles ("PQC angle lives in #2"), covered-by-brief follow-through, ecosystem signals, off-stack or narrow items.

### Step 8: Output

Save the full report as HTML per [template.html](template.html); show a **compact** version in chat (the HTML is the reading artifact — do not dump the whole report into chat).

**The one-writeup rule (the load-bearing design decision):** every blip appears exactly twice — once on the radar visualization, once as its single writeup card in its quadrant section. There is no "Also on radar" section, no standalone watchlist section, no candidate-pool dump, no separate learn-next strip: those were extra repetitions of the same topics and were removed deliberately. Do not reintroduce them. The Learn ring *is* the learn-next list.

**HTML structure (in order):**

1. **Header + meta line** — window, lens, mode, intake summary, feed health one-liner (`55/55 ok`).
2. **The radar** — the interactive SVG, first thing on the page. The template's script renders it from a `BLIPS` array; the agent's only job is to fill the array (`{n, q, ring, move, name, id}` per blip — numbered continuously, Techniques → Platforms → Tools → L&F) and leave the renderer, `QUADRANTS`, and `RINGS` constants untouched. Blips are click-to-scroll (each `id` anchors its card) with hover tooltips showing the topic name; the legend below explains movement shapes and quadrant colors.
3. **Four quadrant sections** (`h2.qhead` color-matched to the radar) — blips grouped under `h3.ring` subheads in ring order (Learn → Try → Watch → Skip; omit empty rings). Every blip gets one card:
   - **Learn/Try cards** carry 2–4 dated evidence bullets, each one line with **at most one bold number** and its source link inline, then a verdict: Learn = why it wins + effort chip + `/learn` command; Try = the cheaper pass to take now.
   - **Watch cards** carry 1–2 evidence bullets and *promote when:* the concrete condition.
   - **Skip cards** may drop evidence bullets — one-line what-it-is plus why not to spend time and what would move it back in.
   - After the ring groups, a `.notblipped` block: non-topic one-liners ("the artifact of #N", "folded into #2", "covered by YYYY-MM-DD brief", "betas; revisit at GA").
4. **Scan audit** — a collapsed `<details>` block: already-covered dedupe lines (+ refresh candidates only if any exist), watchlist changes (expirations + counters only — promote-when conditions live on the cards), must-not-miss clearance (one line per bucket, referencing blip numbers), coverage (feed health detail, manual sources, wildcards, gate results, next-scan rotation).
5. **All sources** — a second collapsed `<details>` with the full dated list. Every evidence bullet on a card already links its source inline; this list is the complete audit trail.

**Evidence style on cards:** dated bullets, not paragraphs. A 100+-word "Why now" wall with six bold spans is the failure mode this structure replaces — one fact per bullet, one bolded number per bullet at most, link inline where the claim is made.

**Chat version (compact):**

```markdown
# Tech Radar — [YYYY-MM-DD]
**Window** · **Lens**[ · Focus] · **Mode** · intake one-liner · feeds one-liner

## Learn — start now
1. **[Topic]** [quadrant · movement] — one line + strongest dated fact. → /learn "…"
[every Learn blip]

## The rest of the radar
**Try:** [names + numbers] · **Watch:** […] · **Skip:** […]
[One line per ring; movers worth a sentence get one. Point at the HTML for the radar + cards.]

## Notable
[2-4 lines: expired watchlist items, a gate that barely passed, a feed that broke,
a topic recommended repeatedly and skipped. Only what the user should actually react to.]
```

In the saved HTML fill the meta tags: `radar-venues` (manual sources + wildcard queries used, for rotation), `radar-mode`, `radar-intake` (item/keep/drop counts). Save `watchlist.json`. Rebuild the index, print paths.

### Step 9: Hand off

End with: *"Pick a blip number — I'll run the full brief (and lab) on it."* On a pick, invoke the **learn** skill workflow on that topic.

## Principles

- **Why this, why now, why this level — or cut it.** A recommendation that works for any engineer at any time is not a recommendation.
- **Momentum needs two independent, dated signals.** Vendor launch + vendor blog = one signal wearing two hats.
- **Deterministic first, search second.** The registry + crawler make wide coverage free and repeatable; agent searches are for what feeds cannot reach. Adding a source is a registry edit, not a prompt edit.
- **Disposition everything.** Every intake item is a keep or a coded drop; every watchlist item moves or expires visibly. An unexplained absence is a bug, not a judgment call.
- **The library is memory, not decoration.** Recommending something already lab-done wastes the user's time twice.
- **The ring is the verdict.** Watch ≠ Learn: early-stage excitement gets a Watch blip with a promotion condition, never a Learn slot. Ring moves between scans are the signal a static list cannot give.
- **A selective Learn ring beats a crowded one.** No fixed blip count anywhere — but Learn past ~8 items means you stopped choosing. If the window was genuinely quiet, say so and place fewer.
- **No fabricated evidence.** Every why-now point is dated and traceable to a source in the list.
- **Missing a critical topic is worse than over-researching.** The must-not-miss checklist, feed-health fallbacks, and coverage gates exist so a thin pass cannot silently skip protocols, security, or evals.
- **Show the pool — as blips, once each.** A Learn ring without the Watch/Skip context is unauditable, so every surviving candidate gets a blip with a verdict, and non-topics get a one-liner. But each topic appears exactly once as a card — repeating the same topic across also-on-radar, watchlist, and pool-dump sections is how a report becomes unreadable.
- **Whole landscape, not the AI corner.** What an AI-heavy feed diet misses is platforms, techniques, and language movements. Quadrant balance is a gate, not a preference; an unfocused scan that returns only AI failed the sweep.

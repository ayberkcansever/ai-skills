> **Supporting files:** this skill uses `template.html`, `feeds.toml`, and `scripts/scan_feeds.py` shipped in the Cursor variant folder (`learning/cursor/tech-radar/`). Copy them next to wherever you keep this command's assets, or install the Cursor variant alongside and keep the default `~/.cursor/skills/tech-radar/` paths referenced in the text.

# Tech Radar

Goal: answer **"what should I learn next?"** for a principal software + AI engineer — a ranked, evidence-backed shortlist, not a trends listicle. Every recommendation must survive the question: *"why this, why now, and why for someone at this level?"*

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
- Optional mode: **full** (default — everything below) or **quick** ("quick scan", "update the watchlist") — crawl + triage + watchlist update + a short movers summary in chat; no confirm pass, no ranked top 5, no HTML. Quick exists for cheap between-scan refreshes; a top 5 without confirmed evidence would violate the two-signal rule, so quick never ranks.

## Workflow

```
- [ ] Step 1: Load memory — brief library, watchlist, previous scan
- [ ] Step 2: Intake crawl — run the script, read feed health
- [ ] Step 3: Manual sweep — agent-fetched sources + wildcard slice
- [ ] Step 4: Triage — 100% disposition of intake + watchlist
- [ ] Step 5: Confirm evidence, build candidate pool, clear the gates
- [ ] Step 6: Merge watchlist, rank through the role lens
- [ ] Step 7: Output, save HTML, rebuild index, hand off        (quick mode stops after Step 4 + watchlist update)
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

For each keep that could plausibly rank, run **one confirming search** for adoption evidence (`"X in production"`, `"migrating to X"`, `"X postmortem"`, `"X GA"`). Budget: **≤20 confirming searches** — spend them on likely top-10 material, not on obvious also-rans. Total agent search budget per full scan (manual sweep + wildcard + confirm) is roughly **25–35 calls**; the crawl itself costs one command.

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

**Coverage gate:** every erroring feed got its fallback search; every manual feed was covered; ≥3 candidates in the pool come from sources other than the top HN stories (the registry exists so the pool is not just HN's front page). **Quadrant balance gate:** pool holds **≥3 candidates per quadrant** or documents a quadrant as genuinely quiet; without an AI focus filter, at most **half** the pool may be AI-ML and the top 5 must span **≥3 quadrants**. Fail a gate → widen (more manual sources, second wildcard pass) and re-pass. Do not rank until both gates pass.

### Step 6: Watchlist merge

`radar/watchlist.json` holds candidates that did not make a previous top 5 but were too real to discard. Shape:

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

- **promote** — new strong signal this window → joins the candidate pool (and possibly the top 5). Remove from watchlist if it ranks; keep as `rising` if it stays pool-only.
- **hold** — new signal, still not rankable → update `last_signal`, append evidence, status `rising` or `holding`, reset `scans_quiet`.
- **quiet** — no signal this window → `scans_quiet += 1`, status `fading` at 2.
- **expire** — `scans_quiet` reaches 3 → remove; list under "expired" in the scan output (visible, not silent).
- **briefed** — user briefed it since last scan → remove (it lives in the library now).

New this scan: pool candidates that miss the top 5 but have real momentum enter as `status: new`. Every item carries a **movement marker** into the output: `▲ new`, `↑ rising`, `→ holding`, `↓ fading`.

### Step 7: Rank

Score each candidate against the role lens (decision leverage, AI depth, durability, force-multiplier, 101-feasibility). Then apply memory:

- drop fresh already-briefed topics (list them as covered);
- promote refresh candidates only when something material changed;
- boost topics that fill a visible gap in the library's coverage.

Tie-breaks favor: production adoption evidence > discussion volume; durable primitives > tools wrapping them; topics that unlock several others. Honor the quadrant balance gate: ≥3 quadrants in the top 5 unless a focus filter narrows the scan.

### Step 8: Output — use this template

Show in chat (markdown) **and** save as HTML per [template.html](template.html).

```markdown
# Tech Radar — [YYYY-MM-DD]
**Window:** last 3 months · **Lens:** principal software + AI engineer[ · Focus: X] · **Mode:** full
**Intake:** N items from M feeds (F errors) · kept K · dropped: noise A / minor B / marketing C / dup D / junior E

## Learn next (ranked)
### 1. [Topic] — [quadrant · category · ▲/↑/→ movement]
**Why now:** [2-3 dated evidence points from different venues — releases, talks, adoption]
**Why you (principal lens):** [1-2 lines — the decision leverage / force-multiplier angle]
**Effort to 101:** [~half day / day — via brief + lab]
**First step:** run /learn on "[exact topic phrasing]"
[5 entries. Rank 1 = best leverage-per-hour, not loudest hype. ≥3 quadrants unless focused.]

## Also on radar
- **[Topic]** — [quadrant · movement · 1 line: what it is + why watch-not-learn-now]
[5 entries — real candidates that lost on ranking, not filler.]

## Quadrant map
[The whole pool, Thoughtworks-style. Each item: status marker (**learn-now** / *watch*)
+ movement marker (▲ new, ↑ rising, → holding, ↓ fading). A genuinely quiet quadrant
says "quiet this window".]
**Techniques:** [items…]
**Platforms:** [items…]
**Tools:** [items…]
**Languages & Frameworks:** [items…]

## Watchlist
[Every watchlist item after the merge: topic, movement, one line. Expired items listed
last: "expired after 3 quiet scans: X, Y". "Watchlist empty" if so.]

## Already covered (skipped)
[Topics excluded by dedupe, with brief dates. "None — library empty" if so.]

## Refresh candidates
[Stale briefs where the window's events justify an update run. Omit if none.]

## Candidate pool (audit)
[All 15-25 scored candidates, one line each, quadrant-tagged — including losers.
This is how misses get caught on review — do not omit.]

## Must-not-miss clearance
[One line per checklist bucket: candidate name, or "cleared: …".]

## Coverage
[Feed health: "54 feeds ok, langchain-blog error → site: fallback run". Registry fixes
needed, if any. Manual sources hit. Wildcard queries used. This feeds next scan's rotation.]

## Sources
- [YYYY-MM-DD] [venue/title] — [URL]
```

In the saved HTML fill the meta tags: `radar-venues` (manual sources + wildcard queries used, for rotation), `radar-mode`, `radar-intake` (item/keep/drop counts). Save `watchlist.json`. Rebuild the index, print paths.

### Step 9: Hand off

End with: *"Pick a number — I'll run the full brief (and lab) on it."* On a pick, invoke the **learn** skill workflow on that topic.

## Principles

- **Why this, why now, why this level — or cut it.** A recommendation that works for any engineer at any time is not a recommendation.
- **Momentum needs two independent, dated signals.** Vendor launch + vendor blog = one signal wearing two hats.
- **Deterministic first, search second.** The registry + crawler make wide coverage free and repeatable; agent searches are for what feeds cannot reach. Adding a source is a registry edit, not a prompt edit.
- **Disposition everything.** Every intake item is a keep or a coded drop; every watchlist item moves or expires visibly. An unexplained absence is a bug, not a judgment call.
- **The library is memory, not decoration.** Recommending something already lab-done wastes the user's time twice.
- **Watch ≠ learn-now.** Early-stage excitement goes on the watchlist with a promotion condition, not in the top 5.
- **Five real candidates beat ten padded ones.** If the window was genuinely quiet, say so and return fewer.
- **No fabricated evidence.** Every why-now point is dated and traceable to a source in the list.
- **Missing a critical topic is worse than over-researching.** The must-not-miss checklist, feed-health fallbacks, and coverage gates exist so a thin pass cannot silently skip protocols, security, or evals.
- **Show the pool.** The ranked five without the losing candidates is unauditable. Always publish the candidate pool and the triage counts.
- **Whole landscape, not the AI corner.** What an AI-heavy feed diet misses is platforms, techniques, and language movements. Quadrant balance is a gate, not a preference; an unfocused scan that returns only AI failed the sweep.

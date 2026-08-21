---
name: tech-radar
description: Discover what to learn next as a principal software + AI engineer. A deterministic crawler (scripts/scan_feeds.py, driven by feeds.toml) pulls every registry feed — AI labs, cloud/platform, every major language, databases, famous framework releases, production engineering blogs, security, observability, HN gravity plus a sub-threshold HN discovery band, Lobsters, endoflife.date — into a dated intake split into a reviewable set and an auto-dropped set that carries its reason on disk; the agent dispositions 100% of the reviewable set, confirms adoption evidence, merges a calendar-expiring watchlist, then places every candidate on a Thoughtworks-style radar — four quadrants (Techniques / Platforms / Tools / Languages & Frameworks) × four rings (Learn / Try / Watch / Skip — Thoughtworks geometry with learning-native names) rendered as an interactive SVG radar with numbered blips and per-blip writeups — with whole-landscape balance enforced, AI one strand not the default. Dedupes against the user's brief library; the Learn ring is the learn-next answer, each Learn blip runs via the learn skill (/learn). Supports full scans and quick watchlist-update scans. Use when the user asks "what should I learn", "scan the radar", "recent topics worth learning", "what's moving in tech/AI", or wants learning recommendations without naming a topic.
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
feeds.toml               registry: every feed (rss/hn/lobsters/endoflife) + manual entries + crawl settings
scripts/scan_feeds.py    stdlib crawler → reviewable set + drop ledger + feed health
scripts/test_scan_feeds.py  guards the drop rules (python3 scripts/test_scan_feeds.py, no network)
intake/YYYY-MM-DD.*      the windowed crawl: titles view (triage input), JSON (URLs), drops (audit)
feed_health.json         consecutive-error memory, so "broken twice" is a fact not a recollection
watchlist.json           persistent candidates across scans (promote-when conditions, calendar expiry)
```

Editing coverage = editing `feeds.toml`. No skill-text change needed to add or drop a source, or to retune caps, floors, and noise keywords — those live in `[settings]`.

**The crawler pre-drops, the agent judges.** Routine maintenance (patch releases, region expansions, noise keywords) is auto-dropped with a recorded reason, so the agent's disposition budget goes to items that need judgement. Two rules make that safe: anything matching the novelty patterns (announcing / introducing / GA / x.0 / graduated / breaking / deprecated / open-sourced / preview) or the security patterns (CVE, security release, vulnerability, supply-chain) **can never be auto-dropped**, whatever else its title looks like. Those overrides are the reason a `1.0.1` announcement and a `24.5.1` security release still reach triage while an ordinary `24.5.1` does not.

## Storage

```
~/Documents/tech-briefs/radar/YYYY-MM-DD.html    # one file per scan, dated
~/Documents/tech-briefs/radar/intake/            # crawler output (JSON + titles.txt + drops.txt per date)
~/Documents/tech-briefs/radar/feed_health.json   # consecutive-error memory across scans (crawler-owned)
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
- **Cadence:** a full scan is worth running roughly **every 2–4 weeks** against the default 90-day window; the window overlaps deliberately so a topic that was early last month gets a second look. Daily or twice-weekly full scans mostly re-triage the same items — use quick mode for that. Watchlist expiry is date-based, so changing cadence no longer changes how long items survive.
- Optional mode: **full** (default — everything below) or **quick** ("quick scan", "update the watchlist") — crawl + triage + watchlist update + a short new-signals summary in chat; no confirm pass, no ring placement, no HTML. Quick exists for cheap between-scan refreshes; ring placement without confirmed evidence would violate the two-signal rule, so quick never places blips.

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
- **Previous scan**: read the newest file in `~/Documents/tech-briefs/radar/` — its `radar-venues` meta lists which manual sources and wildcard queries were used; prefer different ones this scan. Its `radar-next` meta carries that scan's forward guidance (venues due again, conferences to catch); treat it as this scan's starting plan.
- Empty library → say so and rank purely on the landscape.

### Step 2: Intake crawl

Run the crawler (one command — it is fast, parallel, and free):

```bash
python3 ~/.cursor/skills/tech-radar/scripts/scan_feeds.py
```

It reads [feeds.toml](feeds.toml), fetches every machine-readable feed (AI labs, cloud/platform, all major language blogs, databases, famous framework `releases.atom`, production engineering blogs, security, observability, InfoQ, HN's consensus band plus a sub-threshold discovery band, Lobsters, endoflife.date), window-filters, dedupes, auto-drops routine items with a reason, and writes:

- `radar/intake/<date>.titles.txt` — `index|date|source|flag|title` (**triage reads this**, not the JSON). `flag` is `new` for novelty, `disc` for the HN discovery band, `new+disc` for both, `-` otherwise.
- `radar/intake/<date>.json` — the same items with URLs, plus `auto_dropped`, per-feed health, stats, and the manual-feed list
- `radar/intake/<date>.drops.txt` — `date|source|reason|title` for everything the crawler dropped without asking

Read the crawler's stdout summary, not just the files: it prints the reviewable count, the novelty-flag count, auto-drops by reason, and per-feed `kept/in_window`.

**Feed health rules (non-negotiable):**

- Any feed with `status: error` → run a `site:` fallback search for that source's recent posts in this scan. A broken feed never means silently skipped coverage.
- `REGISTRY FIX NEEDED` in the summary (a feed at **2+ consecutive scans** in error, tracked in `feed_health.json`) → propose a replacement URL in the scan output, and probe for one if quick. This is now a fact the crawler carries between scans, not something the agent has to remember.
- Any feed marked `TRUNCATED` (its in-window item count exceeded `per_feed_cap`) → that feed's coverage was cut mid-window. Run one direct search for its recent posts before claiming full coverage, or raise `per_feed_cap` in `[settings]` if it truncates every scan.
- `empty` is usually fine (quiet feed) — flag only if a normally busy feed goes empty.

### Step 3: Manual sweep

The crawler's summary lists `manual` feeds — sources with no machine-readable feed. The agent covers each with its registry `hint` via `WebSearch`/`WebFetch` (parallel where independent). Currently: Anthropic engineering, MCP blog/SEPs, DeepMind, Shopify/Uber engineering, OWASP GenAI, **CISA KEV catalog** (RSS retired 2025), the latest **Thoughtworks Technology Radar volume** (mine blips + themes — in scope even if published outside the window), in-season **trend surveys** (InfoQ Trends, DORA, StackOverflow, CNCF, State of JS, RedMonk — whichever is fresh), and **conference tracks** in window ±6 weeks (titles + official abstracts are enough for candidacy; never invent talk contents).

Add on top:

- **Discussion gravity**: a Reddit shortlist pass (`r/MachineLearning`, `r/LocalLLaMA`, `r/kubernetes`, `r/aws`, `r/devops`, `r/typescript` — high-upvote, deep comments, as pointers only).
- **Wildcard slice**: 3 open searches, two rotated per scan (recorded in `radar-venues` so the next scan varies them) — e.g. one AI-flavored and one deliberately generic: `"generally available" OR GA (agent OR inference OR gateway) 2026` / `"major release" (platform OR runtime OR database OR framework) 2026`.
- **The unknown-name slot is permanent, not rotated.** Every source in the registry is a name someone already decided to track, so the registry structurally cannot introduce a name nobody knows yet — that is what this slot is for. Keep one search per scan phrased so the answer is a *name you do not have*: `"we're open-sourcing" OR "introducing" (database OR runtime OR framework OR compiler) 2026`, `"switched from" OR "replaced" X with 2026`, `"show HN" (tool OR platform) 2026`. If it returns only names already in `feeds.toml`, rephrase once — a slot that always confirms the registry is not searching.

Do **not** read the workspace (`AGENTS.md`, local stack, employer platform) to bias candidates. This radar is a landscape scan for a principal software + AI engineer, not a personal stack report. Optional focus filters ("AI only", "infra only") are the only narrowing allowed, and only when the user asks.

**Trust rules (apply to every manually fetched source and every confirmation):**

- **Trustable =** primary vendor/project feeds, official standards bodies, established engineering blogs of companies that run things in production, recognized practitioners with a track record, peer venues (HN/Lobsters/major subreddits) *for pointers*, reputable tech press.
- **Never trustable as evidence:** SEO content farms, AI-spun aggregator sites, anonymous listicles, "top 10 tools" affiliate posts. No author + no date + reads like autocomplete = drop.
- **Vendor blogs** are trustable for facts about *their own* releases; superiority claims need independent confirmation.
- **Aggregators/newsletters** seed candidates, never serve as sole evidence.

### Step 4: Triage — 100% disposition

Read the **titles view** (`intake/<date>.titles.txt`) and disposition **every index in it** — nothing falls on the floor silently. The crawler already dispositioned the auto-drops (`drops.txt`), so this step is only the set that needs judgement:

- **keep** → candidate for Step 5 (typically 30–50). Reference items by index.
- **drop** → assign one reason code: `noise` (non-tech / off-lens), `marketing` (launch fluff, no engineering substance), `dup` (same story as a kept item), `junior` (not principal-leverage), `narrow` (single-product or too specific to generalize).

**Write the ledger to disk** at `radar/intake/<date>.triage.json` — a claim of 100% disposition that lives only in prose is unverifiable, and unverifiable discipline decays:

```json
{"generated": "YYYY-MM-DD", "kept": [3, 17, 42],
 "dropped": {"marketing": [1, 8], "dup": [9], "junior": [], "noise": [], "narrow": [22]}}
```

Before moving on, check the arithmetic: `len(kept) + sum(len(v) for v in dropped.values())` must equal the reviewable count the crawler printed, with no index appearing twice. A mismatch means items were skipped — go back and place them.

**Items flagged `new` get named, never bulk-dropped.** A novelty flag is the crawler saying "this is a thing arriving or dying" — exactly what the radar exists to catch. Dropping one is allowed; dropping one without it appearing under a reason code is not. Items flagged `disc` come from the HN discovery band: lower vote counts, so weaker evidence, but this is where a project in its first weeks shows up. Treat them as candidates needing confirmation, not as low-quality items.

Items from the manual sweep join the keeps directly (they were hand-picked, they are already triaged).

Watchlist items get their disposition in Step 6 — but scan the titles for signals matching watchlist topics **now** and tag them while reading.

**Quick mode stops here**: update `watchlist.json` (Step 6's merge rules, using unconfirmed keep signals), report new signals + expiries + feed health in chat, done.

### Step 5: Confirm + candidate pool

Split the surviving keeps into two tiers. **The tiers exist because cost is not evenly distributed** — confirming searches are the expensive step, and only the top two rings need them. Bounding the whole pool would throw away free landscape coverage.

**Contender tier — could plausibly reach Learn or Try.** Run **one confirming search** each for adoption evidence (`"X in production"`, `"migrating to X"`, `"X postmortem"`, `"X GA"`). Aim for **12–18 contenders**; budget **≤20 confirming searches**. Evidence bar: **≥2 independent dated signals from different sources** plus the confirming search. One vendor launch is not momentum.

**Landscape tier — everything else that is a real topic.** No confirming search, so **no cap**: these are placed on Watch or Skip from triage evidence alone. Evidence bar: **≥1 dated signal** and a defensible one-line reason for the ring. A typical full scan lands **25–35 blips total**.

Total agent search budget per full scan (manual sweep + wildcard + confirm) stays roughly **25–35 calls**; the crawl itself costs one command. Growing the landscape tier does not move this number.

**Skip is not a dumping ground.** A Skip blip is a topic you would plausibly hear about and wonder whether to learn — visible buzz that fails the lens. Routine releases, artifacts of another blip, and folded angles are *not* topics and stay as one-liners under their quadrant (see Step 7). If you cannot write a promote-back condition for it, it is not a Skip blip.

For each candidate in either tier, record:

- name + one-line what-it-is;
- **quadrant** (`Techniques`, `Platforms`, `Tools`, `Languages & Frameworks`);
- category (brief-library taxonomy: `AI-ML`, `Infrastructure`, `Data`, `Security`, `Languages-Frameworks`, `DevTools`, `Web`, `Other`);
- **momentum evidence, dated** — to the bar set by its tier above;
- maturity: research / early-adopter / production-adopted;
- which must-not-miss bucket(s) it satisfies.

**Window exception — continuing momentum:** a landmark from 3–6 months ago stays eligible if the window still shows migration posts, GA follow-through, conference tracks, or HN recurrence.

**Must-not-miss checklist (clear every bucket — ≥1 candidate or a one-line "cleared: quiet / not principal-leverage").** Two strands of six, deliberately equal: a checklist that is mostly AI buckets manufactures the AI skew the balance gate then flags, and the agent obediently fills what it is asked for. Six and six means the sweep has to actually look at the rest of the industry.

**AI strand**

1. **Agent/tool protocols** — MCP, A2A, new wire-level agent standards
2. **Agent security threat models** — lethal trifecta / permission-hungry agents / structural mitigations
3. **Evals & release control** — agent evals, online evals, CI gating quality
4. **Inference / serving infra** — Gateway API Inference, vLLM/KServe, AI gateways, GPU scheduling
5. **Coding-agent harnesses & agent state** — Agent Skills, harness engineering, spec-driven workflows, production memory layers (not chat "memory" demos)
6. **Model economics / routing** — multi-tier model strategy, open-weight vs closed tradeoffs

**Non-AI strand**

7. **Platform shifts** — platforms/runtimes shipping majors or GA primitives: K8s/CNCF graduations, edge/serverless, WASM, cloud primitives
8. **Data & storage engines** — database majors, query/analytics engines, open table formats, streaming and CDC
9. **Observability & operations** — OpenTelemetry, eBPF, continuous profiling, incident practice, SRE/DORA findings
10. **Security & supply chain** — CVE-class events with architectural consequences, sigstore/SLSA/SBOM, memory safety, post-quantum migration
11. **Techniques & practices** — architecture patterns and approaches with adoption evidence (Thoughtworks blips/themes, DORA findings, migration writeups)
12. **Languages, frameworks & web platform** — major language releases, framework majors, TC39/std-lib advancements, browser/build-tool primitives, notable deprecations

**Coverage gate:** every erroring feed got its fallback search; every truncated feed got its direct search (or a raised `cap`); every manual feed was covered; the triage ledger's arithmetic balances; every `new`-flagged item is either kept or named under a drop reason; ≥3 candidates in the pool come from sources other than the top HN stories, and **≥1 candidate came from something other than the consensus band** — a `disc`-flagged item, a manual source, or a wildcard hit. That last one is the anti-groupthink check: a radar that only ever surfaces what already has 400 upvotes is a lagging indicator.

**Quadrant balance gate:** pool holds **≥3 candidates per quadrant** or documents a quadrant as genuinely quiet; without an AI focus filter, at most **half** the pool may be AI-ML and the Learn ring must span **≥3 quadrants**.

Fail a gate → widen (more manual sources, second wildcard pass) and re-pass. Do not place blips until both gates pass.

### Step 6: Watchlist merge

`radar/watchlist.json` holds candidates that did not make a previous Learn ring but were too real to discard. Shape:

```json
{
  "updated": "YYYY-MM-DD",
  "items": [
    {
      "topic": "…", "quadrant": "Platforms", "category": "Infrastructure",
      "first_seen": "YYYY-MM-DD", "last_signal": "YYYY-MM-DD",
      "review_after": "YYYY-MM-DD",
      "evidence": [{"d": "YYYY-MM-DD", "src": "feed-id or venue", "u": "URL"}],
      "note": "one line — what it is and what would promote it"
    }
  ]
}
```

Disposition every watchlist item, every scan:

- **promote** — new strong signal this window → joins the candidate pool (and possibly the Learn ring). Remove from watchlist if it reaches Learn; keep it on the watchlist if it stays Try/Watch.
- **hold** — new signal, still not Learn-grade → set `last_signal` to today, append evidence.
- **quiet** — no signal this window → leave `last_signal` untouched. Do not count scans.
- **expire** — quiet for longer than `quiet_expiry_days` in `feeds.toml` `[settings]` (default **21 days**), measured as `today − last_signal`. Remove and list under "expired" in the scan output (visible, not silent).
- **briefed** — user briefed it since last scan → remove (it lives in the library now).

**Expiry is a calendar, never a scan count.** Counting scans means the same topic survives three weeks of daily scanning or nine months of quarterly scanning — the number measures the user's habits, not the topic's momentum. Dates measure the topic.

**`review_after` is the escape hatch for slow conditions.** A promote-when tied to a known future event ("when the 1.36 release lands", "when the CNCF vote happens in November") should not die of the calendar before its condition can possibly fire. Set `review_after` to that date and the item is exempt from expiry until it passes. No `review_after` means the default clock applies — do not add one just to keep a favourite alive.

New this scan: pool candidates below the Learn ring with real momentum enter the watchlist. No movement history is tracked or displayed — blips carry no per-scan markers; the watchlist exists only for promote-when conditions and quiet-scan expiry.

### Step 7: Ring placement

Score each candidate against the role lens (decision leverage, AI depth, durability, force-multiplier, 101-feasibility), then place it on a ring — **every candidate that survives triage gets a blip**, there is no fixed count:

- **Learn** — would start the `/learn` loop this week; production-grade, two-signal evidence plus a confirming search. Selective: 3–8 blips typical; past ~8 you are not choosing. Must span ≥3 quadrants (unless a focus filter narrows the scan).
- **Try** — real value, second in queue, or the cheap pass suffices (release notes are the 101). Contender tier only; 2–6 typical.
- **Watch** — tracked with a concrete *promote when:* condition. Landscape tier lands here. No cap.
- **Skip** — deliberately skipped: fading, contested, or evidence-free hype — with the condition that would move it back in. No cap.

**Rendering headroom.** Blips are spread evenly across 66° of arc per quadrant with an alternating radial offset, so a quadrant×ring cell holds roughly 6 in the Learn band, 12 in Try, 18 in Watch and 24 in Skip before circles touch. The inner rings are the tight ones and they are also the capped ones, so the uncapped tiers cannot crowd the picture. If a single cell would exceed its number, the ring call is probably too generous — tighten it rather than widening the geometry.

Then apply memory:

- fresh already-briefed topics do not get blips (name them in the chat Notable lines);
- refresh candidates re-enter only when something material changed;
- boost topics that fill a visible gap in the library's coverage.

Tie-breaks favor: production adoption evidence > discussion volume; durable primitives > tools wrapping them; topics that unlock several others.

Items that are **not topics** stay off the radar as one-liners under their quadrant: artifacts of another blip ("the library of #N"), folded angles ("PQC angle lives in #2"), covered-by-brief follow-through, ecosystem signals, narrow or single-product items.

### Step 8: Output

Save the full report as HTML per [template.html](template.html); show a **compact** version in chat (the HTML is the reading artifact — do not dump the whole report into chat).

**The one-writeup rule (the load-bearing design decision):** every blip appears exactly twice — once on the radar visualization, once as its single writeup card in its quadrant section. There is no "Also on radar" section, no standalone watchlist section, no candidate-pool dump, no separate learn-next strip: those were extra repetitions of the same topics and were removed deliberately. Do not reintroduce them. The Learn ring *is* the learn-next list.

**HTML structure (in order):**

1. **Masthead — answer first, receipts later.** Eyebrow left, scan date right, then a clean `What to learn next` h1 (no date in the title). Below it ONE human sentence: the window in words, how wide the sweep was, the lens — no counts, no mode, no feed health. Then the **ring-count strip** (`5 Learn / 2 Try / 7 Watch / 6 Skip`), which tells the reader the shape of the scan and doubles as the ring legend, since the radar itself only labels rings in small axis type. Show a `0` rather than dropping a chip. Scan diagnostics never appear up here — a reader opening the report wants the answer, not the plumbing.
2. **The radar** — the interactive SVG, first thing on the page. The template's script renders it from a `BLIPS` array; the agent's only job is to fill the array (`{n, q, ring, name, id}` per blip — numbered continuously, Techniques → Platforms → Tools → L&F) and leave the renderer, `QUADRANTS`, and `RINGS` constants untouched. Blips are click-to-scroll (each `id` anchors its card) with hover tooltips showing the topic name; the corner quadrant labels and the legend below both scroll to their quadrant section.
3. **Four quadrant sections** (`h2.qhead` color-matched to the radar, carrying the fixed ids the radar links to — `q-techniques`, `q-platforms`, `q-tools`, `q-langs`) — each quadrant wrapped in a `section.qsec` and each ring group in a `div.ringgrp`, which is what lets the quadrant and ring headers freeze at the top of the viewport and hand off cleanly on scroll. Blips grouped under `h3.ring` subheads in ring order (Learn → Try → Watch → Skip; omit empty rings). Every blip gets one card:
   - **Learn/Try cards** carry 2–4 dated evidence bullets, each one line with **at most one bold number** and its source link inline, then a verdict: Learn = why it wins; Try = the cheaper pass to take now, with a `span.effort` estimate when it is a real per-topic number. No `/learn` command on cards for now — it is parked until the learn skill is updated, then it comes back. Skip the effort chip when the honest answer is the same for every topic; a constant is not information.
   - **Watch cards** carry 1–2 evidence bullets and *promote when:* the concrete condition.
   - **Skip cards** may drop evidence bullets — one-line what-it-is plus why not to spend time and what would move it back in.
   - After the ring groups, a `.notblipped` block: non-topic one-liners ("the artifact of #N", "folded into #2", "covered by YYYY-MM-DD brief", "betas; revisit at GA").
4. **All sources** — a collapsed `<details>` with the full dated list. Every evidence bullet on a card already links its source inline; this list is the complete audit trail.

**No scan-audit section in the HTML.** The gates still run and the checklist is still cleared — that discipline is not optional — but the receipts are not written into the page: scan parameters, dedupe, watchlist changes, clearance and gate results are reported in chat, and the machine-readable state lives in the `radar-*` meta tags plus `watchlist.json`. Anything the *next* scan needs must go in a meta tag, never only in prose: `radar-venues` for what was used, `radar-next` for forward guidance (venues due again, conferences to catch, wildcards to vary).

**Evidence style on cards:** dated bullets, not paragraphs. A 100+-word "Why now" wall with six bold spans is the failure mode this structure replaces — one fact per bullet, one bolded number per bullet at most, link inline where the claim is made.

**Chat version (compact):**

```markdown
# Tech Radar — [YYYY-MM-DD]
**Window** · **Lens**[ · Focus] · **Mode** · intake one-liner · feeds one-liner

## Learn — start now
1. **[Topic]** [quadrant] — one line + strongest dated fact.
[every Learn blip. No `→ /learn "…"` suffix while the command is parked.]

## The rest of the radar
**Try:** [names + numbers] · **Watch:** […] · **Skip:** […]
[One line per ring; anything worth a sentence gets one. Point at the HTML for the radar + cards.]

## Notable
[2-4 lines: expired watchlist items, a gate that barely passed, a feed that broke,
topics excluded as already briefed, a topic recommended repeatedly and skipped.
The HTML has no audit section, so this is where the receipts surface — but still only
what the user should actually react to, not the full ledger.]
```

In the saved HTML fill the meta tags: `radar-venues` (manual sources + wildcard queries used, for rotation), `radar-next` (forward guidance for the next scan), `radar-mode`, `radar-intake` (item/keep/drop counts). These tags are the only scan memory the page carries, so an unfilled one is lost state. Save `watchlist.json`. Rebuild the index, print paths.

### Step 9: Hand off

End with: *"Pick a blip number — I'll run the full brief (and lab) on it."* On a pick, invoke the **learn** skill workflow on that topic.

## Principles

- **Why this, why now, why this level — or cut it.** A recommendation that works for any engineer at any time is not a recommendation.
- **Momentum needs two independent, dated signals.** Vendor launch + vendor blog = one signal wearing two hats.
- **Deterministic first, search second.** The registry + crawler make wide coverage free and repeatable; agent searches are for what feeds cannot reach. Adding a source is a registry edit, not a prompt edit.
- **Disposition everything, in a file.** Every intake item is a keep or a coded drop — the crawler's auto-drops in `drops.txt`, the agent's in `triage.json`, and the two together account for the whole crawl. An unexplained absence is a bug, not a judgment call, and a ledger that exists only in prose cannot be checked.
- **Rules decay silently; tests do not.** The auto-drop rules are the only place this skill can lose a topic without anyone noticing, so they are covered by `scripts/test_scan_feeds.py`. Change a pattern, run the tests, and add the case that caught you.
- **Measure the topic, not the user's habits.** Anything that ages — watchlist expiry, brief staleness, window edges — ages on the calendar. Scan counters measure how often someone ran the tool, which is not evidence about anything.
- **The registry cannot discover a name it does not contain.** Feeds cover known sources exhaustively and unknown ones not at all; the HN discovery band and the permanent unknown-name wildcard exist to cover that blind spot. Never let both lapse in the same scan.
- **The library is memory, not decoration.** Recommending something already lab-done wastes the user's time twice.
- **The ring is the verdict.** Watch ≠ Learn: early-stage excitement gets a Watch blip with a promotion condition, never a Learn slot.
- **A selective Learn ring beats a crowded one.** No fixed blip count anywhere — but Learn past ~8 items means you stopped choosing. If the window was genuinely quiet, say so and place fewer.
- **No fabricated evidence.** Every why-now point is dated and traceable to a source in the list.
- **Missing a critical topic is worse than over-researching.** The must-not-miss checklist, feed-health fallbacks, and coverage gates exist so a thin pass cannot silently skip protocols, security, or evals.
- **Show the pool — as blips, once each.** A Learn ring without the Watch/Skip context is unauditable, so every surviving candidate gets a blip with a verdict, and non-topics get a one-liner. But each topic appears exactly once as a card — repeating the same topic across also-on-radar, watchlist, and pool-dump sections is how a report becomes unreadable.
- **Whole landscape, not the AI corner.** What an AI-heavy feed diet misses is platforms, techniques, and language movements. Quadrant balance is a gate, not a preference; an unfocused scan that returns only AI failed the sweep.

# Workflow — memory, crawl, sweep, triage, watchlist, rings

Contents:

- Step 1: Load memory
- Step 2: Intake crawl
- Step 3: Manual sweep
- Step 4: Triage (100% disposition)
- Step 6: Watchlist merge
- Step 7: Ring placement (full mode only)

Step 5 (confirm + gates) lives in [gates.md](gates.md). Step 8–9 (HTML + chat) live in [output.md](output.md).

Quick mode: Steps 1–4, then Step 6 using unconfirmed keep signals, then a short new-signals summary in chat. Stop. No gates.md, no output.md, no HTML.

## Step 1: Load memory

Read `~/Documents/tech-briefs/` before anything else:

- List existing briefs: topic, `brief-date`, `brief-verdict`, `brief-poc` (meta tags in each HTML).
- **Already briefed and fresh** → excluded from recommendations; name them in chat Notable so the user sees dedupe worked.
- **Briefed but stale** (>180 days) or verdict was "Hold — revisit when X" and X may have happened → eligible again, flagged *refresh* not *new*.
- **Lab done** topics = strong areas — use them to spot *gaps* (lots of agent-framework briefs, nothing on serving → inference economics ranks up).
- **Watchlist**: read `radar/watchlist.json` — every item must be dispositioned this scan (Step 6). Missing file = first scan, start empty.
- **Previous scan**: newest file in `~/Documents/tech-briefs/radar/` — `radar-venues` meta lists last manual sources + wildcard queries; prefer different ones. `radar-next` is this scan's starting plan.
- Empty library → say so and rank purely on the landscape.

Do **not** read the workspace (`AGENTS.md`, local stack, employer platform) to bias candidates. Focus filters only when the user asked.

## Step 2: Intake crawl

```bash
python3 ~/.cursor/skills/tech-radar/scripts/scan_feeds.py
```

Window override: add `--window N`. Output dir defaults to `~/Documents/tech-briefs/radar`.

Reads `feeds.toml`. Writes:

- `radar/intake/<date>.titles.txt` — `index|date|source|flag|title` (**triage reads this**, not the JSON). `flag` is `new` (novelty), `disc` (HN discovery band), `new+disc`, or `-`.
- `radar/intake/<date>.json` — same items with URLs, plus `auto_dropped`, per-feed health, stats, `manual` list
- `radar/intake/<date>.drops.txt` — `date|source|reason|title`

Read stdout, not just the files: reviewable count, novelty-flag count, auto-drops by reason, per-feed `kept/in_window`, the `manual` block.

**Exit codes:**

- `2` — registry unreadable. Stop. Do not invent coverage.
- `1` — >50% of fetchable feeds errored. Continue, but every erroring feed is owed a `site:` fallback this scan; say so in chat.
- `0` — continue. Still honor the feed-health rules below for any individual error/truncation.

**Feed health (non-negotiable):**

- `status: error` → `site:` fallback search for that source's recent posts. A broken feed is never silently skipped.
- `REGISTRY FIX NEEDED` (2+ consecutive errors in `feed_health.json`) → propose a replacement URL; probe for one if quick.
- `TRUNCATED` (in-window count exceeded `per_feed_cap`) → one direct search for that publisher, or raise that feed's `cap` in `[settings]` if it truncates every scan.
- `empty` is usually fine — flag only if a normally busy feed goes quiet.

## Step 3: Manual sweep

Cover **every `manual` row the crawler printed**, using that row's `hint`. Do not use a remembered list — the registry is the source of truth (DeepMind-as-manual already drifted once). Parallel `WebSearch`/`WebFetch` where independent.

On top of the printed manual list:

- **Discussion gravity**: Reddit shortlist (`r/MachineLearning`, `r/LocalLLaMA`, `r/kubernetes`, `r/aws`, `r/devops`, `r/typescript` — high-upvote, deep comments, as pointers only).
- **Wildcard slice**: 3 open searches, two rotated per scan (record in `radar-venues`). One AI-flavored, one generic. Use the **scan date's year**, never a hardcoded year. Examples: `"generally available" OR GA (agent OR inference OR gateway) YEAR` / `"major release" (platform OR runtime OR database OR framework) YEAR`.
- **Unknown-name slot is permanent, not rotated.** One search phrased so the answer is a *name you do not have*: `"we're open-sourcing" OR "introducing" (database OR runtime OR framework OR compiler) YEAR`, `"switched from" OR "replaced" X with YEAR`, `"show HN" (tool OR platform) YEAR`. If it returns only names already in `feeds.toml`, rephrase once.

**Trust rules** (every manual fetch and every later confirmation):

- Trustable: primary vendor/project feeds, standards bodies, engineering blogs of companies that run production, recognized practitioners, peer venues (HN/Lobsters/major subreddits) *for pointers*, reputable tech press.
- Never evidence: SEO farms, AI-spun aggregators, anonymous listicles, affiliate "top 10" posts. No author + no date + reads like autocomplete = drop.
- Vendor blogs: facts about *their own* releases. Superiority claims need independent confirmation.
- Aggregators/newsletters seed candidates; never sole evidence.

Manual-sweep picks join the keep set directly (already triaged).

## Step 4: Triage — 100% disposition

Read `intake/<date>.titles.txt`. Disposition **every index**. Auto-drops are already in `drops.txt`.

- **keep** → candidate for Step 5 (typically 30–50). Reference by index.
- **drop** → one reason code: `noise` (non-tech / off-lens), `marketing` (launch fluff), `dup` (same story as a kept item), `junior` (not principal-leverage), `narrow` (single-product / too specific).

Write `radar/intake/<date>.triage.json`:

```json
{"generated": "YYYY-MM-DD", "kept": [3, 17, 42],
 "dropped": {"marketing": [1, 8], "dup": [9], "junior": [], "noise": [], "narrow": [22]}}
```

Then run:

```bash
python3 ~/.cursor/skills/tech-radar/scripts/validate_triage.py \
  --intake ~/Documents/tech-briefs/radar/intake/YYYY-MM-DD.json \
  --triage ~/Documents/tech-briefs/radar/intake/YYYY-MM-DD.triage.json
```

Exit 0 required. A mismatch means skipped indexes — go back and place them. Do not proceed on a failed validator.

**`new`-flagged items get named, never bulk-dropped.** Dropping one is allowed; dropping one without it appearing under a reason code is not. `disc` items are candidates needing confirmation, not low-quality junk.

While reading titles, tag signals that match current watchlist topics.

**Quick mode stops after Step 6** (watchlist merge on unconfirmed keeps). Report new signals + expiries + feed health in chat. Done.

## Step 6: Watchlist merge

`radar/watchlist.json` — candidates that missed Learn but were too real to discard:

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

Disposition every item, every scan:

- **promote** — new strong signal → candidate pool (and possibly Learn). Remove from watchlist if it reaches Learn; keep if it stays Try/Watch.
- **hold** — new signal, still not Learn-grade → `last_signal` = today, append evidence.
- **quiet** — no signal → leave `last_signal` untouched. Do not count scans.
- **expire** — quiet longer than `quiet_expiry_days` in `feeds.toml` `[settings]` (default **90**, matched to `window_days` so a quiet item survives the 2–4 week cadence), measured as `today − last_signal`. Remove and list under "expired" in chat (visible, not silent).
- **briefed** — user briefed it since last scan → remove.

Expiry is a calendar, never a scan count. Dates measure the topic.

**`review_after`** exempts an item until a known future event can fire ("when 1.36 lands", "when the CNCF vote happens"). No `review_after` means the default clock. Do not add one just to keep a favourite alive.

New this scan: pool candidates below Learn with real momentum enter the watchlist. No per-scan movement markers on blips.

## Step 7: Ring placement (full mode)

Score against the role lens, then place — **every candidate that survives triage gets a blip**, no fixed count:

- **Learn** — would start `/learn` this week; two-signal evidence plus a confirming search. 3–8 typical; past ~8 you stopped choosing. Must span ≥3 quadrants unless a focus filter narrows the scan.
- **Try** — real value, second in queue, or the cheap pass is the whole 101. Contender tier only; 2–6 typical.
- **Watch** — *promote when:* concrete condition. Landscape tier lands here. No cap.
- **Skip** — fading, contested, or evidence-free hype, plus the condition that would move it back. No cap.

**Rendering headroom.** 66° of arc per quadrant, alternating radial offset. A quadrant×ring cell holds roughly 6 Learn / 12 Try / 18 Watch / 24 Skip before circles touch. If a cell would exceed that, the ring call is too generous — tighten it, do not widen the geometry.

Then apply memory:

- fresh already-briefed topics do not get blips (name them in chat Notable);
- refresh candidates re-enter only when something material changed;
- boost topics that fill a visible library gap.

Tie-breaks: production adoption > discussion volume; durable primitives > tools wrapping them; topics that unlock several others.

Items that are **not topics** stay off the radar as one-liners under their quadrant: artifacts of another blip, folded angles, covered-by-brief follow-through, ecosystem signals, narrow/single-product items.

Continue to [output.md](output.md).

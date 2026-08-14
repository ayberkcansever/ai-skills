---
name: learning-radar
description: Discover what to learn next as a principal software + AI engineer. Scans wide but trustable — a two-tier venue map: Core every scan (pinned change-feeds MCP/Anthropic/OpenAI/Google/AWS/CNCF/K8s/Cloudflare/LangChain, conference calendars, HN/Reddit gravity, Thoughtworks radar, arXiv crossover, security feeds) plus a rotating Extended net (big-tech + production eng blogs, InfoQ/New Stack/ACM Queue, trend surveys like DORA/StackOverflow/AI Index, newsletters as seeds, GitHub trending, standards bodies, talks) — last ~3 months — then ranks candidates through a principal-engineer lens, dedupes against the user's brief library, and outputs a top-5 learn-next list with dated evidence. Each pick runs via tech-radar-brief. Use when the user asks "what should I learn", "scan the radar", "recent topics worth learning", "what's moving in tech/AI", or wants learning recommendations without naming a topic.
---

# Learning Radar

Goal: answer **"what should I learn next?"** for a principal software + AI engineer — a ranked, evidence-backed shortlist, not a trends listicle. Every recommendation must survive the question: *"why this, why now, and why for someone at this level?"*

This skill finds the topics; the sibling **tech-radar-brief** skill (`~/.cursor/skills/tech-radar-brief/`) learns them (brief → learn path → lab → quiz). The two share one library: briefs produced there are this skill's memory, and this skill's output is that skill's input queue.

## The role lens

All ranking happens through this lens. It is the skill's identity — apply it ruthlessly.

A principal software + AI engineer needs topics that provide:

- **Decision leverage** — things that change architecture choices, build-vs-buy calls, platform bets, or how you review others' designs. Not "another framework that renders lists".
- **AI engineering depth** — the moving frontier: agent architectures, LLM serving/inference economics, evals and reliability, retrieval, model routing, AI-adjacent infra. Signal over demos.
- **Durability** — likely to still matter in 2 years. A hot repo with no production adoption is a *watch*, not a *learn-now*.
- **Force-multiplier potential** — knowledge that upgrades how the whole team works (tooling, patterns, platform capabilities), not just personal trivia.
- **101-feasibility** — learnable to a correct 101 in roughly a day via the tech-radar-brief loop. If a topic needs a semester, recommend its learnable entry slice instead.

Explicitly out of scope: junior-level fundamentals, certification chasing, single-vendor feature announcements dressed as trends, and anything whose only evidence is marketing.

Optional per-run focus narrows the lens ("AI only", "infra only", "what should I learn for the next quarter") — but the level stays principal.

## Storage

```
~/Documents/tech-briefs/radar/YYYY-MM-DD.html   # one file per scan, dated
~/Documents/tech-briefs/index.html               # library index links to the latest scan
```

- `mkdir -p ~/Documents/tech-briefs/radar` before writing.
- One scan record per date: a same-day re-scan **updates that day's file in place** (merge new findings, refresh the `radar-venues` tag); a new day gets a new file. Never create `YYYY-MM-DD-2.html` variants — the index and rotation logic assume date-named files.
- Fill the `radar-*` `<meta>` tags in [template.html](template.html).
- **Rebuild the library index after every save**: `python3 ~/.cursor/skills/tech-radar-brief/scripts/build_index.py` — it links the newest scan in the header.
- Print the saved path plus `open ~/Documents/tech-briefs/radar/<date>.html`.

## Inputs

- None required.
- Optional: focus filter ("AI only", "infra/platform only"), window override (default **3 months** — discovery needs a tighter window than a deep brief), "include topics I already briefed" to disable dedupe.

## Workflow

```
- [ ] Step 1: Load memory — inventory the brief library
- [ ] Step 2: Landscape sweep, recency-bounded (~3 months)
- [ ] Step 3: Build candidate pool (15-25), evidence-tagged
- [ ] Step 4: Rank through the role lens, dedupe against memory
- [ ] Step 5: Output top 5 + also-on-radar, save HTML, rebuild index
- [ ] Step 6: Offer to run tech-radar-brief on a pick
```

### Step 1: Load memory

Read `~/Documents/tech-briefs/` before searching:

- List existing briefs: topic, `brief-date`, `brief-verdict`, `brief-poc` status (meta tags in each HTML).
- **Already briefed and fresh** → excluded from recommendations; listed in the scan's "already covered" line so the user sees the dedupe worked.
- **Briefed but stale** (>180 days) or verdict was "Hold — revisit when X" and X may have happened → eligible again, flagged as *refresh* rather than *new*.
- **Lab done** topics indicate the user's strong areas — use them to spot *gaps* (e.g. lots of agent-framework briefs, nothing on serving/inference → inference economics ranks up).
- **Previous scan's venue rotation**: read the newest file in `~/Documents/tech-briefs/radar/` and its `radar-venues` meta tag — this scan prefers Extended venues *not* on that list.
- Empty library → say so and rank purely on the landscape.

### Step 2: Landscape sweep

Use `WebSearch` + `WebFetch`, parallel where independent, window = last ~3 months. The scan's value is its **width** — but width from trustable sources only. The venue map has two tiers: **Core** (every scan, non-negotiable) and **Extended** (wide net, rotated across scans so successive scans cover different ground). Prefer **pinned URLs / site: queries** over open-ended googling; open search is for confirmation and gap-fill only.

#### Trust rules (apply to every source, both tiers)

- **Trustable =** primary vendor/project feeds, official standards bodies, established engineering blogs of companies that run things in production, recognized practitioners with a track record, peer venues (HN/Lobsters/major subreddits) *for pointers*, and reputable tech press.
- **Never trustable as evidence:** SEO content farms, AI-spun summary/aggregator sites, anonymous listicles, "top 10 tools" affiliate posts. If a page has no author, no date, and reads like autocomplete — drop it.
- **Vendor blogs** are trustable for facts about *their own* releases; claims of superiority need independent confirmation.
- **Aggregators/digests/newsletters** are candidate *seeders*, never sole evidence — every seed gets a primary or practitioner confirmation.

#### CORE venues — every scan, all of them

**C1. Pinned primary change-feeds** (where durable topics ship; hit each at least once):

| Feed | How |
|------|-----|
| MCP blog / SEPs | `site:blog.modelcontextprotocol.io` + spec repo releases |
| Anthropic Engineering | `site:anthropic.com/engineering` |
| OpenAI blog / cookbook | `site:openai.com/blog` OR `site:openai.com/index` |
| Google AI / Developers blog | `site:developers.googleblog.com` + `site:blog.google/technology/ai` |
| AWS ML / Architecture blogs | `site:aws.amazon.com/blogs/machine-learning` + `site:aws.amazon.com/blogs/architecture` |
| Kubernetes blog + CNCF announcements | `site:kubernetes.io/blog` + `site:cncf.io/announcements` |
| Cloudflare blog (edge/AI/MCP) | `site:blog.cloudflare.com` |
| LangChain / LangGraph blog | `site:blog.langchain.com` (stack-adjacent for this user) |

Plus one omnibus query: `"generally available" OR GA OR "release notes" (agent OR MCP OR inference OR gateway) 2026`.

**C2. Conference calendar** (events in window or ±6 weeks — fetch track lists / "key themes" writeups):

- **Cloud/infra:** KubeCon + CloudNativeCon (EU + NA), AWS re:Invent, Google Cloud Next, Microsoft Build
- **AI industry:** NeurIPS / ICML industry tracks, AI Engineer World's Fair, Databricks Data+AI Summit
- **Language/platform:** PyCon, JSConf/Node events, systems conferences if active

Titles + official abstracts are enough for candidacy. Do not invent talk contents.

**C3. Discussion gravity:** HN (`site:news.ycombinator.com`, recurrence > spikes), Lobsters (`site:lobste.rs`), Reddit shortlist (`r/MachineLearning`, `r/LocalLLaMA`, `r/kubernetes`, `r/aws`, `r/LangChain`, `r/typescript`, `r/devops` — high-upvote, deep comments), Simon Willison (`site:simonwillison.net`).

**C4. Curated radar:** latest Thoughtworks Technology Radar volume (PDF — mine blips + themes, always in scope even if published outside window).

**C5. Research crossover:** arXiv `cs.AI` / `cs.LG` / `cs.SE` / `cs.CR` — only with a second adoption signal. Paper alone = watch.

**C6. Security feeds:** Willison (prompt injection / trifecta), Trail of Bits, OWASP (LLM / agentic security Top 10 updates), cloud-vendor AI security posts, agent threat-model pattern catalogs.

#### EXTENDED venues — wide net, rotated at the source level

Eight venue *classes* (E1–E8), each containing many individual sources. Per scan: hit **≥8 individual Extended sources spanning ≥5 classes**. Rotation happens at the **source** level, not the class level — Netflix this scan, Shopify the next; E2 as a class can appear every scan. Record which sources were hit in the scan output; the next scan reads the previous scan's list and prefers sources not recently covered. A focus filter ("AI only") biases the pick toward that slice; a must-not-miss bucket with no candidate forces the matching Extended class into this scan regardless of rotation.

**E1. Big-tech & lab engineering blogs:** Meta AI + Engineering (`engineering.fb.com`), Microsoft / Azure AI blog, DeepMind blog, Mistral, Hugging Face blog (+ daily papers page), NVIDIA Developer blog, Vercel blog, GitHub blog/changelog.

**E2. Production engineering blogs (war stories, postmortems, migrations):** Netflix TechBlog, Uber Engineering, Stripe Engineering, Shopify Engineering, Airbnb Engineering, Discord Engineering, Slack Engineering, Grab/DoorDash Engineering, Pinterest Engineering, Canva Engineering. This is where "X in production" evidence lives — one migration writeup outranks five launch posts.

**E3. Quality tech press & analysis:** InfoQ (news + minibooks), The New Stack, ACM Queue, IEEE Spectrum (AI section), The Register (skeptical takes), Ars Technica. Funding/market moves: TechCrunch / The Information headlines as Tier-3 signal only.

**E4. Trend reports & surveys (each has a season — check which is fresh):** InfoQ Trends Reports (AI/ML, architecture, culture — quarterly-ish), DORA / State of DevOps, Stack Overflow Developer Survey, JetBrains Developer Ecosystem, State of JS / State of CSS, CNCF Annual Survey, Stanford HAI AI Index, RedMonk language rankings, Deloitte/McKinsey State of AI.

**E5. Newsletters & podcasts as seed lists (confirm elsewhere, always):** Pragmatic Engineer (Gergely Orosz), ByteByteGo, Import AI (Jack Clark), Latent Space (blog + pod), TLDR / TLDR AI, The Batch, Last Week in AWS (Corey Quinn), Changelog, Thoughtworks Technology Podcast, Kubernetes Podcast. Show notes and issue archives are fetchable even when audio is not.

**E6. Code-level signal:** GitHub Trending (by relevant language/topic), release velocity on protocol/reference repos (dated Releases + adoption mentions, not vanity stars), Papers with Code trending, npm/PyPI download inflections when checkable.

**E7. Standards & governance (beyond core):** TC39 stage advancements, WHATWG/W3C when web-platform relevant, IETF (AI-agent or transport relevant drafts), Linux Foundation AI & Data / Agentic AI project graduations, NIST AI RMF updates, EU AI Act implementation milestones (compliance = principal-level concern).

**E8. YouTube / talks (signal only):** conference channel uploads (KubeCon, AWS Events, Anthropic, GOTO, InfoQ). Speaker/venue/date/title = momentum evidence. **No fake transcripts** — a talk without a write-up is a pointer, not a summary source.

#### Search tactics

- Always include the current year; date-restrict where the engine allows.
- Prefer `site:` queries from the tables above over generic keywords.
- If a direct fetch of a pinned feed fails (403/paywall/JS-only page), fall back to a `site:` search for that feed's recent posts — a failed fetch does not excuse skipping the feed.
- For each promising candidate: one confirming search for adoption evidence (`"X in production"`, `"migrating to X"`, `"X postmortem"`, `"X GA"`).
- Run venue classes **in parallel** (multiple WebSearch/WebFetch per message). Budget roughly **30–60 tool calls** per full scan: all Core classes + ≥8 Extended sources. Under budget with a thin pool = under-scanned; widen before ranking.
- **Rotation memory:** the scan output lists venues covered (`Venues covered` section + `radar-venues` meta tag). Read the previous scan's list first; prefer Extended venues not hit last time.

**Window exceptions (anti-miss):**
- **Latest curated radar** (Thoughtworks Technology Radar, etc.) is in scope even if published just outside the 3-month window — radars are semi-annual; skip them and you miss a whole theme set. Fetch the PDF/HTML and mine **blips + themes**, not only the press release.
- **Continuing momentum**: a landmark from 3–6 months ago stays eligible if the window still has migration posts, GA follow-through, conference tracks, or HN recurrence. Example: a March GA still discussed at an August KubeCon schedule reveal.

**Must-not-miss checklist (run every scan).** Before closing the candidate pool, explicitly clear each bucket — either with ≥1 candidate or a one-line "cleared: quiet / not principal-leverage":

1. **Agent/tool protocols** — MCP, A2A, and any new wire-level agent standards
2. **Agent security threat models** — lethal trifecta / permission-hungry agents / structural mitigations (not vendor WAF ads)
3. **Evals & release control** — agent evals, online evals, CI gating quality
4. **Inference / serving infra** — Gateway API Inference, vLLM/KServe, AI gateways, GPU scheduling
5. **Coding-agent harnesses** — Agent Skills, harness engineering, spec-driven agent workflows
6. **Agent memory / state** — production memory layers, not chat "memory" product demos
7. **Model economics / routing** — multi-tier model strategy, open-weight vs closed cost/latency tradeoffs
8. **Stack-adjacent** — if the user's known stack is visible (workspace AGENTS.md, recent briefs, or stated role context like AWS/Bedrock/LangGraph/TypeScript/Python), force at least one search keyed to that stack's recent releases (e.g. `Bedrock AgentCore 2026`, `LangGraph 2026`)

**Venue coverage gate:** every Core class (C1–C6) must contribute ≥1 candidate or get a documented second-pass search; at least **8 individual Extended sources spanning ≥5 classes** must have been hit this scan, and at least **3 candidates** in the pool must come from Extended sources that Core did not surface (that is the point of the wide net — if Extended only echoes Core, rotate to different sources and re-pass). Do not rank until the gate passes.

### Step 3: Candidate pool

Collect **15-25 candidates** before ranking anything — ranking from a pool of six is a coin flip with extra steps. For each candidate record:

- name + one-line what-it-is;
- category (same taxonomy as the brief library: `AI-ML`, `Infrastructure`, `Data`, `Security`, `Languages-Frameworks`, `DevTools`, `Web`, `Other`);
- **momentum evidence, dated** — at least 2 independent signals from different venue classes above. One vendor launch is not momentum;
- maturity: research / early-adopter / production-adopted;
- which must-not-miss bucket(s) it satisfies.

If the pool is under 15 after the checklist, widen searches (more conferences, more site-scoped HN, next Thoughtworks ring) rather than ranking a thin set.

### Step 4: Rank

Score each candidate against the role lens (decision leverage, AI depth, durability, force-multiplier, 101-feasibility). Then apply memory:

- drop fresh already-briefed topics (list them as covered);
- promote refresh candidates only when something material changed;
- boost topics that fill a visible gap in the library's coverage.

Tie-breaks favor: production adoption evidence > discussion volume; durable primitives > tools wrapping them; topics that unlock several others.

### Step 5: Output — use this template

Show in chat (markdown) **and** save as HTML per [template.html](template.html).

```markdown
# Learning Radar — [YYYY-MM-DD]
**Window:** last 3 months · **Lens:** principal software + AI engineer[ · Focus: X]

## Learn next (ranked)
### 1. [Topic] — [category]
**Why now:** [2-3 dated evidence points from different venues — releases, talks, adoption]
**Why you (principal lens):** [1-2 lines — the decision leverage / force-multiplier angle]
**Effort to 101:** [~half day / day — via brief + lab]
**First step:** run tech-radar-brief on "[exact topic phrasing]"
[5 entries. Rank 1 = best leverage-per-hour, not loudest hype.]

## Also on radar
- **[Topic]** — [1 line: what it is + why it's watch-not-learn-now]
[5 entries — real candidates that lost on ranking, not filler.]

## Already covered (skipped)
[Topics from your library excluded by dedupe, with brief dates. "None — library empty" if so.]

## Refresh candidates
[Stale briefs where the window's events justify an update run. Omit section if none.]

## Candidate pool (audit)
[List all 15-25 scored candidates in one line each, including those that lost. This is how misses get caught on review — do not omit.]

## Must-not-miss clearance
[One line per checklist bucket: candidate name, or "cleared: …".]

## Venues covered
[Core: C1–C6 confirmation. Extended: list the E-venues hit this scan (e.g. "E1 Meta/HF, E2 Netflix/Stripe, E3 InfoQ, E4 DORA, E5 Pragmatic Engineer, E6 GitHub trending, E7 TC39, E8 KubeCon talks"). This feeds the next scan's rotation.]

## Sources
- [YYYY-MM-DD] [venue/title] — [URL]
```

In the saved HTML, mirror the Extended-venue list into the `radar-venues` meta tag (comma-separated, e.g. `E1:meta+hf, E2:netflix+stripe, E3:infoq, …`) so the next scan can rotate.

After saving: rebuild the index, print paths.

### Step 6: Hand off

End with: *"Pick a number — I'll run the full brief (and lab) on it."* On a pick, invoke the **tech-radar-brief** skill workflow on that topic.

## Principles

- **Why this, why now, why this level — or cut it.** A recommendation that works for any engineer at any time is not a recommendation.
- **Momentum needs two independent, dated signals.** Vendor launch + vendor blog = one signal wearing two hats.
- **The library is memory, not decoration.** Recommending something already lab-done wastes the user's time twice.
- **Watch ≠ learn-now.** Early-stage excitement goes in "also on radar" with a reason, not in the top 5.
- **Five real candidates beat ten padded ones.** If the window was genuinely quiet, say so and return fewer.
- **No fabricated evidence.** Every why-now point is dated and traceable to a source in the list.
- **Missing a critical topic is worse than over-researching.** The must-not-miss checklist and venue coverage gate exist so a thin Google pass cannot silently skip protocols, security, or evals.
- **Pinned feeds beat open search.** If a change-feed URL is in the venue map, hit it. Generic "AI trends 2026" queries are gap-fill, not the spine of the scan.
- **Wide, but trustable — and rotated.** The scan's value is its width; width without the trust rules is SEO sludge, and width without rotation is the same 10 sites every time. Core every scan, Extended rotated, every source vetted.
- **Show the pool.** The ranked five without the losing candidates is unauditable. Always publish the candidate pool.

---
name: tech-radar-brief
description: Learn a tech topic to a correct 101 level in minimal time. Researches open sources (official docs/releases, engineering blogs, YouTube talks, HN/Reddit, news, papers) restricted to recent material, then produces a brief with a 101 mental model, what changed, tradeoffs, an adopt/trial/hold/avoid verdict, a time-budgeted learn-it-fast resource path, adjacent topics, and a proposed ~1h hands-on PoC lab (scaffolded on request; the user implements the core parts, then gets quizzed for retention). Use when the user asks to research, learn, get up to speed on, "give me a brief/report on", or wants a hands-on PoC/lab/quiz for a technology, tool, framework, protocol, model, or engineering trend.
---

# Tech Radar Brief

Goal: take a tech topic and get the user to a **correct 101 level in minimal time** — a working mental model, the current state of play, and real hands-on muscle. Not expert depth; expert-*shaped* fundamentals. Recent material only. Every claim dated and sourced.

Written for a senior engineer who ships production systems: bias toward how-to-think-about-it, maturity, and tradeoffs over feature lists and launch hype. The output must survive two tests: (a) a tech lead could make an adopt/trial/hold/avoid call from it, and (b) after the lab + quiz, the user can explain the topic's core mechanism in their own words without being wrong.

## The learning loop

The skill delivers learning in escalating, optional stages — each stage is skippable, but the order is fixed:

```
1. Brief          ~10 min read   → mental model + state of play + verdict
2. Learn-it-fast  ≤ half day     → 3-5 curated resources, time-budgeted, in order
3. Lab            ~1 hour        → user implements core parts, agent removes friction
4. Quiz           ~10 min        → retrieval practice; wrong answers corrected with sources
```

Stage 1 always happens. Stages 2-3-4 are offers the user takes or leaves. Muscle comes from 3 and 4; the brief alone is recognition-level knowledge, and the skill should say so when offering the lab.

**Topic discovery:** when the user doesn't have a topic and asks "what should I learn?", that is the sibling **learning-radar** skill (`~/.cursor/skills/learning-radar/`) — it scans the recent landscape, dedupes against this library, and hands ranked topics back to this skill.

## Storage

Every brief is **saved to disk automatically** as a self-contained HTML file, never into the current repo/cwd:

```
~/Documents/tech-briefs/<Category>/<topic-slug>.html
~/Documents/tech-briefs/index.html          # auto-generated landing page
~/Documents/tech-briefs/poc/<topic-slug>/   # guided PoC lab, only when the user says go
```

- **Category** — exactly one, best fit from this fixed list: `AI-ML`, `Infrastructure`, `Data`, `Security`, `Languages-Frameworks`, `DevTools`, `Web`, `Other`. Folder name verbatim.
- **Tags** — 2-5 free-form topic tags (`agents, langgraph, orchestration`). One category folder, but the index surfaces the brief under every tag.
- Slugify topic (lowercase, hyphens): "Model Context Protocol" → `model-context-protocol.html`. Prefer the full name over an acronym for the slug; put the acronym in tags.
- `mkdir -p ~/Documents/tech-briefs/<Category>` before writing.
- Fill the `brief-*` `<meta>` tags in [template.html](template.html) — the index builder reads them.
- `brief-poc` on first save: `proposed` when PoC suitability is *good fit* or *partial*, `none` when *not practical*. The lab lifecycle later bumps it to `scaffolded` → `completed` (Step 6).
- **Rebuild the index after every save**: `python3 ~/.cursor/skills/tech-radar-brief/scripts/build_index.py`
- Print the saved path plus `open ~/Documents/tech-briefs/<Category>/<topic-slug>.html` and mention `open ~/Documents/tech-briefs/index.html`.

### Re-running a topic

Before researching, check whether a brief already exists (search **all** category folders for the slug):

- **Exists** → this is an *update run*, not a rewrite. Research only what changed **since the existing brief's `brief-date`**. Append a new dated `<section class="update">` block at the top of the body content (newest first), leave the original brief intact below it, and bump the `brief-date` / `brief-verdict` meta tags. Say in chat that you updated an existing brief and what moved. Also re-check the PoC section: if a lab was scaffolded and the window's changes would break or outdate it (API changes, renamed concepts), say so explicitly; if suitability changed, update it.
- **Does not exist** → normal full run.
- Never silently fork a near-duplicate file. If recategorizing, move (don't copy).

## Inputs

- Required: the topic.
- Optional overrides: recency window (`--last 3m`), depth (`tight` / `medium` / `deep`), angle (builder / strategy), focus question ("is it ready for prod Lambda workloads?").
- Defaults: **6-month window**, **medium** depth (~2 pages), **tech-lead** angle.

## Workflow

```
- [ ] Step 1: Scope the topic (disambiguate, set window, check for existing brief)
- [ ] Step 2: Multi-source sweep, recency-bounded
- [ ] Step 3: Synthesize — dedupe, date-check, separate signal from vendor marketing
- [ ] Step 4: Output brief in template + save HTML + rebuild index
- [ ] Step 5: Recommend 3-5 adjacent topics, offer to run one
- [ ] Step 6: Assess PoC suitability + propose a ~1h lab; scaffold on go, review, quiz, mark completed
```

### Step 1: Scope

- Disambiguate ambiguous names before burning searches (MCP = Model Context Protocol or Microsoft Certified Professional? Bun = runtime or the package manager story?). One quick `WebSearch` to pin it down; ask the user only if still ambiguous.
- Fix the window explicitly: default = **today minus 6 months**. State the actual date range in the brief header.
- Check `~/Documents/tech-briefs/` for an existing brief on this slug (update run vs. full run).

### Step 2: Multi-source sweep

Use `WebSearch` + `WebFetch`. Hit **every tier below** — a brief built from one tier is not a brief, it is a blog post. Run searches in parallel where independent.

**Tier 1 — Primary (highest trust).** Official docs, release notes, changelogs, RFCs/specs, GitHub releases and issues, vendor status/deprecation notices. This is where "what actually shipped" lives.

**Tier 2 — Practitioner.** Engineering blogs from teams running it in production, conference talks, YouTube deep-dives, HN and Reddit threads with substantive comments (not the headline — the comments). This is where "what breaks in production" lives.

**Tier 3 — Press & market.** Tech news, funding, acquisitions, adoption/market moves. Useful for trajectory, weak for technical truth.

**Tier 4 — Research.** arXiv / papers / benchmarks when the topic has an academic core. Note whether benchmarks are vendor-run.

Search tactics:
- Add the current year to queries; search engines otherwise surface 2-3 year old SEO pages.
- Use site-scoped searches for high-signal venues: `site:news.ycombinator.com`, `site:github.com <repo> releases`, `site:reddit.com/r/<sub>`.
- For YouTube: search for conference talks and deep-dives by name. **Constraint to respect** — fetching a watch URL usually yields title/description only, not a transcript. So report the talk (speaker, venue, date, why it matters) rather than pretending to summarize its contents. If a transcript or written write-up of the talk exists, use that and say so. Never invent what a video said.

Recency rules:
- **Hard rule: every item in the brief carries a date.** No date findable → either drop it or explicitly mark `(undated)`.
- Older-than-window material is allowed **only** as background needed to make the recent news legible, and must be labeled `Background:`.
- If the topic has genuinely no activity in the window, say that outright — "quiet for 6 months" is a real and useful finding, not a failed research run.

### Step 3: Synthesize

- Cross-check load-bearing claims against ≥2 independent sources. Single-sourced → mark it.
- **Discount vendor marketing.** A vendor blog announcing its own product's superiority is Tier 3 evidence at best. Prefer independent reproduction, third-party benchmarks, and production war stories.
- Separate *announced* from *shipped* from *stable*. Preview/beta/GA is a load-bearing distinction for an adopt decision.
- Collapse duplicate coverage — ten outlets rewriting one press release is one data point.
- Contradictions between credible sources are content, not a problem: surface the disagreement.

### Step 4: Output and save — use this template

Show the brief in chat (markdown) **and** write identical content as HTML per [template.html](template.html).

```markdown
# [Topic] — Tech Brief
**Window:** [YYYY-MM-DD] → [YYYY-MM-DD] · **Generated:** [date]

## TLDR
- [most important thing a tech lead needs to know]
- [second]
- [third]

## Verdict: [Adopt | Trial | Hold | Avoid] · confidence [high | medium | low]
[2-4 sentences: the call, the single strongest reason for it, and what would flip it.
Name the condition that changes the verdict — "flips to Trial once X ships GA".]

## State of play
[What it is in 2-3 sentences, assuming a smart engineer who has not touched it.
Then maturity: version, GA/beta, who runs it in production, how big the ecosystem is.]

## Mental model (101)
**Problem it solves:** [1-2 sentences — what hurt before this existed, and for whom.]
**How it works:** [3-5 sentences on the core mechanism. The test: after reading, the user
can predict how the thing behaves in a case the brief never mentions.]
**Vocabulary:** [4-8 terms you must know to read the docs — official terminology only,
each with a half-line definition. This is the map from "heard of it" to "can read about it".]
- **[term]** — [definition]
**Misconceptions:** [1-3 wrong beliefs a newcomer typically picks up from headlines or
outdated tutorials, each corrected in one line. Only include real, observed confusions.]

## What changed in the window
- **[YYYY-MM]** [event — release, spec change, funding, deprecation, notable adoption] — [why it matters, 1 line]
[Reverse-chronological. 5-10 items. Every one dated. This section is the point of the brief.]

## Key players & ecosystem
- **[Project/company]** — [role, and their actual position: leader, fast follower, fading]
[3-6 entries. Include the credible alternative approaches, not only the topic itself.]

## Tradeoffs
**Strong at:** [where it genuinely wins]
**Weak / risky:** [failure modes, operational cost, lock-in, missing pieces, immature tooling]
**Unknown:** [what nobody can answer yet]

## Learn it fast
[3-5 resources, **in consumption order**, each with a time budget and one line on what it
uniquely delivers. Total ≤ half a day. Rules: current-version material only (a great 2023
tutorial for a rewritten API is a trap — that is where wrong 101 knowledge comes from);
prefer official quickstarts and primary-author talks; every entry says *why this one*,
never a link dump.]
1. **[~20 min]** [Resource title + URL] — [what it delivers that the others don't]
[If the topic is well served by less, list less. Padding a learning path wastes the exact
thing this skill exists to save.]

## Adjacent topics to explore
1. **[Topic]** — [1 line on why it connects and what it would unlock]
[3-5 topics.]

## Hands-on PoC
**Suitability:** [good fit | partial | not practical] — [why, 1 line]
**Proposed lab (~1h):** [what you would build and which 2-3 core concepts the exercises force you to touch]
[If a lab is already scaffolded: `Lab: ~/Documents/tech-briefs/poc/<topic-slug>/ — start with LAB.md`]

## Sources
- [YYYY-MM-DD] [Source name / title] — [URL] *(tier 1-4)*
[Dated, tiered. List what was actually used.]
```

Depth tuning:
- `tight`: TLDR + Verdict + Mental model + What changed + Sources. ~1 page. (Mental model survives every cut — it is the learning payload.)
- `medium` (default): template as-is.
- `deep`: add code/config samples, benchmark numbers with methodology caveats, migration notes, and a longer timeline.

Angle overrides (default is tech-lead):
- `builder`: expand Tradeoffs into "how to actually use it", add setup/code, thin out market content.
- `strategy`: expand Key players into adoption curve, funding, and vendor risk; thin out implementation detail.

### Step 5: Adjacent topics

End the chat response with the 3-5 adjacent topics and offer to run one immediately:
*"Want a brief on any of these? Say the number."*

Pick adjacent topics that a tech lead evaluating this one would plausibly need next — competing approaches, the layer above/below in the stack, the operational concern it creates (cost, security, observability). Not generic "related buzzwords".

### Step 6: Hands-on PoC (guided lab)

The point: the user learns by implementing, so **the user writes the core code, not the agent**. The agent removes the boring friction (setup, boilerplate, verification) and leaves the learning in.

**Suitability check (goes in every brief).** A topic is:
- **good fit** — runnable locally or on a free tier within ~1h: libraries, frameworks, protocols, CLIs, databases, file formats, most cloud services with local emulators.
- **partial** — hands-on possible but only for a slice (e.g. paid API with a free trial, hardware topic with a simulator). Say which slice.
- **not practical** — hardware-gated, enterprise-license-only, org/process topics (team topologies, pricing trends), pure research with no runnable artifact. Say why; recommend the closest runnable neighbor instead.

**Trigger.** The brief always contains the suitability verdict and a one-line proposed lab. **Do not scaffold during the brief run.** End the chat response with: *"Say 'scaffold the lab' to get hands dirty."* Scaffold only on explicit go (or when the user opens with `--poc` / "PoC on X").

**Prereq check — before scaffolding anything.** Verify the user's machine can run the lab: check required runtimes/tools and versions (`node --version`, `python3 --version`, `docker info`, whatever the lab needs). Missing prereq → either adapt the lab to what is installed, or tell the user the one install command needed and wait. A lab that dies on setup teaches only frustration.

**Scaffold — on go, create:**

```
~/Documents/tech-briefs/poc/<topic-slug>/
  LAB.md            # the lab itself — goal, prereqs, exercises, checkpoints, self-check
  NOTES.md          # user's own-words notes, one block per exercise (retrieval practice)
  README.md         # 3 lines: what this is, link to the brief, how to start
  ...project files  # deps manifest, config, boilerplate, skeleton code
```

Scaffolding rules:
- **Time-box ~1 hour total**: setup ≤10 min (verify with a smoke command before handing over), then 3-6 exercises escalating from "make it respond" to one genuinely non-trivial concept. 101 level — one topic pillar done properly beats five skimmed.
- **Every exercise carries a minute budget** (`Exercise 2 (~15 min)`). Budgets honest, not aspirational; if an exercise realistically needs 30 min, it is two exercises.
- **Exercises map to the mental model.** Each exercise exists to make one concept from the brief's Mental model section physical. A fun exercise that teaches nothing from the model is scope creep — cut it.
- Optional **stretch exercise** at the end, clearly marked, outside the 1h budget, for when appetite exceeds the time-box.
- Agent writes: dependency manifest, project config, entry-point boilerplate, test harness / verification scripts, sample data.
- User writes: the core logic. Mark every gap with a `TODO(you): ...` comment stating *what* to implement and *which exercise* it belongs to — never how.
- Each exercise in `LAB.md` has: **Goal** (1 line), **Where** (file + TODO marker), **Done when** (a concrete command to run and the exact observable output/behavior), and **Concept** (which mental-model concept this makes physical).
- `NOTES.md` is pre-seeded with one heading per exercise and the prompt: *"After the exercise passes, write 2-3 sentences in your own words: what did the code you wrote actually do, and why does it work?"* This is the retrieval practice that turns doing into knowing — the skill's whole point. The review loop reads it.
- `LAB.md` ends with a **Self-check** block: 5 questions the user should answer from memory after finishing. Questions target the mental model and the exercises, not trivia. **No answers in the file** — closing line: *"Ask me to quiz you."*
- Pin dependency versions to what current docs support; the lab must not break on install.
- Never scaffold into a work repo or the cwd — always `~/Documents/tech-briefs/poc/<topic-slug>/`. Fresh folder; if one already exists for the slug, ask before touching it.
- No solution code anywhere in the scaffold. When the user is stuck: hint first (point at the relevant doc/concept), fuller hint second, full solution only on explicit request.
- After scaffolding, update the brief's `brief-poc` meta tag to `scaffolded` (from `proposed`) and rebuild the index — the card gets a lab chip.

**Review loop.** When the user says "review my lab" / "check exercise N": read their code **and their `NOTES.md`**, run the verification commands, then respond with:
- what works and what's wrong (file:line);
- **corrections to the notes** — if an own-words explanation is wrong or fuzzy, fix the understanding, not just the code. Passing code with a wrong explanation is the failure mode this skill exists to prevent;
- one thing they did better than the obvious approach — if true. No praise padding.

**Quiz — on "quiz me" (or after a full lab review passes, offer it).** Ask the Self-check questions from `LAB.md` **one at a time**, wait for the answer, then grade honestly: right / partially right / wrong, with the correction grounded in the brief or primary docs — never vibes. Add 1-2 transfer questions not in the file (novel scenario, same concepts) to test the model rather than memory of the lab. Score at the end. A wrong answer is the most valuable output of the whole loop — say what the misconception was, plainly.

**Completion.** When all exercise verifications pass and the quiz is done (or explicitly skipped), set the brief's `brief-poc` meta tag to `completed` and rebuild the index — the card's chip flips to "lab done". That chip is the muscle tracker: library shows what was read vs. what was actually learned.

## Principles

- **Correct and narrow beats broad and fuzzy.** 101 means the fundamentals are *right*, not that everything got mentioned. One concept the user can reason with outweighs five they can recite.
- **Time is the budget.** Every stage carries an honest time cost and earns it. Padding a brief, a learning path, or a lab wastes the exact resource this skill exists to save.
- **Explaining it back is the test.** Passing verification commands proves the code works; `NOTES.md` and the quiz prove the *user* works. Both, or the loop is not done.
- **Decision-grade or don't ship it.** If the brief does not help someone choose, it is a Wikipedia article.
- **Dates are non-negotiable.** An undated claim in a recency-scoped brief is a bug.
- **Announced ≠ shipped ≠ stable.** Keep the three apart, always.
- **Hype gets discounted, production reports get weighted.** One team's postmortem outweighs five launch posts.
- **No fabrication.** No invented benchmarks, quotes, versions, or video contents. Thin evidence gets said out loud: "little independent verification yet".
- **Honest verdicts.** "Hold — too early, revisit after the 2.0 spec lands" is a better answer than manufactured enthusiasm.
- **The user's hands get dirty, not the agent's.** In a lab, agent-written core logic is a failed lab. Friction removed, learning kept.
- **Wrong answers are gold.** A quiz miss caught today is a production mistake avoided later. Grade honestly, correct with sources, never soften.

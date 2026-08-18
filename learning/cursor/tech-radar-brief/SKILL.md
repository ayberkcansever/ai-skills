---
name: tech-radar-brief
description: Learn a tech topic to a correct 101 level in minimal time. Researches open sources (official docs/releases, engineering blogs, YouTube talks, HN/Reddit, news, papers) restricted to recent material, then produces a brief with a 101 mental model, what changed, tradeoffs, an adopt/trial/hold/avoid verdict, a time-budgeted learn-it-fast resource path, adjacent topics, and a proposed hands-on PoC lab (scaffolded on request; code ships complete, the user predicts, runs, observes and explains back, then gets quizzed for retention). Use when the user asks to research, learn, get up to speed on, "give me a brief/report on", or wants a hands-on PoC/lab/quiz for a technology, tool, framework, protocol, model, or engineering trend.
---

# Tech Radar Brief

Goal: take a tech topic and get the user to a **correct 101 level in minimal time** — a working mental model, the current state of play, and real hands-on muscle. Not expert depth; expert-*shaped* fundamentals. Recent material only. Every claim dated and sourced.

Written for a senior engineer who ships production systems: bias toward how-to-think-about-it, maturity, and tradeoffs over feature lists and launch hype. The output must survive two tests: (a) a tech lead could make an adopt/trial/hold/avoid call from it, and (b) after the lab + quiz, the user can explain the topic's core mechanism in their own words without being wrong.

## The learning loop

The skill delivers learning in escalating, optional stages — each stage is skippable, but the order is fixed:

```
1. Brief          ~10 min read   → mental model + state of play + verdict
2. Learn-it-fast  ≤ half day     → 3-5 curated resources, time-budgeted, in order
3. Lab            ~1-1.5 hours   → agent ships working code; user predicts, runs, explains
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

`poc/<topic-slug>/` is a **code workspace**, not a document — it holds dependency manifests, virtualenvs, and scratch output. Two consequences: every scaffold ships a `.gitignore` covering the environment dirs and any local secrets file (`.venv/`, `node_modules/`, `__pycache__/`, `.env`) so credentials and binaries never land in the briefs tree, and the index builder ignores `poc/` — labs are surfaced through their brief's `brief-poc` chip, never as index entries of their own.

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
- [ ] Step 6: Assess PoC suitability + propose a ~1-1.5h lab; scaffold on go, review, quiz, mark completed
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
**What you walk through (~[N] min):** [one sentence — the working thing the lab demonstrates,
then the env switches that drive its failure demos, e.g. `BREAK_AGENT=1` plants a routing bug]
**Concepts it makes physical:** [2-3 named concepts from the Mental model section]

**Setup (~10 min)**
- Prereqs: [runtimes, accounts, keys — name the exact versions/tiers]
- Install: [the literal command(s)]
- Smoke check: [one command + the output that proves setup worked]

**Steps**
1. **[~12 min] [Step name]** — [the literal command]. Watch for: [the exact output that appears
   and what it proves]. Counterfactual: [the second command showing what breaks if built the
   other way, and the number it produces].
[4-6 steps, escalating from "make it respond" to one genuinely non-trivial concept. Every step
carries an honest minute budget, one command to run, and a checkable watch-for. Write them so a
reader could follow them without the agent — plain imperative sentences, no framework jargon left
undefined, no step that silently contains three.]

**Stretch (optional, outside the budget):** [one harder extension]

[Rules for this section: every step is *run and observe* — the scaffold ships all the code
working, so a step names a command and the output worth watching, never code for the reader to
write. These brief steps are the summary; `LAB.html` expands each into the full seven-slot
anatomy (Step 6). Prefer one tool the reader installs once over a menu of options. If suitability
is *not practical*, replace Setup/Steps with one line naming the closest runnable neighbour.]
[If a lab is already scaffolded: `Lab: ~/Documents/tech-briefs/poc/<topic-slug>/ — open LAB.html`]

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

### Step 6: Hands-on PoC (guided walkthrough lab)

The point: the user learns by **predicting, running, observing, and explaining back — not by writing code**. The agent ships the lab fully implemented and verified end to end; the user's job per step is to commit to a prediction, run one command, compare, and say in their own words why the output came out that way. The learning pressure lives in the predictions, `NOTES.html`, and the quiz — never in typing code.

**Suitability check (goes in every brief).** A topic is:
- **good fit** — runnable locally or on a free tier inside the time-box: libraries, frameworks, protocols, CLIs, databases, file formats, most cloud services with local emulators.
- **partial** — hands-on possible but only for a slice (e.g. paid API with a free trial, hardware topic with a simulator). Say which slice.
- **not practical** — hardware-gated, enterprise-license-only, org/process topics (team topologies, pricing trends), pure research with no runnable artifact. Say why; recommend the closest runnable neighbor instead.

**Trigger.** The brief always contains the suitability verdict, the setup block, and the numbered steps — enough that a reader can follow the walkthrough by hand without ever scaffolding. **Do not scaffold during the brief run.** End the chat response with: *"Say 'scaffold the lab' to get the runnable walkthrough."* Scaffold only on explicit go (or when the user opens with `--poc` / "PoC on X").

**Prereq check — before scaffolding anything.** Verify the user's machine can run the lab: check required runtimes/tools and versions (`node --version`, `python3 --version`, `docker info`, whatever the lab needs). Never print the value of an environment variable to test for a credential — check presence only. Missing prereq → either adapt the lab to what is installed, or tell the user the one install command needed and wait. A lab that dies on setup teaches only frustration.

**Credentials are a prereq like any other.** If the lab needs a paid API key the user does not have, prefer a scaffold that runs offline by default — a local stub standing in for the paid call — with a documented one-line switch to the real provider. Say plainly in `LAB.html` which parts the stub does and does not faithfully reproduce. Never make the first run of a lab depend on the user going to find a key.

**Default LLM provider for labs: Google AI Studio** (`GOOGLE_API_KEY`, generativelanguage endpoint or `ChatGoogleGenerativeAI`) — the user has a key for it and it is the first provider a scaffold should try. Write the key into the lab's gitignored `.env` only; never into `LAB.html`, the brief, a committed config, or this skill. Keep the stub fallback anyway so the lab still runs if the key is revoked.

**Scaffold — on go, create:**

```
~/Documents/tech-briefs/poc/<topic-slug>/
  LAB.html          # the walkthrough — orientation, setup, run-and-observe steps, recap card, self-check
  NOTES.html        # user's own-words notes, one block per step (retrieval practice)
  README.html       # what this is, link to the brief, how to start
  ...project files  # complete, working, verified code — nothing left as an exercise
```

**Lab docs are HTML, not Markdown** — same reading experience as the brief, opened in the browser next to it. Build them from [lab-template.html](lab-template.html) and [notes-template.html](notes-template.html); both are self-contained (inline CSS matching the brief palette, no build step, no CDN). Every lab doc links back to its brief with a relative path (`../../<Category>/<topic-slug>.html`) and across to its siblings. Code files, `.env`, and dependency manifests stay plain — this rule is about the docs only.

**Build order — do not write `LAB.html` first.** The doc quotes verified output and reveals verified prediction answers, so it can only be written *after* the runs exist. Work in this order:

```
1. Code       → all project files complete, including the counterfactual switches/anti-pattern files
2. Verify     → run every step command AND every counterfactual, with the exact strings the lab will print;
                capture the real output and the true answer to each prediction question
3. Calibrate  → if a payoff depended on luck (a flap that did not flap, two estimates disagreeing by noise),
                fix the demo — better sample, more rounds, or an invariant derived from the samples — and re-run
4. Write      → LAB.html from lab-template.html, NOTES.html from notes-template.html, README.html
5. Clean      → delete state the verification created (baselines, caches); leave first-run moments to the user
6. Publish    → brief's POC steps + brief-poc meta → scaffolded, rebuild the index
```

Step 3 is the one agents skip. A demo that teaches only when the sampling cooperates will fail for the user on the run that matters — see the *deterministic payoff* rule below.

Scaffolding rules:
- **`LAB.html` opens with orientation, before setup.** Without a map, step 1 lands as an unexplained file name. A required **The big picture** section carries four things: what the system under test is and why it is deliberately small (so the reader stops evaluating it and starts evaluating the machinery around it); the single question the whole lab answers, in bold; the pipeline diagram; and the arc as an `ol.arc` — one line per step, title in bold, then what it establishes and earns for the next ("step 3 shows why the judge cannot block; step 4 fixes it"). Never present the arc as a prose paragraph — five steps woven into running text is unscannable. Follow with a short file map, one clause per file, saying which part of the diagram each belongs to. A reader who stops after this section should still be able to describe the design.
- **Diagrams are styled HTML, never ASCII art in a `<pre>`.** ASCII overflows into a horizontal scrollbar, breaks on narrow windows, and looks like a placeholder. Use the `.lanes` component from the template: one row per pipeline stage — trigger chip, name, its question in italics, a timing chip, and a colour-coded authority badge (`blocks` red / `reports` amber / `informs` blue). The recap card reuses the same rows with `.lanes.small`.
- **No meta-sections that do not teach.** The opening block is *How to use this lab*, 2-3 sentences, not a manifesto about the step anatomy — the anatomy shows itself. Provider/credential notes and the stub fallback are one `p.note` inside Setup, not a standalone callout. Env switches are introduced by the steps that use them and listed once in the recap card; never enumerate them up front, before the reader knows what any of them would break.
- **The brief's numbered steps are the walkthrough, 1:1** — same order, same budgets, same watch-fors and counterfactuals. The brief carries the one-line summary of each step; `LAB.html` carries the full seven slots. Deviate only when the prereq check forces it, and say so.
- **All code ships complete and verified.** Before handing over, the agent runs every step's command and confirms the documented output actually appears — including the failure demos and every counterfactual. Any number in an Observe block or a revealed prediction comes from a run the agent actually made; an unverified prediction answer is fabrication of the worst kind, because the reader commits to a guess before seeing it.
- **Verify with the exact command string the lab prints, not an equivalent.** `python -m pytest` puts the cwd on `sys.path`; bare `pytest` does not — an equivalent-looking command can pass for the agent and fail for the user (fix: `pythonpath = .` in `pytest.ini`). Same trap: activated venv vs `./.venv/bin/...`, exported env vars vs inline ones.
- **Every gate needs a controlled failure.** A lab that only shows green teaches nothing — build in env-flag switches (e.g. `BREAK_AGENT=1`, `AGENT_FLAKE=0.2`) that plant a bug or inject unreliability so the user watches the gate go red without editing any file. Off by default; each switch is introduced by the step that uses it and listed once in the recap card.
- **Time-box ~1-1.5 hours total**: setup ≤10 min (verify with a smoke command before handing over), then 3-6 steps escalating from "make it respond" to one genuinely non-trivial concept. The seven-slot anatomy costs ~12 min per step — budget honestly and cut steps rather than thinning slots. 101 level — one topic pillar done properly beats five skimmed.
- **Every step carries a minute budget.** Budgets honest, not aspirational; if a step realistically needs 30 min, it is two steps.
- **Steps map to the mental model.** Each step exists to make one concept from the brief's Mental model section physical. A fun step that teaches nothing from the model is scope creep — cut it.
- Optional **stretch step** at the end, clearly marked, outside the time-box, for when appetite exceeds it.
- **Every step in `LAB.html` uses the same seven slots, in this order.** Each is a `<li>` in `ol.steps` with the budget as a `.budget` chip; slots render as `.step-label` blocks. Uniform shape is what makes the lab skimmable and the concepts comparable across steps:
  1. **Question it answers** — one line, phrased as a question, directly under the title. Gives the reader a slot to file the answer into.
  2. **Code that matters** — 5-15 lines inline in a `pre.src` with a `.srcpath` citation (`file.py:29-30`) and one sentence of framing. Never "go skim this file": the point is no context switch, and the excerpt makes clear which lines carry the idea.
  3. **Predict** — the question as a visible `p.predict-q`, then a `details.predict` revealing the verified answer plus *why the tempting wrong answer is tempting*. This is the load-bearing slot. Good predictions have a non-obvious answer the step's output settles unambiguously ("how many of the five fail, and why not all five?"). Bad ones are yes/no or restate the concept. No input widgets — a guess box was tried and rejected as friction; the reveal is enough.
  4. **Run** — the literal command(s) in a `pre`.
  5. **Observe** — a `pre.out` with the real output from the verified run, trimmed to the lines that matter.
  6. **Why it happened** — a `ul.chain` of 3-5 causal links, each `<li>` tracing one code or design fact to the output fact it produced, with the load-bearing phrase in bold. Never a prose paragraph: a wall of prose in the explanation slot is where readers skim, and a chain is scannable on the second pass. The derivation, not the slogan — this is where the concept is taught rather than named.
  7. **What breaks otherwise** — the counterfactual, as a runnable command wherever one flag can produce it, with its verified numbers. Knowing what fails the other way is what separates understanding a design from having watched it work.
  Close each step with a `details.takeaway-d` — summary *"Takeaway — say yours in one sentence first, then compare"*, body holding the transferable rule. Collapsed, not printed: reading a polished summary feels like learning, producing one is learning. Mirror the same line as the step's concept in `NOTES.html` and in the recap card.

  A filled example of the shape, abridged from the agent-evaluation lab:

  > **Lane 1 — the deterministic gate** `~12 min`
  > *Question:* why can this check block a merge when a judge score cannot?
  > *Code that matters:* `called = [c["tool"] for c in result["tool_calls"]]; assert called == golden["expected_tools"]` — `tests/test_deterministic.py:29-30`, no model or threshold anywhere in the file.
  > *Predict:* "`BREAK_AGENT=1` re-routes visitor questions to the sales tool. Five goldens run — how many fail, and why not all five?" → reveals: three; two goldens already targeted sales, so the bug is invisible on 40% of the suite, which is really a lesson about golden-set coverage.
  > *Run:* `pytest -q tests/test_deterministic.py`, then the same with `BREAK_AGENT=1`.
  > *Observe:* `5 passed in 0.01s` → `3 failed, 2 passed`, message naming expected vs actual trajectory.
  > *Why (a chain, one causal link per line):* the flag forces the metric before routing → visitor goldens diverge at index 0 while sales goldens match; no API in the loop → same verdict on every machine, and the 0.01s runtime is what earns a place in the blocking path.
  > *What breaks otherwise:* `REWORD_ANSWER=1` on the text-matching test file — 5 failed there while the trajectory test stays 5 passed. A false block on unchanged behaviour.
  > *Takeaway:* blocking checks must be deterministic **and** assert on behaviour rather than presentation.

  Note what the prediction does there: the tempting answer (five) is wrong for a reason the step then makes visible, so the miss teaches the real lesson. Predictions with obvious answers are decoration.
- **Counterfactuals are switches, not prose.** Ship the anti-pattern alongside the pattern — a `REWORD_ANSWER=1` flag, a deliberately brittle test file, a `--gate` mode — so the reader watches the wrong design fail rather than reading that it would. Mark anti-pattern files unmistakably in their docstring so they are never mistaken for the recommended lane.
- **Nondeterministic outputs get a deterministic payoff.** When a step's interesting behavior is stochastic (LLM scores, injected flakiness), never let the lesson depend on the run being lucky. Derive something invariant from the samples and print that — a flap window ("any floor in (0.5, 1.0] flips this verdict"), a spread, a measured rate over many rounds — then hedge the raw numbers and tell the reader theirs will differ. A step whose point appears only half the time is a broken step.
- **Interleave retrieval; do not let a concept be met once.** A lab read straight through is a single pass, and single-pass material does not survive the week. From step 3 onward, open roughly every other step with a `details.recall` posing one question about an *earlier* step, answered from memory before the new one starts ("under `BREAK_AGENT` two goldens still passed — why, and what does that say about golden sets?"). Retrieval at a delay is worth more than any amount of re-reading, and it costs a minute.
- **End with a recap card, and make it stand alone.** Nobody re-reads a 30 KB walkthrough to refresh a topic months later, so the lab must produce one screen that survives on its own: the pipeline diagram again, every step's takeaway as a numbered list, the *contrasts* the topic is built from as an instead-of / use / because table, what each env switch proves with its verified number, and a short glossary of the terms needed to read the real docs. Most topics are a handful of contrasts — pairs learned as pairs stick far better than halves learned separately, and the card is where they finally sit side by side.
- **Give big numbers a felt scale.** `0.01s` and `~50s` read as two facts; "a factor of 5000 — run the judge on every push and you add minutes to each PR" reads as a design constraint. Whenever a step turns on a magnitude, say what the magnitude means for someone operating the system.
- **`LAB.html` ends with a Self-check block: 5-6 questions answered from memory**, targeting the mental model and what the steps showed, not trivia. The last one is a **transfer question** — same concepts, a domain the lab never touched ("you are gating a RAG pipeline instead — what plays the role of the trajectory?"). Questions about the lab test memory of the lab; only transfer tests whether the mental model came along.
- **Every self-check question carries a brief answer behind a reveal.** 2-3 verified sentences in a `details.recall` inside the `<li>` — months later the reader opens the file with no chat session running, and a question they cannot verify is a question they skip. The closing note says to answer aloud first and offers the chat quiz as the deeper interrogation; "no answers in this file" was tried and is friction, not rigor.
- **Notes discipline lives in the *How to use* block, not a section of its own.** One sentence — write 2-3 own-words sentences in `NOTES.html` after each step, plus any missed prediction. A standalone section after the recap card arrives after the reader needed it.
- **Per-step progress checkboxes.** `LAB.html` carries a `data-done` checkbox per step persisted to `localStorage` under `lab-progress:<slug>:<n>`, with a counter and a reset button. Labs now span more than one sitting; resuming should not mean re-reading.
- `NOTES.html` is pre-seeded with one `section.note-block` per step — heading, the step's takeaway and counterfactual as its concept line, and an empty `textarea` — under the prompt: *"After each step, write 2-3 sentences in your own words: what did the output demonstrate, and why did it come out that way? If your prediction missed, write what you expected and what corrected it."* Prediction misses are the highest-value notes in the file; ask for them explicitly.
- **Notes live in browser localStorage, so the agent cannot read them.** `NOTES.html` autosaves as the user types and offers *Copy as Markdown* / *Download .md*. When starting a review, ask the user to paste the copied notes (or point at the downloaded `.md`) — never assume the notes are on disk.
- Pin dependency versions to what current docs support; the lab must not break on install.
- Never scaffold into a work repo or the cwd — always `~/Documents/tech-briefs/poc/<topic-slug>/`. Fresh folder; if one already exists for the slug, ask before touching it.
- **Leave the scaffold pristine for the user's first run.** Delete any state files the verification runs created (baselines, caches, downloaded artifacts) so first-run moments — "baseline written", first smoke check — happen for the user, not the agent.
- After scaffolding, update the brief's `brief-poc` meta tag to `scaffolded` (from `proposed`) and rebuild the index — the card gets a lab chip.

**Review loop.** When the user says "review my lab" / "check step N": ask them to paste their notes from `NOTES.html`, then respond with:
- **corrections to the notes** — if an own-words explanation is wrong or fuzzy, fix the understanding. Watched output with a wrong explanation is the failure mode this skill exists to prevent;
- if they report output that differs from the documented watch-for, re-run the step yourself and explain the difference (stochastic spread vs. an actual break);
- one connection they made beyond the lab's framing — if true. No praise padding.

**Quiz — on "quiz me" (or after a full lab review passes, offer it).** Ask the Self-check questions from `LAB.html` **one at a time**, wait for the answer, then grade honestly: right / partially right / wrong, with the correction grounded in the brief or primary docs — never vibes. Add 1-2 transfer questions not in the file (novel scenario, same concepts) to test the model rather than memory of the lab. Score at the end. A wrong answer is the most valuable output of the whole loop — say what the misconception was, plainly.

**Completion.** When the user has walked every step and the quiz is done (or explicitly skipped), set the brief's `brief-poc` meta tag to `completed` and rebuild the index — the card's chip flips to "lab done". That chip is the muscle tracker: library shows what was read vs. what was actually learned.

## Principles

- **Correct and narrow beats broad and fuzzy.** 101 means the fundamentals are *right*, not that everything got mentioned. One concept the user can reason with outweighs five they can recite.
- **Time is the budget.** Every stage carries an honest time cost and earns it. Padding a brief, a learning path, or a lab wastes the exact resource this skill exists to save.
- **Explaining it back is the test.** The agent's verification runs prove the code works; `NOTES.html` and the quiz prove the *user* works. Both, or the loop is not done.
- **Decision-grade or don't ship it.** If the brief does not help someone choose, it is a Wikipedia article.
- **Dates are non-negotiable.** An undated claim in a recency-scoped brief is a bug.
- **Announced ≠ shipped ≠ stable.** Keep the three apart, always.
- **Hype gets discounted, production reports get weighted.** One team's postmortem outweighs five launch posts.
- **No fabrication.** No invented benchmarks, quotes, versions, or video contents. Thin evidence gets said out loud: "little independent verification yet".
- **Honest verdicts.** "Hold — too early, revisit after the 2.0 spec lands" is a better answer than manufactured enthusiasm.
- **The user runs and explains; the agent prepares and verifies.** In a lab, a step whose output the user cannot watch appear and then explain is a failed step. Friction removed, learning kept.
- **Prediction before observation.** Memory forms in the gap between what the reader expected and what happened. A step that shows its result before asking for a guess has spent the output and bought nothing.
- **Design for the second pass, not the first.** Anything encountered once is gone by next week. Interleaved recall, a generated rather than given takeaway, and a standalone recap card are what turn an hour of watching into knowledge that survives.
- **Understanding is knowing what breaks otherwise.** Watching the right design work proves it works; watching the wrong one fail is what makes the choice repeatable in a design review months later.
- **Wrong answers are gold.** A quiz miss caught today is a production mistake avoided later. Grade honestly, correct with sources, never soften.

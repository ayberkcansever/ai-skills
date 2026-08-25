# Output — HTML, chat, handoff

Read this at **full-mode Step 8**, together with `assets/template.html` (linked from SKILL.md). Quick mode never reads this file.

Contents:

- One-writeup rule
- HTML structure
- Card rules
- Chat compact template
- Meta tags and save
- Verify after write
- Handoff

## One-writeup rule

Every blip appears **exactly twice** — once on the SVG radar, once as its single writeup card. No "Also on radar", no standalone watchlist section, no candidate-pool dump, no separate learn-next strip. The Learn ring *is* the learn-next list.

Show a **compact** version in chat. HTML is the reading artifact — do not dump the report into chat.

## HTML structure (in order)

Fill placeholders in `assets/template.html`. Leave the renderer, `QUADRANTS`, and `RINGS` constants untouched.

1. **Masthead.** Eyebrow left, scan date right, `What to learn next` h1 (no date in the title). ONE human sentence in `{{LEDE}}`: the window in words, how wide the sweep was, the lens — no counts, no mode, no feed health. Then the ring-count strip. Show a `0` rather than dropping a chip. Diagnostics never appear up here.
2. **The radar.** Fill `BLIPS`: `{n, q, ring, name, id}` numbered continuously, Techniques → Platforms → Tools → L&F. `id` anchors the card. `q`: 0 Techniques, 1 Platforms, 2 Tools, 3 L&F. `ring`: 0 Learn, 1 Try, 2 Watch, 3 Skip.
3. **Four quadrant sections.** Required ids: `q-techniques`, `q-platforms`, `q-tools`, `q-langs` — all four present even if a quadrant is thin. Each quadrant in `section.qsec`; each ring group in `div.ringgrp`. Rings in order Learn → Try → Watch → Skip; omit empty rings.

   Card rules:
   - **Learn/Try:** 2–4 dated evidence bullets, one line each, **at most one bold number**, source link inline, then a verdict (Learn = why it wins; Try = the cheaper pass now, with `span.effort` only when it is a real per-topic number). No `/learn` command on cards (parked). Skip the effort chip when the number would be the same on every card.
   - **Watch:** 1–2 evidence bullets + *promote when:* the concrete condition.
   - **Skip:** may drop evidence bullets — one-line what-it-is, why not, what would move it back.
   - After ring groups: `.notblipped` one-liners.

4. **All sources.** Collapsed `<details>` with the full dated list. Cards already link sources inline; this list is the audit trail.

**No scan-audit section in the HTML.** Gates still run; receipts go in chat + `radar-*` meta + `watchlist.json`. Anything the *next* scan needs goes in a meta tag, never only in prose.

Evidence style: dated bullets, not paragraphs. One fact per bullet.

## Chat compact

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
[2–4 lines: expired watchlist items, a gate that barely passed, a feed that broke,
topics excluded as already briefed, a topic recommended repeatedly and skipped.
Only what the user should react to, not the full ledger.]
```

## Meta tags and save

Fill every `radar-*` tag. An unfilled one is lost state:

- `radar-venues` — manual sources + wildcard queries used (next scan rotates away)
- `radar-next` — forward guidance: venues due again, conferences to catch, wildcards to vary
- `radar-mode` — `full` | `quick`
- `radar-intake` — e.g. `items:687 kept:42 dropped:645 feeds-ok:54 feeds-error:0`

Save `watchlist.json`. Rebuild the library index:

```bash
python3 ~/.cursor/skills/learn/scripts/build_index.py
```

Print the saved path plus `open ~/Documents/tech-briefs/radar/<date>.html`.

## Verify after write

Before declaring done:

- every `BLIPS[].id` exists as a card `id` in the HTML
- all four quadrant ids are present
- ring-count strip matches `BLIPS` lengths
- no leftover `{{PLACEHOLDER}}` in the saved file

## Handoff

End with: *"Pick a blip number — I'll run the full brief (and lab) on it."* On a pick, invoke the **learn** skill on that topic.

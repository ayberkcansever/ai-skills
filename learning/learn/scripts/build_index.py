#!/usr/bin/env python3
"""Rebuild ~/Documents/tech-briefs/index.html from all brief HTML files.

Scans every <Category>/*.html brief, reads its brief-* <meta> tags, and writes a
single styled landing page: newest first, grouped by category, with search plus
tag and verdict filters. Briefs older than STALE_DAYS get a "stale" marker so a
refresh run is easy to spot. Safe to run repeatedly; only index.html is written.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

LIBRARY = Path.home() / "Documents" / "tech-briefs"
STALE_DAYS = 180

CATEGORIES = [
    "AI-ML",
    "Infrastructure",
    "Data",
    "Security",
    "Languages-Frameworks",
    "DevTools",
    "Web",
    "Other",
]

VERDICTS = ["Adopt", "Trial", "Hold", "Avoid"]

META_RE = {
    "topic": re.compile(r'<meta name="brief-topic" content="([^"]*)"'),
    "category": re.compile(r'<meta name="brief-category" content="([^"]*)"'),
    "tags": re.compile(r'<meta name="brief-tags" content="([^"]*)"'),
    "date": re.compile(r'<meta name="brief-date" content="([^"]*)"'),
    "window": re.compile(r'<meta name="brief-window" content="([^"]*)"'),
    "verdict": re.compile(r'<meta name="brief-verdict" content="([^"]*)"'),
    "confidence": re.compile(r'<meta name="brief-confidence" content="([^"]*)"'),
    "poc": re.compile(r'<meta name="brief-poc" content="([^"]*)"'),
}

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_date(raw: str) -> date | None:
    m = DATE_RE.search(raw or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_brief(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if '<meta name="brief-topic"' not in text:
        return None
    out: dict = {"path": path}
    for key, rx in META_RE.items():
        m = rx.search(text)
        out[key] = html.unescape(m.group(1).strip()) if m else ""
    if not out["topic"]:
        out["topic"] = path.stem.replace("-", " ").title()
    if not out["category"]:
        out["category"] = path.parent.name if path.parent != LIBRARY else "Other"
    out["tag_list"] = [t.strip() for t in out["tags"].split(",") if t.strip()]
    out["date_obj"] = parse_date(out["date"])
    out["verdict_key"] = next(
        (v for v in VERDICTS if v.lower() == out["verdict"].strip().lower()), ""
    )
    age = (date.today() - out["date_obj"]).days if out["date_obj"] else None
    out["age_days"] = age
    out["stale"] = age is not None and age > STALE_DAYS
    out["poc_status"] = out["poc"].strip().lower()
    return out


def collect() -> list[dict]:
    briefs: list[dict] = []
    if not LIBRARY.exists():
        return briefs
    skip_dirs = (LIBRARY / "poc", LIBRARY / "radar")
    for p in sorted(LIBRARY.rglob("*.html")):
        if p.name == "index.html" or any(d in p.parents for d in skip_dirs):
            continue
        b = parse_brief(p)
        if b:
            b["rel"] = str(p.relative_to(LIBRARY))
            briefs.append(b)
    # Newest brief first; undated sink to the bottom.
    briefs.sort(key=lambda b: (b["date_obj"] or date.min), reverse=True)
    return briefs


def card_html(b: dict) -> str:
    tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in b["tag_list"])
    data_tags = html.escape(json.dumps(b["tag_list"]))
    verdict_cls = b["verdict_key"].lower() or "none"
    verdict_label = b["verdict_key"] or "—"
    conf = f' · {html.escape(b["confidence"])} confidence' if b["confidence"] else ""
    when = html.escape(b["date"] or "undated")
    stale = '<span class="stale">stale</span>' if b["stale"] else ""
    if b["poc_status"] == "completed":
        lab = '<span class="labdone">lab done</span>'
    elif b["poc_status"] == "scaffolded":
        lab = '<span class="lab">lab</span>'
    else:
        lab = ""
    return (
        f'<a class="card" href="{html.escape(b["rel"])}" '
        f"data-tags='{data_tags}' "
        f'data-verdict="{html.escape(verdict_cls)}" '
        f'data-title="{html.escape(b["topic"].lower())}">'
        f'<div class="card-head">'
        f'<span class="badge {verdict_cls}">{html.escape(verdict_label)}</span>{lab}{stale}'
        f"</div>"
        f'<div class="card-title">{html.escape(b["topic"])}</div>'
        f'<div class="card-by">{when}{conf}</div>'
        f'<div class="tags">{tags_html}</div></a>'
    )


def latest_radar_scan() -> Path | None:
    radar = LIBRARY / "radar"
    if not radar.exists():
        return None
    # Only date-named scans; YYYY-MM-DD names sort chronologically.
    scans = sorted(p for p in radar.glob("*.html") if DATE_RE.fullmatch(p.stem))
    return scans[-1] if scans else None


def render(briefs: list[dict]) -> str:
    order = {c: i for i, c in enumerate(CATEGORIES)}
    by_cat: dict[str, list[dict]] = {}
    for b in briefs:
        by_cat.setdefault(b["category"], []).append(b)

    all_tags = sorted({t for b in briefs for t in b["tag_list"]}, key=str.lower)
    total = len(briefs)
    stale_count = sum(1 for b in briefs if b["stale"])
    labs_done = sum(1 for b in briefs if b["poc_status"] == "completed")
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cat_sections = []
    for cat in sorted(by_cat, key=lambda c: order.get(c, 999)):
        items = by_cat[cat]  # already newest-first from collect()
        cards = "".join(card_html(b) for b in items)
        cat_sections.append(
            f'<section class="cat" data-cat="{html.escape(cat)}">'
            f'<h2>{html.escape(cat)} <span class="count">{len(items)}</span></h2>'
            f'<div class="grid">{cards}</div></section>'
        )

    tag_chips = "".join(
        f'<button class="chip" data-tag="{html.escape(t)}">{html.escape(t)}</button>'
        for t in all_tags
    )
    verdict_chips = "".join(
        f'<button class="chip vchip" data-verdict="{v.lower()}">{v}</button>' for v in VERDICTS
    )

    stale_note = (
        f' · <span class="stale-note">{stale_count} stale (&gt;{STALE_DAYS}d)</span>'
        if stale_count
        else ""
    )

    scan = latest_radar_scan()
    radar_link = (
        f' · <a class="radar-link" href="radar/{html.escape(scan.name)}">'
        f"latest radar scan ({html.escape(scan.stem)})</a>"
        if scan
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Tech Briefs Library</title>
<style>
  :root {{ --ink:#131a24; --muted:#5f6b7a; --accent:#1f6feb; --line:#e3e8ef; --bg:#f6f8fa; --card:#fff;
           --adopt:#1a7f4b; --trial:#1f6feb; --hold:#b3730a; --avoid:#c0392b; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif; padding:40px 20px; }}
  .wrap {{ max-width:1020px; margin:0 auto; }}
  h1 {{ font-size:30px; margin:0 0 4px; letter-spacing:-0.015em; }}
  .sub {{ color:var(--muted); font-size:13.5px; }}
  .stale-note {{ color:var(--hold); font-weight:600; }}
  .radar-link {{ color:#6d28d9; font-weight:600; text-decoration:none; }}
  .radar-link:hover {{ text-decoration:underline; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:22px 0 6px; }}
  #search {{ flex:1; min-width:220px; padding:10px 14px; border:1px solid var(--line); border-radius:10px; font:15px ui-sans-serif,system-ui,sans-serif; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 4px; }}
  .chips.tags {{ margin-bottom:24px; }}
  .chip {{ border:1px solid var(--line); background:var(--card); color:var(--muted); border-radius:999px; padding:5px 12px; font-size:13px; cursor:pointer; }}
  .chip.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
  .vchip[data-verdict="adopt"].active {{ background:var(--adopt); border-color:var(--adopt); }}
  .vchip[data-verdict="trial"].active {{ background:var(--trial); border-color:var(--trial); }}
  .vchip[data-verdict="hold"].active  {{ background:var(--hold);  border-color:var(--hold); }}
  .vchip[data-verdict="avoid"].active {{ background:var(--avoid); border-color:var(--avoid); }}
  h2 {{ font-size:12.5px; letter-spacing:0.12em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--line); padding-bottom:8px; margin:32px 0 16px; }}
  h2 .count {{ color:var(--accent); margin-left:6px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }}
  .card {{ display:block; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:15px 17px; text-decoration:none; color:inherit; transition:.15s; }}
  .card:hover {{ border-color:var(--accent); box-shadow:0 6px 22px rgba(19,26,36,.07); transform:translateY(-1px); }}
  .card-head {{ display:flex; align-items:center; gap:8px; margin-bottom:9px; }}
  .badge {{ display:inline-block; border-radius:999px; padding:2px 10px; font:700 10.5px/1.6 ui-sans-serif,system-ui,sans-serif; letter-spacing:.08em; text-transform:uppercase; color:#fff; background:var(--muted); }}
  .badge.adopt {{ background:var(--adopt); }}
  .badge.trial {{ background:var(--trial); }}
  .badge.hold  {{ background:var(--hold); }}
  .badge.avoid {{ background:var(--avoid); }}
  .badge.none  {{ background:#aab3bf; }}
  .stale {{ font:600 10.5px/1.6 ui-sans-serif,system-ui,sans-serif; letter-spacing:.06em; text-transform:uppercase; color:var(--hold); border:1px solid #ffd9a8; background:#fffaf1; border-radius:999px; padding:1px 8px; }}
  .lab {{ font:600 10.5px/1.6 ui-sans-serif,system-ui,sans-serif; letter-spacing:.06em; text-transform:uppercase; color:var(--hold); border:1px solid #f2ddb8; background:#fdf8ee; border-radius:999px; padding:1px 8px; }}
  .labdone {{ font:600 10.5px/1.6 ui-sans-serif,system-ui,sans-serif; letter-spacing:.06em; text-transform:uppercase; color:var(--adopt); border:1px solid #bfe3cf; background:#f0faf4; border-radius:999px; padding:1px 8px; }}
  .card-title {{ font-weight:700; font-size:16px; margin-bottom:3px; }}
  .card-by {{ color:var(--muted); font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace; margin-bottom:10px; }}
  .tags {{ display:flex; flex-wrap:wrap; gap:5px; }}
  .tag {{ background:#eef1f5; color:var(--muted); border-radius:6px; padding:2px 8px; font-size:11px; }}
  .cat.hidden, .card.hidden {{ display:none; }}
  .empty {{ color:var(--muted); padding:40px 0; text-align:center; display:none; }}
  footer {{ margin-top:40px; color:var(--muted); font-size:12px; border-top:1px solid var(--line); padding-top:14px; }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Tech Briefs Library</h1>
      <div class="sub">{total} brief{"s" if total != 1 else ""} · {labs_done} lab{"s" if labs_done != 1 else ""} done · newest first · updated {updated}{stale_note}{radar_link}</div>
    </header>
    <div class="controls">
      <input id="search" type="search" placeholder="Search topic…" />
    </div>
    <div class="chips verdicts">{verdict_chips}</div>
    <div class="chips tags">{tag_chips or '<span class="sub">No tags yet</span>'}</div>
    {"".join(cat_sections) or '<p class="sub">No briefs yet. Run the learn skill.</p>'}
    <p class="empty">No matches.</p>
    <footer>Generated by learn · build_index.py</footer>
  </div>
<script>
  const search = document.getElementById('search');
  const tagChips = [...document.querySelectorAll('.chip[data-tag]')];
  const verdictChips = [...document.querySelectorAll('.vchip')];
  const cards = [...document.querySelectorAll('.card')];
  const cats = [...document.querySelectorAll('.cat')];
  const empty = document.querySelector('.empty');
  const activeTags = new Set();
  const activeVerdicts = new Set();

  function apply() {{
    const q = search.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach(c => {{
      const tags = JSON.parse(c.dataset.tags || '[]');
      const okText = !q || c.dataset.title.includes(q);
      const okTags = activeTags.size === 0 || [...activeTags].every(t => tags.includes(t));
      const okVerdict = activeVerdicts.size === 0 || activeVerdicts.has(c.dataset.verdict);
      const show = okText && okTags && okVerdict;
      c.classList.toggle('hidden', !show);
      if (show) visible++;
    }});
    cats.forEach(s => {{
      const any = [...s.querySelectorAll('.card')].some(c => !c.classList.contains('hidden'));
      s.classList.toggle('hidden', !any);
    }});
    empty.style.display = visible === 0 ? 'block' : 'none';
  }}

  function toggle(set, key, el) {{
    if (set.has(key)) {{ set.delete(key); el.classList.remove('active'); }}
    else {{ set.add(key); el.classList.add('active'); }}
    apply();
  }}

  search.addEventListener('input', apply);
  tagChips.forEach(ch => ch.addEventListener('click', () => toggle(activeTags, ch.dataset.tag, ch)));
  verdictChips.forEach(ch => ch.addEventListener('click', () => toggle(activeVerdicts, ch.dataset.verdict, ch)));
</script>
</body>
</html>
"""


def main() -> None:
    briefs = collect()
    LIBRARY.mkdir(parents=True, exist_ok=True)
    (LIBRARY / "index.html").write_text(render(briefs), encoding="utf-8")
    print(f"Indexed {len(briefs)} brief(s) → {LIBRARY / 'index.html'}")


if __name__ == "__main__":
    main()

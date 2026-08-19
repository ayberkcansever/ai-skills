#!/usr/bin/env python3
"""tech-radar intake crawler — stdlib only, no pip installs.

Reads feeds.toml (sibling of this script's parent dir), fetches every machine-
readable feed in parallel, window-filters, dedupes, drops noise, caps per feed,
and writes a compact intake JSON the agent triages. Manual feeds are not
fetched — they are listed in the output so the agent cannot silently skip them.

Usage:
    python3 scan_feeds.py                       # defaults: 90-day window
    python3 scan_feeds.py --window 30           # shorter window
    python3 scan_feeds.py --out-dir /tmp/radar  # write elsewhere

Output: <out-dir>/intake/YYYY-MM-DD.json plus a human summary on stdout.
Exit code is 0 unless the registry is unreadable or >50% of feeds error.
"""

import argparse
import concurrent.futures
import datetime as dt
import email.utils
import gzip
import json
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) tech-radar-scan/1.0"
TIMEOUT = 15
DEFAULT_OUT = Path.home() / "Documents" / "tech-briefs" / "radar"
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last_err = None
    for _ in range(2):  # one retry
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)
                return data
        except Exception as e:  # noqa: BLE001 — report any fetch failure as feed health
            last_err = e
    raise RuntimeError(f"{type(last_err).__name__}: {last_err}")


def parse_date(raw: str) -> dt.date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:  # RFC 822 (RSS pubDate)
        return email.utils.parsedate_to_datetime(raw).date()
    except (TypeError, ValueError):
        pass
    try:  # ISO 8601 (Atom updated/published)
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def parse_feed_xml(data: bytes) -> list[dict]:
    """Parse RSS 2.0 or Atom into [{title, url, date}]."""
    root = ET.fromstring(data)
    items = []
    if root.tag == f"{ATOM}feed":  # Atom
        for entry in root.findall(f"{ATOM}entry"):
            title = (entry.findtext(f"{ATOM}title") or "").strip()
            link = ""
            for l in entry.findall(f"{ATOM}link"):
                if l.get("rel") in (None, "alternate"):
                    link = l.get("href", "")
                    break
            date = parse_date(
                entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated") or ""
            )
            items.append({"title": title, "url": link, "date": date})
    else:  # RSS 2.0 (root <rss> or <rdf>)
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            date = parse_date(item.findtext("pubDate") or item.findtext("date") or "")
            items.append({"title": title, "url": link, "date": date})
    return items


def fetch_rss(feed: dict, since: dt.date, cap: int) -> list[dict]:
    parsed = parse_feed_xml(fetch(feed["url"]))
    dated = [it for it in parsed if it["date"]]
    if not dated and parsed:
        # Some feeds (e.g. Google Developers Blog) publish no item dates. They
        # serve only their latest posts, so keep them rather than lose the feed.
        return parsed[:cap]
    kept = [it for it in dated if it["date"] >= since]
    kept.sort(key=lambda it: it["date"], reverse=True)
    return kept[:cap]


def fetch_hn(feed: dict, since: dt.date, settings: dict) -> list[dict]:
    min_points = settings.get("hn_min_points", 400)
    cap = settings.get("hn_cap", 150)
    since_epoch = int(dt.datetime.combine(since, dt.time.min, dt.timezone.utc).timestamp())
    collected, page = [], 0
    while page < 10:
        qs = urllib.parse.urlencode(
            {
                "tags": "story",
                "numericFilters": f"points>={min_points},created_at_i>={since_epoch}",
                "hitsPerPage": 100,
                "page": page,
            }
        )
        payload = json.loads(fetch(f"https://hn.algolia.com/api/v1/search_by_date?{qs}"))
        hits = payload.get("hits", [])
        for h in hits:
            collected.append(
                {
                    "title": h.get("title") or "",
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "date": dt.datetime.fromtimestamp(
                        h.get("created_at_i", 0), dt.timezone.utc
                    ).date(),
                    "points": h.get("points", 0),
                }
            )
        page += 1
        if page >= payload.get("nbPages", 0):
            break
    collected.sort(key=lambda it: it["points"], reverse=True)
    return collected[:cap]


def fetch_lobsters(feed: dict, since: dt.date, cap: int) -> list[dict]:
    payload = json.loads(fetch(feed["url"]))
    items = []
    for story in payload:
        date = parse_date(story.get("created_at", ""))
        if date and date >= since:
            items.append(
                {
                    "title": story.get("title", ""),
                    "url": story.get("url") or story.get("comments_url", ""),
                    "date": date,
                }
            )
    return items[:cap]


def fetch_endoflife(feed: dict, settings: dict) -> list[dict]:
    """Upcoming (or just-passed) EOL dates for the configured products."""
    today = dt.date.today()
    horizon = today + dt.timedelta(days=settings.get("eol_horizon_days", 180))
    lookback = today - dt.timedelta(days=30)
    items = []
    for product in settings.get("eol_products", []):
        try:
            cycles = json.loads(fetch(f"https://endoflife.date/api/{product}.json"))
        except Exception:  # one bad product must not kill the whole feed
            continue
        for cycle in cycles:
            eol = cycle.get("eol")
            if not isinstance(eol, str):
                continue
            eol_date = parse_date(eol)
            if eol_date and lookback <= eol_date <= horizon:
                items.append(
                    {
                        "title": f"EOL: {product} {cycle.get('cycle')} end-of-life {eol_date}",
                        "url": f"https://endoflife.date/{product}",
                        "date": eol_date,
                    }
                )
    items.sort(key=lambda it: it["date"])
    return items


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", default=str(Path(__file__).parent.parent / "feeds.toml"))
    ap.add_argument("--window", type=int, default=None, help="override window_days")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    try:
        registry = tomllib.loads(Path(args.registry).read_text())
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: cannot read registry {args.registry}: {e}", file=sys.stderr)
        return 2

    settings = registry.get("settings", {})
    window_days = args.window or settings.get("window_days", 90)
    cap = settings.get("per_feed_cap", 15)
    noise = [k.lower() for k in settings.get("noise_keywords", [])]
    since = dt.date.today() - dt.timedelta(days=window_days)

    feeds = registry.get("feeds", [])
    manual = [f for f in feeds if f["type"] == "manual"]
    fetchable = [f for f in feeds if f["type"] != "manual"]

    def run_one(feed: dict) -> tuple[dict, list[dict], str]:
        try:
            if feed["type"] == "rss":
                items = fetch_rss(feed, since, cap)
            elif feed["type"] == "hn":
                items = fetch_hn(feed, since, settings)
            elif feed["type"] == "lobsters":
                items = fetch_lobsters(feed, since, cap)
            elif feed["type"] == "endoflife":
                items = fetch_endoflife(feed, settings)
            else:
                return feed, [], f"error: unknown type {feed['type']}"
            return feed, items, "ok" if items else "empty"
        except Exception as e:  # noqa: BLE001
            return feed, [], f"error: {e}"

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for feed, items, status in pool.map(run_one, fetchable):
            results.append((feed, items, status))

    # Merge, drop noise, dedupe (title-normalized or exact URL).
    seen_titles, seen_urls = set(), set()
    all_items, dropped_noise, dropped_dupes = [], 0, 0
    for feed, items, _status in results:
        for it in items:
            title = it["title"]
            if any(k in title.lower() for k in noise):
                dropped_noise += 1
                continue
            tkey, ukey = normalize_title(title), it["url"]
            if tkey in seen_titles or (ukey and ukey in seen_urls):
                dropped_dupes += 1
                continue
            seen_titles.add(tkey)
            if ukey:
                seen_urls.add(ukey)
            entry = {
                "d": str(it["date"]) if it["date"] else "",
                "s": feed["id"],
                "c": feed.get("class", ""),
                "t": title,
                "u": it["url"],
            }
            if "points" in it:
                entry["p"] = it["points"]
            all_items.append(entry)

    all_items.sort(key=lambda e: e["d"], reverse=True)
    for i, entry in enumerate(all_items):
        entry["i"] = i

    health = [
        {"id": feed["id"], "status": status, "kept": len(items)}
        for feed, items, status in sorted(results, key=lambda r: r[0]["id"])
    ]
    errors = [h for h in health if h["status"].startswith("error")]

    out_dir = Path(args.out_dir) / "intake"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dt.date.today()}.json"
    out_path.write_text(
        json.dumps(
            {
                "generated": str(dt.date.today()),
                "window_days": window_days,
                "feeds": health,
                "manual": [
                    {"id": f["id"], "name": f["name"], "hint": f.get("hint", ""), "url": f["url"]}
                    for f in manual
                ],
                "stats": {
                    "items": len(all_items),
                    "dropped_noise": dropped_noise,
                    "dropped_dupes": dropped_dupes,
                },
                "items": all_items,
            },
            separators=(",", ":"),
        )
    )

    # Compact triage view — the agent reads THIS for keep/drop (about half the
    # tokens of the JSON); URLs are looked up in the JSON by index for keeps only.
    titles_path = out_dir / f"{dt.date.today()}.titles.txt"
    titles_path.write_text(
        "\n".join(f"{e['i']}|{e['d']}|{e['s']}|{e['t']}" for e in all_items) + "\n"
    )

    # Human summary
    print(f"intake: {out_path}")
    print(f"triage view: {titles_path}")
    print(f"window: {window_days}d  items: {len(all_items)}  "
          f"noise-dropped: {dropped_noise}  dupes-dropped: {dropped_dupes}\n")
    width = max(len(h["id"]) for h in health)
    for h in health:
        print(f"  {h['id']:<{width}}  {h['kept']:>4}  {h['status']}")
    print(f"\nmanual feeds the AGENT must cover ({len(manual)}):")
    for f in manual:
        print(f"  {f['id']:<{width}}  {f.get('hint', '')[:90]}")
    if errors:
        print(f"\n{len(errors)} feed(s) in error — agent must run site: fallback searches for these.")
    return 1 if len(errors) > len(fetchable) / 2 else 0


if __name__ == "__main__":
    sys.exit(main())

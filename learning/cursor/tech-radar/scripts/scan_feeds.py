#!/usr/bin/env python3
"""tech-radar intake crawler — stdlib only, no pip installs.

Reads feeds.toml (sibling of this script's parent dir), fetches every machine-
readable feed in parallel, window-filters, dedupes, and splits the result into
a reviewable set the agent must disposition and an auto-dropped set that
already carries its reason. Manual feeds are not fetched — they are listed in
the output so the agent cannot silently skip them.

Usage:
    python3 scan_feeds.py                       # defaults: 90-day window
    python3 scan_feeds.py --window 30           # shorter window
    python3 scan_feeds.py --out-dir /tmp/radar  # write elsewhere

Output under <out-dir>/intake/:
    YYYY-MM-DD.json        reviewable items + auto-drops + feed health + manual list
    YYYY-MM-DD.titles.txt  the reviewable set  (i|date|source|flag|title)
    YYYY-MM-DD.drops.txt   the audit trail     (date|source|reason|title)
Plus <out-dir>/feed_health.json — consecutive-error memory across scans, so a
feed that breaks twice in a row is reported as a registry fix, not a blip.

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

# A thing arriving, changing shape, or going away. Never auto-dropped: this is
# the class of item the radar exists to catch, so it outranks the minor rules.
NOVELTY_RE = re.compile(
    r"""(?ix)
      \b(announc|introduc|unveil|launch)\w*\b
    | \bgenerally\s+available\b | \bGA\b
    | \bgraduat\w*\b
    | \bmajor\s+release\b | \bfirst\s+stable\b
    | \bbreaking\s+chang\w*\b
    | \bdeprecat\w*\b | \bsunset\w*\b | \bend[-\s]of[-\s]life\b | \bEOL\b
    | \bopen[-\s]sourc\w*\b
    | \b[vV]?[1-9]\d*\.0(\.0)?\b
    | \b(public\s+)?(beta|preview)\b | \brelease\s+candidate\b
    """
)

# Security always survives triage — a patch-shaped title can be an emergency.
SECURITY_RE = re.compile(
    r"""(?ix)
      \bCVE-\d{4}-\d+\b
    | \bsecurity\s+(release|update|advisor\w*|fix)\b
    | \bvulnerab\w*\b | \bexploit\w*\b | \bzero[-\s]day\b
    | \bRCE\b | \bmalware\b | \bsupply[-\s]chain\b | \bbackdoor\b
    """
)

# A capability claim rescues a patch-shaped title: "New Iceberg features in
# v1.5.3" is a topic, "v1.5.3" is not. Real patch releases do not advertise.
FEATURE_RE = re.compile(
    r"""(?ix)
      \bnew\s+(\w+[\s-]+){0,3}features?\b | \bnew\s+features?\b
    | \badds?\b | \bnow\s+supports?\b | \bsupport\s+for\b
    | \bimprove\w*\b | \bfaster\b | \brewritten\b | \brewrite\b
    """
)

# x.y.z with a non-zero patch component — routine maintenance, not a topic.
PATCH_RE = re.compile(r"\b[vV]?\d+\.\d+\.[1-9]\d*\b")
REGION_RE = re.compile(r"(?i)\b(now\s+available|expand\w*|additional|new)\b.*\bregions?\b")
MAINTENANCE_RE = re.compile(
    r"(?i)\b(patch|point|maintenance)\s+release\b|\bbug\s?fix\w*\b|\bhotfix\b"
)


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


def is_novel(title: str) -> bool:
    return bool(NOVELTY_RE.search(title))


def is_priority(title: str) -> bool:
    """Worth a cap slot ahead of a merely newer post."""
    return is_novel(title) or bool(SECURITY_RE.search(title))


def select_window(items: list[dict], since: dt.date, cap: int) -> tuple[list[dict], int]:
    """Items inside the window, capped, newest-first. Returns (kept, in_window).

    in_window > len(kept) means the cap truncated real coverage, which the
    caller reports so the agent knows to back that feed with a direct search.
    When the cap bites, significance wins the slots before recency does: a
    high-volume publisher would otherwise bury its own launch announcement
    under three weeks of routine posts.
    """
    dated = [it for it in items if it.get("date")]
    if not dated and items:
        # Some feeds (e.g. Google Developers Blog) publish no item dates. They
        # serve only their latest posts, so keep them rather than lose the feed.
        return items[:cap], len(items)
    kept = [it for it in dated if it["date"] >= since]
    kept.sort(key=lambda it: it["date"], reverse=True)
    in_window = len(kept)
    if in_window > cap:
        priority = [it for it in kept if is_priority(it["title"])]
        rest = [it for it in kept if not is_priority(it["title"])]
        kept = priority[:cap] + rest[: max(0, cap - len(priority))]
        kept.sort(key=lambda it: it["date"], reverse=True)
    return kept[:cap], in_window


def auto_drop_reason(title: str, noise_keywords: list[str]) -> str | None:
    """Why this item needs no human judgement, or None if it must be reviewed.

    Order matters: noise is unconditional, then novelty, security, and
    capability claims rescue an item, and only then do the routine-maintenance
    rules apply.
    """
    low = title.lower()
    if not title.strip():
        return "empty"
    if any(k in low for k in noise_keywords):
        return "noise"
    if is_novel(title) or SECURITY_RE.search(title) or FEATURE_RE.search(title):
        return None
    if REGION_RE.search(title) or MAINTENANCE_RE.search(title) or PATCH_RE.search(title):
        return "minor"
    return None


def fetch_rss(feed: dict, since: dt.date, cap: int) -> tuple[list[dict], int]:
    return select_window(parse_feed_xml(fetch(feed["url"])), since, cap)


def _hn_query(min_points: int, max_points: int | None, since_epoch: int) -> list[dict]:
    numeric = [f"points>={min_points}", f"created_at_i>={since_epoch}"]
    if max_points is not None:
        numeric.append(f"points<{max_points}")
    collected, page = [], 0
    while page < 10:
        qs = urllib.parse.urlencode(
            {
                "tags": "story",
                "numericFilters": ",".join(numeric),
                "hitsPerPage": 100,
                "page": page,
            }
        )
        payload = json.loads(fetch(f"https://hn.algolia.com/api/v1/search_by_date?{qs}"))
        for h in payload.get("hits", []):
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
    return collected


def fetch_hn(feed: dict, since: dt.date, settings: dict) -> tuple[list[dict], int]:
    """Two bands: what the crowd already voted up, plus a discovery slice.

    The high floor finds consensus. A new name nobody has heard of never clears
    it, so the discovery band (below the floor, hard-capped) is where a project
    in its first weeks can still reach the radar.
    """
    top_floor = settings.get("hn_min_points", 400)
    top_cap = settings.get("hn_cap", 150)
    disc_floor = settings.get("hn_discovery_min_points", 0)
    disc_cap = settings.get("hn_discovery_cap", 0)
    since_epoch = int(dt.datetime.combine(since, dt.time.min, dt.timezone.utc).timestamp())

    top = _hn_query(top_floor, None, since_epoch)
    items, in_window = top[:top_cap], len(top)

    if disc_floor and disc_cap and disc_floor < top_floor:
        disc = _hn_query(disc_floor, top_floor, since_epoch)
        in_window += len(disc)
        for it in disc[:disc_cap]:
            items.append({**it, "tier": "discovery"})
    return items, in_window


def fetch_lobsters(feed: dict, since: dt.date, cap: int) -> tuple[list[dict], int]:
    payload = json.loads(fetch(feed["url"]))
    items = []
    for story in payload:
        items.append(
            {
                "title": story.get("title", ""),
                "url": story.get("url") or story.get("comments_url", ""),
                "date": parse_date(story.get("created_at", "")),
            }
        )
    return select_window(items, since, cap)


def fetch_endoflife(feed: dict, settings: dict) -> tuple[list[dict], int]:
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
    return items, len(items)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def merge_items(
    results: list[tuple[dict, list[dict], str]], noise_keywords: list[str]
) -> tuple[list[dict], list[dict]]:
    """Split every fetched item into (reviewable, auto_dropped).

    Every input item lands in exactly one of the two lists, so the pair is a
    complete account of the crawl — that is what makes the ledger auditable.
    """
    seen_titles, seen_urls = set(), set()
    reviewable, dropped = [], []
    for feed, items, _status in results:
        for it in items:
            title = it["title"]
            record = {
                "d": str(it["date"]) if it.get("date") else "",
                "s": feed["id"],
                "c": feed.get("class", ""),
                "t": title,
                "u": it["url"],
            }
            if "points" in it:
                record["p"] = it["points"]
            if it.get("tier"):
                record["tier"] = it["tier"]

            reason = auto_drop_reason(title, noise_keywords)
            if reason:
                dropped.append({**record, "r": reason})
                continue

            tkey, ukey = normalize_title(title), it["url"]
            if tkey in seen_titles or (ukey and ukey in seen_urls):
                dropped.append({**record, "r": "dupe"})
                continue
            seen_titles.add(tkey)
            if ukey:
                seen_urls.add(ukey)
            if is_novel(title):
                record["n"] = 1
            reviewable.append(record)

    reviewable.sort(key=lambda e: e["d"], reverse=True)
    for i, entry in enumerate(reviewable):
        entry["i"] = i
    return reviewable, dropped


def update_feed_health(path: Path, health: list[dict], today: dt.date) -> dict:
    """Carry error counts across scans so 'broken twice' is a fact, not a memory."""
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        state = {"feeds": {}}
    feeds = state.get("feeds", {})
    for h in health:
        prev = feeds.get(h["id"], {})
        if h["status"].startswith("error"):
            h["consecutive_errors"] = prev.get("consecutive_errors", 0) + 1
            h["last_ok"] = prev.get("last_ok", "")
        else:
            h["consecutive_errors"] = 0
            h["last_ok"] = str(today)
        feeds[h["id"]] = {
            "consecutive_errors": h["consecutive_errors"],
            "last_ok": h["last_ok"],
            "last_status": h["status"],
        }
    state = {"updated": str(today), "feeds": feeds}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return state


def flags_for(entry: dict) -> str:
    flags = []
    if entry.get("n"):
        flags.append("new")
    if entry.get("tier") == "discovery":
        flags.append("disc")
    return "+".join(flags) or "-"


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
    cap = settings.get("per_feed_cap", 25)
    noise = [k.lower() for k in settings.get("noise_keywords", [])]
    today = dt.date.today()
    since = today - dt.timedelta(days=window_days)

    feeds = registry.get("feeds", [])
    manual = [f for f in feeds if f["type"] == "manual"]
    fetchable = [f for f in feeds if f["type"] != "manual"]

    def run_one(feed: dict) -> tuple[dict, list[dict], str, int]:
        feed_cap = feed.get("cap", cap)  # a genuinely high-volume feed can raise its own
        try:
            if feed["type"] == "rss":
                items, in_window = fetch_rss(feed, since, feed_cap)
            elif feed["type"] == "hn":
                items, in_window = fetch_hn(feed, since, settings)
            elif feed["type"] == "lobsters":
                items, in_window = fetch_lobsters(feed, since, feed_cap)
            elif feed["type"] == "endoflife":
                items, in_window = fetch_endoflife(feed, settings)
            else:
                return feed, [], f"error: unknown type {feed['type']}", 0
            return feed, items, "ok" if items else "empty", in_window
        except Exception as e:  # noqa: BLE001
            return feed, [], f"error: {e}", 0

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for feed, items, status, in_window in pool.map(run_one, fetchable):
            results.append((feed, items, status, in_window))

    reviewable, dropped = merge_items([(f, i, s) for f, i, s, _ in results], noise)

    health = [
        {
            "id": feed["id"],
            "status": status,
            "kept": len(items),
            "in_window": in_window,
            # Aggregators sample by design — a points floor IS their policy, so
            # only a publisher feed losing its own posts counts as truncation.
            "truncated": in_window > len(items) and feed["type"] == "rss",
        }
        for feed, items, status, in_window in sorted(results, key=lambda r: r[0]["id"])
    ]
    out_root = Path(args.out_dir)
    update_feed_health(out_root / "feed_health.json", health, today)
    errors = [h for h in health if h["status"].startswith("error")]
    stale = [h for h in health if h["consecutive_errors"] >= 2]
    truncated = [h for h in health if h["truncated"]]

    drop_counts: dict[str, int] = {}
    for d in dropped:
        drop_counts[d["r"]] = drop_counts.get(d["r"], 0) + 1

    out_dir = out_root / "intake"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"
    out_path.write_text(
        json.dumps(
            {
                "generated": str(today),
                "window_days": window_days,
                "feeds": health,
                "manual": [
                    {"id": f["id"], "name": f["name"], "hint": f.get("hint", ""), "url": f["url"]}
                    for f in manual
                ],
                "stats": {
                    "reviewable": len(reviewable),
                    "novelty": sum(1 for e in reviewable if e.get("n")),
                    "discovery": sum(1 for e in reviewable if e.get("tier") == "discovery"),
                    "auto_dropped": len(dropped),
                    "auto_dropped_by_reason": drop_counts,
                    "truncated_feeds": [h["id"] for h in truncated],
                },
                "items": reviewable,
                "auto_dropped": dropped,
            },
            separators=(",", ":"),
        )
    )

    # Compact triage view — the agent reads THIS for keep/drop (about half the
    # tokens of the JSON); URLs are looked up in the JSON by index for keeps only.
    titles_path = out_dir / f"{today}.titles.txt"
    titles_path.write_text(
        "\n".join(f"{e['i']}|{e['d']}|{e['s']}|{flags_for(e)}|{e['t']}" for e in reviewable) + "\n"
    )

    # The audit trail: what the crawler decided without asking, and why.
    drops_path = out_dir / f"{today}.drops.txt"
    drops_path.write_text(
        "\n".join(f"{d['d']}|{d['s']}|{d['r']}|{d['t']}" for d in dropped) + "\n"
    )

    print(f"intake: {out_path}")
    print(f"triage view: {titles_path}   ({len(reviewable)} items to disposition)")
    print(f"drop ledger: {drops_path}")
    print(
        f"window: {window_days}d  reviewable: {len(reviewable)}  "
        f"novelty-flagged: {sum(1 for e in reviewable if e.get('n'))}  "
        f"auto-dropped: {len(dropped)} {drop_counts}\n"
    )
    width = max(len(h["id"]) for h in health)
    for h in health:
        mark = " TRUNCATED" if h["truncated"] else ""
        print(f"  {h['id']:<{width}}  {h['kept']:>4}/{h['in_window']:<4}  {h['status']}{mark}")
    print(f"\nmanual feeds the AGENT must cover ({len(manual)}):")
    for f in manual:
        print(f"  {f['id']:<{width}}  {f.get('hint', '')[:90]}")
    if truncated:
        print(
            f"\n{len(truncated)} publisher feed(s) hit the cap (default {cap}) — coverage was cut "
            "after novelty and security items were secured. Agent must run a direct search for "
            "these, or give the feed its own `cap` in feeds.toml."
        )
    if errors:
        print(f"\n{len(errors)} feed(s) in error — agent must run site: fallback searches for these.")
    if stale:
        print(
            "REGISTRY FIX NEEDED (failed 2+ scans in a row): "
            + ", ".join(f"{h['id']}({h['consecutive_errors']})" for h in stale)
        )
    return 1 if len(errors) > len(fetchable) / 2 else 0


if __name__ == "__main__":
    sys.exit(main())

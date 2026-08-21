#!/usr/bin/env python3
"""Tests for the intake crawler's pure logic. Stdlib only, no network.

    python3 scripts/test_scan_feeds.py

Every test here guards a coverage rule: if one of these fails, the radar is
either dropping items it should review or reviewing items it should drop.
"""

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scan_feeds import (  # noqa: E402
    auto_drop_reason,
    flags_for,
    is_novel,
    merge_items,
    normalize_title,
    parse_date,
    parse_feed_xml,
    select_window,
    update_feed_health,
)

NOISE = ["webinar", "hiring", "this week in"]


class ParseDate(unittest.TestCase):
    def test_rfc822(self):
        self.assertEqual(parse_date("Tue, 05 Aug 2025 10:00:00 GMT"), dt.date(2025, 8, 5))

    def test_iso_with_zulu(self):
        self.assertEqual(parse_date("2026-02-11T09:30:00Z"), dt.date(2026, 2, 11))

    def test_garbage_and_empty_are_none(self):
        self.assertIsNone(parse_date("last Tuesday"))
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date(None))


class ParseFeedXml(unittest.TestCase):
    def test_atom_prefers_alternate_link(self):
        xml = b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Introducing Widget</title>
            <link rel="edit" href="https://x.test/edit"/>
            <link rel="alternate" href="https://x.test/post"/>
            <published>2026-03-01T00:00:00Z</published>
          </entry>
        </feed>"""
        items = parse_feed_xml(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://x.test/post")
        self.assertEqual(items[0]["date"], dt.date(2026, 3, 1))

    def test_rss(self):
        xml = b"""<rss><channel><item>
            <title>Thing 2.0</title><link>https://y.test/a</link>
            <pubDate>Wed, 01 Apr 2026 00:00:00 GMT</pubDate>
        </item></channel></rss>"""
        items = parse_feed_xml(xml)
        self.assertEqual(items[0]["title"], "Thing 2.0")
        self.assertEqual(items[0]["date"], dt.date(2026, 4, 1))


class SelectWindow(unittest.TestCase):
    def items(self, *days_ago):
        today = dt.date.today()
        return [
            {"title": f"t{d}", "url": f"u{d}", "date": today - dt.timedelta(days=d)}
            for d in days_ago
        ]

    def test_drops_items_older_than_window(self):
        since = dt.date.today() - dt.timedelta(days=30)
        kept, in_window = select_window(self.items(1, 10, 200), since, 25)
        self.assertEqual([it["title"] for it in kept], ["t1", "t10"])
        self.assertEqual(in_window, 2)

    def test_cap_truncates_and_reports_real_total(self):
        since = dt.date.today() - dt.timedelta(days=90)
        kept, in_window = select_window(self.items(1, 2, 3, 4, 5), since, 2)
        self.assertEqual(len(kept), 2)
        self.assertEqual(in_window, 5)  # this gap is what triggers TRUNCATED

    def test_cap_keeps_significance_over_recency(self):
        # A busy publisher must not bury its own launch under routine posts.
        today = dt.date.today()
        raw = [
            {"title": f"routine post {d}", "url": f"u{d}", "date": today - dt.timedelta(days=d)}
            for d in range(1, 6)
        ]
        raw.append(
            {"title": "Announcing Widget 3.0", "url": "u99", "date": today - dt.timedelta(days=40)}
        )
        raw.append(
            {"title": "CVE-2026-9999 in our SDK", "url": "u98", "date": today - dt.timedelta(days=50)}
        )
        kept, in_window = select_window(raw, today - dt.timedelta(days=90), 3)
        titles = [it["title"] for it in kept]
        self.assertIn("Announcing Widget 3.0", titles)
        self.assertIn("CVE-2026-9999 in our SDK", titles)
        self.assertEqual(len(kept), 3)
        self.assertEqual(in_window, 7)

    def test_priority_items_cannot_exceed_the_cap(self):
        today = dt.date.today()
        raw = [
            {"title": f"Announcing Thing {d}.0", "url": f"u{d}", "date": today - dt.timedelta(days=d)}
            for d in range(1, 8)
        ]
        kept, in_window = select_window(raw, today - dt.timedelta(days=90), 4)
        self.assertEqual(len(kept), 4)
        self.assertEqual(in_window, 7)

    def test_newest_first(self):
        since = dt.date.today() - dt.timedelta(days=90)
        kept, _ = select_window(self.items(9, 1, 5), since, 25)
        self.assertEqual([it["title"] for it in kept], ["t1", "t5", "t9"])

    def test_undated_feed_is_kept_not_lost(self):
        raw = [{"title": "a", "url": "ua", "date": None}, {"title": "b", "url": "ub", "date": None}]
        kept, in_window = select_window(raw, dt.date.today(), 25)
        self.assertEqual(len(kept), 2)
        self.assertEqual(in_window, 2)


class AutoDrop(unittest.TestCase):
    def test_noise_always_drops(self):
        self.assertEqual(auto_drop_reason("Join our webinar on Rust", NOISE), "noise")
        self.assertEqual(auto_drop_reason("This week in Kubernetes", NOISE), "noise")

    def test_patch_release_is_minor(self):
        self.assertEqual(auto_drop_reason("Node.js 24.5.1 released", NOISE), "minor")
        self.assertEqual(auto_drop_reason("Kubernetes v1.34.3 is out", NOISE), "minor")

    def test_region_expansion_is_minor(self):
        self.assertEqual(
            auto_drop_reason("Amazon Bedrock now available in three new regions", NOISE), "minor"
        )

    def test_maintenance_wording_is_minor(self):
        self.assertEqual(auto_drop_reason("Django 5.2.4 bugfix release", NOISE), "minor")

    def test_minor_zero_patch_is_reviewed(self):
        # x.y.0 is a feature release — never auto-dropped.
        self.assertIsNone(auto_drop_reason("PostgreSQL 19.2.0 released", NOISE))
        self.assertIsNone(auto_drop_reason("Rust 1.90 released", NOISE))

    def test_novelty_outranks_patch_shape(self):
        self.assertIsNone(auto_drop_reason("Announcing Zed 1.0.1", NOISE))
        self.assertIsNone(auto_drop_reason("Introducing Foo 3.1.4", NOISE))

    def test_security_outranks_patch_shape(self):
        self.assertIsNone(auto_drop_reason("Node.js 24.5.1 security release", NOISE))
        self.assertIsNone(auto_drop_reason("CVE-2026-1234 in libfoo 1.2.3", NOISE))
        self.assertIsNone(auto_drop_reason("Supply-chain attack on npm 9.8.7", NOISE))

    def test_capability_claim_outranks_patch_shape(self):
        # Real regressions found in a live crawl: feature posts whose only sin
        # was carrying a patch-shaped version number.
        self.assertIsNone(auto_drop_reason("New DuckDB-Iceberg Features in v1.5.3", NOISE))
        self.assertIsNone(auto_drop_reason("Foo 1.2.3 adds support for WebGPU", NOISE))
        self.assertIsNone(auto_drop_reason("Bar 2.1.4 now supports OpenTelemetry", NOISE))
        self.assertIsNone(auto_drop_reason("Baz 3.0.1: query engine rewritten in Rust", NOISE))

    def test_bare_patch_release_is_still_minor(self):
        # The capability override must not swallow the rule it guards.
        for title in [
            "PHP 8.4.22 Released!",
            "v16.3.1-canary.20",
            "svelte@5.56.9",
            "Node.js 22.23.1 (LTS)",
            "langgraph-checkpoint-sqlite==3.1.1",
        ]:
            self.assertEqual(auto_drop_reason(title, NOISE), "minor", title)

    def test_generic_release_note_verbs_do_not_rescue(self):
        # Measured at a 10% auto-drop rate on the 2026-08-21 scan: "adds",
        # "improves" and "faster" appear in nearly every patch note, so treating
        # them as capability claims disabled the rule they were meant to refine.
        for title in [
            "CodeQL 2.26.3 improves GitHub Actions queries",
            "Foo 1.2.3 adds a config flag",
            "Bar 4.5.6 is faster on cold start",
            "Baz 1.0.9 improved memory usage",
        ]:
            self.assertEqual(auto_drop_reason(title, NOISE), "minor", title)

    def test_ordinary_topic_is_reviewed(self):
        self.assertIsNone(auto_drop_reason("How we cut p99 latency in half", NOISE))

    def test_empty_title_drops(self):
        self.assertEqual(auto_drop_reason("   ", NOISE), "empty")


class Novelty(unittest.TestCase):
    def test_flags_arrival_change_and_death(self):
        for title in [
            "Announcing Bun 2.0",
            "Introducing a new inference runtime",
            "Postgres 19 is generally available",
            "Valkey graduated from the CNCF incubator",
            "Breaking changes in React 20",
            "Deprecating the v1 API",
            "Redis end-of-life for 6.x",
            "We are open-sourcing our scheduler",
            "Vite 8.0 release candidate",
        ]:
            self.assertTrue(is_novel(title), title)

    def test_does_not_flag_ordinary_prose(self):
        for title in ["Debugging a slow query", "Notes on distributed locks"]:
            self.assertFalse(is_novel(title), title)


class MergeItems(unittest.TestCase):
    def feed(self, fid="f1", cls="ai"):
        return {"id": fid, "class": cls}

    def test_every_item_is_accounted_for(self):
        raw = [
            {"title": "Announcing Foo 1.0", "url": "u1", "date": dt.date(2026, 5, 1)},
            {"title": "Our webinar next week", "url": "u2", "date": dt.date(2026, 5, 2)},
            {"title": "Bar 2.3.4 released", "url": "u3", "date": dt.date(2026, 5, 3)},
            {"title": "Announcing Foo 1.0", "url": "u4", "date": dt.date(2026, 5, 4)},
        ]
        reviewable, dropped = merge_items([(self.feed(), raw, "ok")], NOISE)
        self.assertEqual(len(reviewable) + len(dropped), len(raw))
        self.assertEqual([e["t"] for e in reviewable], ["Announcing Foo 1.0"])
        self.assertEqual(
            sorted(d["r"] for d in dropped), ["dupe", "minor", "noise"]
        )

    def test_dedupes_on_url_across_feeds(self):
        a = [{"title": "Same story, different headline", "url": "http://x/1", "date": dt.date(2026, 5, 1)}]
        b = [{"title": "Different headline entirely", "url": "http://x/1", "date": dt.date(2026, 5, 1)}]
        reviewable, dropped = merge_items(
            [(self.feed("f1"), a, "ok"), (self.feed("f2"), b, "ok")], NOISE
        )
        self.assertEqual(len(reviewable), 1)
        self.assertEqual(dropped[0]["r"], "dupe")

    def test_indexes_are_dense_and_newest_first(self):
        raw = [
            {"title": "older topic", "url": "u1", "date": dt.date(2026, 1, 1)},
            {"title": "newer topic", "url": "u2", "date": dt.date(2026, 6, 1)},
        ]
        reviewable, _ = merge_items([(self.feed(), raw, "ok")], NOISE)
        self.assertEqual([e["i"] for e in reviewable], [0, 1])
        self.assertEqual(reviewable[0]["t"], "newer topic")

    def test_carries_novelty_flag_points_and_tier(self):
        raw = [
            {
                "title": "Introducing Quux",
                "url": "u1",
                "date": dt.date(2026, 5, 1),
                "points": 310,
                "tier": "discovery",
            }
        ]
        reviewable, _ = merge_items([(self.feed("hn", "aggregator"), raw, "ok")], NOISE)
        entry = reviewable[0]
        self.assertEqual(entry["n"], 1)
        self.assertEqual(entry["p"], 310)
        self.assertEqual(entry["tier"], "discovery")
        self.assertEqual(entry["c"], "aggregator")
        self.assertEqual(flags_for(entry), "new+disc")

    def test_normalize_title_ignores_punctuation_and_case(self):
        self.assertEqual(
            normalize_title("Rust 1.90: What's New!"), normalize_title("rust 1 90 what s new")
        )


class FeedHealthMemory(unittest.TestCase):
    def test_errors_accumulate_and_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feed_health.json"
            day1 = [{"id": "a", "status": "error: timeout"}, {"id": "b", "status": "ok"}]
            update_feed_health(path, day1, dt.date(2026, 5, 1))
            self.assertEqual(day1[0]["consecutive_errors"], 1)
            self.assertEqual(day1[1]["last_ok"], "2026-05-01")

            day2 = [{"id": "a", "status": "error: timeout"}, {"id": "b", "status": "ok"}]
            update_feed_health(path, day2, dt.date(2026, 5, 8))
            self.assertEqual(day2[0]["consecutive_errors"], 2)  # registry fix needed
            self.assertEqual(day2[0]["last_ok"], "")

            day3 = [{"id": "a", "status": "ok"}]
            update_feed_health(path, day3, dt.date(2026, 5, 15))
            self.assertEqual(day3[0]["consecutive_errors"], 0)
            self.assertEqual(json.loads(path.read_text())["feeds"]["a"]["last_ok"], "2026-05-15")

    def test_missing_state_file_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            health = [{"id": "a", "status": "ok"}]
            update_feed_health(Path(tmp) / "nested" / "feed_health.json", health, dt.date.today())
            self.assertEqual(health[0]["consecutive_errors"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Offline tests for trader-gold: python3 -m unittest discover -s .claude/skills/trader-gold/tests

Fixtures: chart-*.json and news.xml are real Yahoo responses saved on
2026-10-22. calendar.json is hand-written in ForexFactory's export format.
"""

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
spec = importlib.util.spec_from_file_location("gold", os.path.join(HERE, "..", "gold.py"))
gold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gold)

NOW = dt.datetime(2026, 10, 22, 9, 45, tzinfo=dt.timezone.utc)  # 11:45 in Berlin


class GoldTest(unittest.TestCase):
    def setUp(self):
        self.f = gold.Fetcher(FIX)

    def test_quote(self):
        q = gold.quote(self.f)
        self.assertEqual(q["symbol"], "GC=F")
        self.assertGreater(q["price"], 1000)
        self.assertLessEqual(q["low_24h"], q["price"])
        self.assertGreaterEqual(q["high_24h"], q["price"])
        self.assertAlmostEqual(q["change"], q["price"] - q["prev_close"], places=2)

    def test_levels_use_completed_days_only(self):
        lv = gold.levels(self.f)
        _, daily = gold.parse_chart(self.f.get(None, "chart-daily.json"))
        self.assertEqual(lv["prev_close"], daily[-2]["c"])
        self.assertGreater(lv["atr14"], 0)
        self.assertLessEqual(lv["low20"], lv["high20"])

    def test_atr(self):
        bars = [{"h": 11, "l": 9, "c": 10}] * 15
        self.assertEqual(gold.atr(bars), 2)
        self.assertIsNone(gold.atr(bars[:5]))

    def test_news_filters_mining_noise_and_remembers(self):
        with tempfile.TemporaryDirectory() as d:
            state = os.path.join(d, "news.json")
            items, total, hidden = gold.news(self.f, NOW, 24, state_path=state)
            self.assertTrue(items)
            self.assertGreater(hidden, 0)
            self.assertTrue(all(i["relevant"] for i in items))
            self.assertFalse(any("Almadex" in i["title"] for i in items))
            self.assertTrue(any(i["source"] == "Investing.com" for i in items))
            again, _, _ = gold.news(self.f, NOW, 24, state_path=state)
            self.assertEqual(again, [])
            everything, _, none_hidden = gold.news(self.f, NOW, 24, show_all=True, state_path=state, everything=True)
            self.assertEqual(none_hidden, 0)
            self.assertGreater(len(everything), len(items))

    def test_calendar_filters_and_converts_to_berlin(self):
        ev = gold.calendar(self.f, NOW)
        titles = [e["title"] for e in ev]
        self.assertEqual(titles, ["Unemployment Claims", "Existing Home Sales",
                                  "Core PCE Price Index m/m", "Revised UoM Consumer Sentiment"])
        self.assertTrue(ev[0]["time"].startswith("2026-10-22T14:30:00+02:00"))
        self.assertTrue(ev[0]["gold_mover"])
        self.assertFalse(ev[1]["gold_mover"])
        self.assertFalse(ev[0]["past"])

    def test_calendar_countries_and_impact(self):
        ev = gold.calendar(self.f, NOW, countries=("EUR",), impacts=("High",))
        self.assertEqual([e["title"] for e in ev], ["Flash Manufacturing PMI"])

    def test_calendar_render_marks_next(self):
        out = gold.render_calendar(gold.calendar(self.f, NOW), NOW)
        self.assertIn("Donnerstag 22.10.  (heute)", out)
        self.assertIn("NÄCHSTER, in 2h 45min", out)

    def test_main_brief_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = gold.main(["--offline", FIX, "--now", NOW.isoformat(), "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["errors"], [])
        self.assertIn("quote", data)
        self.assertIn("levels", data)
        self.assertIn("calendar", data)

    def test_german_number_format(self):
        self.assertEqual(gold.money(4101.8), "$4.101,80")
        self.assertEqual(gold.de(-1.2), "-1,20")


if __name__ == "__main__":
    unittest.main()

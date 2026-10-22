"""Offline tests for the gold breakout signals.

chart-60d.json holds real GC=F 5-minute bars for 13-15 Oct 2026 (Berlin
dates); chart-1y.json real daily bars. On 14 Oct the rules gave a SELL at
10:45 that reached its 1.5R target at 14:30.
"""

import datetime as dt
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(HERE, ".."))
spec = importlib.util.spec_from_file_location("signals", os.path.join(HERE, "..", "signals.py"))
signals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signals)
gold = signals.gold

UTC = dt.timezone.utc


def at(hour, minute=0, day=14):
    return dt.datetime(2026, 10, day, hour, minute, tzinfo=UTC)


class SignalTest(unittest.TestCase):
    def setUp(self):
        self.f = gold.Fetcher(FIX)

    def test_waiting_before_breakout(self):
        r = signals.scan(self.f, at(7, 30))  # 09:30 Berlin
        self.assertEqual(r["state"], "waiting")
        self.assertEqual(r["trend"], "down")
        self.assertIn("unter", r["reason"])

    def test_sell_signal_and_target(self):
        r = signals.scan(self.f, at(9))
        self.assertEqual(r["state"], "signal")
        s = r["signal"]
        self.assertEqual(s["side"], "SELL")
        self.assertEqual(s["time"][11:16], "10:45")
        self.assertAlmostEqual(s["stop"], round((r["asia_high"] + r["asia_low"]) / 2, 1))
        self.assertLess(s["target"], s["entry"])
        self.assertIsNone(r["outcome"])  # not yet
        done = signals.scan(self.f, at(19, 30))
        self.assertEqual(done["outcome"]["result"], "target")
        self.assertEqual(done["outcome"]["r"], 1.5)

    def test_no_lookahead(self):
        # At 10:44 Berlin the signal bar (10:40-10:45) is not complete yet.
        r = signals.scan(self.f, at(8, 44))
        self.assertEqual(r["state"], "waiting")

    def test_pushes_once(self):
        state = {}
        first = signals.push_messages(signals.scan(self.f, at(9)), state)
        self.assertEqual(len(first), 1)
        self.assertIn("VERKAUFEN", first[0]["title"])
        self.assertEqual(signals.push_messages(signals.scan(self.f, at(10)), state), [])
        last = signals.push_messages(signals.scan(self.f, at(19, 30)), state)
        self.assertEqual(len(last), 1)
        self.assertIn("ZIEL", last[0]["title"])
        self.assertEqual(signals.push_messages(signals.scan(self.f, at(19, 45)), state), [])

    def test_calendar_blocks_signal(self):
        now = at(9)
        ev = [{"impact": "High", "gold_mover": True, "title": "CPI m/m",
               "time": (now + dt.timedelta(minutes=20)).isoformat()}]
        self.assertEqual(signals.blocked_by_calendar(ev, now)["title"], "CPI m/m")
        ev[0]["time"] = (now + dt.timedelta(minutes=90)).isoformat()
        self.assertIsNone(signals.blocked_by_calendar(ev, now))
        r = signals.scan(self.f, now)
        r["blocked_by"] = {"title": "CPI m/m", "time": "2026-10-14T11:00:00+02:00"}
        msgs = signals.push_messages(r, {})
        self.assertEqual(len(msgs), 1)
        self.assertIn("Termin", msgs[0]["title"])

    def test_range_filter(self):
        bars = [{"t": int(at(h - 2, 0).timestamp()), "o": 100, "h": 100.5, "l": 99.5, "c": 100, "v": 0}
                for h in range(2, 8)]  # 02:00-07:00 Berlin
        ctx = {"atr": 50.0, "sma20": 90.0, "close": 100.0}
        r = signals.evaluate_day(bars, ctx)
        self.assertEqual(r["state"], "no-trade")
        self.assertIn("zu eng", r["reason"])

    def test_backtest_runs(self):
        bt = signals.backtest(self.f, at(23, 0, day=15) + dt.timedelta(days=1))
        self.assertGreaterEqual(bt["n"], 1)
        self.assertTrue(any(t["day"] == "2026-10-14" and t["result"] == "target" for t in bt["trades"]))


if __name__ == "__main__":
    unittest.main()

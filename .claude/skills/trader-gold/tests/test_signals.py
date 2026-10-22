"""Offline tests for the engine, the setups and the live signal pushes.

fixtures/live holds real Yahoo bars saved on 2026-10-22 around 12:10 German
time (GC=F, DX-Y.NYB, ^TNX, SI=F in 5m/15m/1h, GC=F daily). On that morning
trend_vwap_pullback gave a 1h SELL at 11:00 at $4,099.10.
"""

import datetime as dt
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..")
LIVE = os.path.join(HERE, "fixtures", "live")
sys.path.insert(0, SKILL)
spec = importlib.util.spec_from_file_location("signals", os.path.join(SKILL, "signals.py"))
signals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signals)
engine, gold, research = signals.engine, signals.gold, signals.research

UTC = dt.timezone.utc


def at(h, m=0):
    return dt.datetime(2026, 10, 22, h, m, tzinfo=UTC)


def bars(rows, start, step=3600):
    """rows of (o, h, l, c) -> Bars starting at `start` (aware datetime)."""
    t0 = int(start.timestamp())
    cols = list(zip(*rows))
    return engine.Bars([t0 + k * step for k in range(len(rows))], list(cols[0]), list(cols[1]),
                       list(cols[2]), list(cols[3]), [0] * len(rows), step)


class EngineTest(unittest.TestCase):
    def ctx(self, rows, start=dt.datetime(2026, 10, 20, 7, 0, tzinfo=UTC)):  # 09:00 Berlin
        return engine.Ctx(bars(rows, start))

    def test_stop_wins_when_bar_touches_both(self):
        c = self.ctx([(100, 101, 99, 100), (100, 106, 94, 100), (100, 100, 100, 100)])
        t = engine.simulate(c, [engine.signal(0, 1, 95, 105)], "x", cost=0)
        self.assertEqual(t[0]["result"], "stop")
        self.assertEqual(t[0]["r"], -1)

    def test_gap_through_stop_fills_at_open(self):
        c = self.ctx([(100, 101, 99, 100), (90, 91, 89, 90), (90, 90, 90, 90)])
        t = engine.simulate(c, [engine.signal(0, 1, 95, 110)], "x", cost=0)
        self.assertEqual(t[0]["r"], -2)

    def test_target_and_cost(self):
        c = self.ctx([(100, 101, 99, 100), (100, 111, 100, 110), (110, 110, 110, 110)])
        t = engine.simulate(c, [engine.signal(0, 1, 95, 110)], "x", cost=0.5)
        self.assertEqual(t[0]["result"], "target")
        self.assertAlmostEqual(t[0]["r"], 1.9)

    def test_flat_at_22_and_window(self):
        start = dt.datetime(2026, 10, 20, 17, 0, tzinfo=UTC)  # 19:00 Berlin, bar ends 20:00
        c = self.ctx([(100, 101, 99, 100), (100, 101, 99, 101), (101, 102, 100, 102), (102, 102, 102, 102)], start)
        t = engine.simulate(c, [engine.signal(0, 1, 90, 120), engine.signal(1, 1, 90, 120)], "x", cost=0)
        self.assertEqual(len(t), 1)  # the bar ending 21:00 is outside 08:00-20:00
        self.assertEqual(t[0]["result"], "flat")
        self.assertEqual(t[0]["exit_i"], 2)  # the 21:00-22:00 bar is the last one

    def test_keep_open_on_last_bar(self):
        c = self.ctx([(100, 101, 99, 100), (100, 101, 99, 100)])
        self.assertEqual(engine.simulate(c, [engine.signal(1, 1, 95, 110)], "x"), [])
        t = engine.simulate(c, [engine.signal(1, 1, 95, 110)], "x", keep_open=True)
        self.assertIsNone(t[0]["result"])

    def test_trim_drops_forming_bar(self):
        b = bars([(1, 1, 1, 1)] * 3, at(8))
        self.assertEqual(engine.trim(b, int(at(10, 30).timestamp())).n, 2)


class SetupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctxs = signals.load_live(gold.Fetcher(LIVE), at(10), ["1h", "15m", "5m"])
        cls.reg = research.all_setups()

    def test_registry_tiers(self):
        live = research.all_setups(watch=False)
        self.assertIn("trend_vwap_pullback", live)
        self.assertTrue(research.watch_names())
        self.assertFalse(research.watch_names() & set(live))

    def test_no_lookahead(self):
        """A setup's signals up to bar k must not change when later bars are removed."""
        for name, (fn, tf, params) in sorted(self.reg.items()):
            full = self.ctxs[tf]
            sig_full = fn(full, **params)
            for cut in (full.b.n - 40, full.b.n - 13, full.b.n - 1):
                ts = full.b.t[cut - 1] + full.b.step
                part = engine.Ctx(engine.trim(full.b, ts), daily=full.daily,
                                  extras={k: engine.trim(v, ts) for k, v in full.extras.items()})
                a = [(s["i"], s["side"], round(s["stop"], 4)) for s in sig_full if s["i"] < cut]
                b = [(s["i"], s["side"], round(s["stop"], 4)) for s in fn(part, **params)]
                self.assertEqual(a, b, "%s @ %s changes with future bars (cut %d)" % (name, tf, cut))


class LiveTest(unittest.TestCase):
    def setUp(self):
        self.f = gold.Fetcher(LIVE)
        self.stats = signals.load_stats()

    def scan(self, now):
        return signals.scan(self.f, now)

    def test_vwap_pullback_sell_at_11(self):
        r = self.scan(at(9, 20))
        t = [x for x in r["trades"] if x["setup"] == "trend_vwap_pullback"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["side"], -1)
        self.assertEqual(t[0]["signal_time"][11:16], "11:00")
        self.assertAlmostEqual(t[0]["entry"], 4099.1, places=1)
        self.assertIsNone(t[0]["result"])

    def test_no_signal_before_bar_completes(self):
        r = self.scan(at(8, 59))
        self.assertFalse([x for x in r["trades"] if x["setup"] == "trend_vwap_pullback"])

    def test_push_once_with_stars_and_confluence(self):
        state = {}
        msgs = signals.push_messages(self.scan(at(9, 20)), state, self.stats, at(9, 20))
        self.assertEqual(len(msgs), 1)
        m = msgs[0]
        self.assertTrue(m["title"].startswith("Gold VERKAUFEN 11:00"))
        self.assertEqual(m["priority"], "high")
        self.assertIn("Bestätigt von 2 Setups", m["body"])
        self.assertEqual(signals.push_messages(self.scan(at(9, 35)), state, self.stats, at(9, 35)), [])

    def test_stale_signals_are_not_pushed(self):
        state = {}
        msgs = signals.push_messages(self.scan(at(10, 10)), state, self.stats, at(10, 10))
        self.assertEqual(msgs, [])
        self.assertTrue(state["sent"])

    def test_watch_only_is_low_priority(self):
        r = {"day": "2026-10-22", "trades": [], "blocked_by": None, "next_event": None, "headline": None}
        t = dict(setup="london_or", tf="15m", side=1, entry=100.0, stop=95.0, target=107.5, risk=5.0,
                 signal_time=at(8).isoformat(), key="k", result=None)
        r["trades"] = [t]
        msgs = signals.push_messages(r, {}, self.stats, at(8, 5))
        self.assertTrue(msgs[0]["title"].startswith("Gold Beobachtung: KAUFEN"))
        self.assertEqual(msgs[0]["priority"], "low")
        self.assertIn("EXPERIMENTELL", msgs[0]["body"])

    def test_outcome_pushed_once_after_signal(self):
        state = {}
        t = dict(setup="trend_vwap_pullback", tf="1h", side=-1, entry=100.0, stop=105.0, target=92.5, risk=5.0,
                 signal_time=at(9).isoformat(), key="k", result=None)
        r = {"day": "2026-10-22", "trades": [t], "blocked_by": None, "next_event": None, "headline": None}
        self.assertEqual(len(signals.push_messages(r, state, self.stats, at(9, 5))), 1)
        r["trades"] = [dict(t, result="target", r=1.42, exit_time="13:00")]
        out = signals.push_messages(r, state, self.stats, at(11, 5))
        self.assertEqual(len(out), 1)
        self.assertIn("ZIEL", out[0]["title"])
        self.assertEqual(signals.push_messages(r, state, self.stats, at(11, 20)), [])

    def test_calendar_block(self):
        now = at(9)
        ev = [{"impact": "High", "gold_mover": True, "title": "CPI m/m", "time": (now + dt.timedelta(minutes=20)).isoformat()}]
        self.assertEqual(signals.blocked_by_calendar(ev, now)["title"], "CPI m/m")
        ev[0]["time"] = (now + dt.timedelta(minutes=90)).isoformat()
        self.assertIsNone(signals.blocked_by_calendar(ev, now))
        t = dict(setup="trend_vwap_pullback", tf="1h", side=1, entry=100.0, stop=95.0, target=107.5, risk=5.0,
                 signal_time=now.isoformat(), key="k", result=None)
        r = {"day": "2026-10-22", "trades": [t], "next_event": None, "headline": None,
             "blocked_by": {"title": "CPI m/m", "time": "2026-10-22T11:20:00+02:00"}}
        msgs = signals.push_messages(r, {}, self.stats, now)
        self.assertIn("gesperrt", msgs[0]["title"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Backtest and signal engine for trader-gold. Standard library only.

A setup is a function `setup(ctx, **params) -> [Signal]` that looks at the
bars in `ctx` and returns entries. The engine simulates every entry the same
way (entry at the signal bar's close, stop/target on later bars, a bar that
touches both counts as the stop, flat at FLAT time, costs per ounce), keeps
one open trade per setup, and only accepts signals whose bar CLOSES between
WINDOW[0] and WINDOW[1] German time.

    from engine import Ctx, load_yahoo, simulate, metrics, report
    ctx = Ctx(load_yahoo(open("gc-1h.json","rb").read()), extras={"dxy": load_yahoo(...)})
    trades = simulate(ctx, my_setup(ctx), "my_setup")
    print(report("my_setup", trades, split="2026-01-01"))

Rules for setups (no lookahead): a signal at index i may only use data of
bars 0..i (their close included) and of extras with time <= ctx.t[i] + bar.
Use the helpers on Ctx; they are all causal.
"""

import bisect
import datetime as _dt
import json
import math
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
WINDOW = ((8, 0), (20, 0))  # signal bar must close inside this (Berlin)
FLAT = (22, 0)              # open trades are closed at the first bar at/after this
COST = 0.40                 # round-trip spread + slippage in $ per ounce


class Bars:
    def __init__(self, t, o, h, l, c, v, step):
        self.t, self.o, self.h, self.l, self.c, self.v, self.step = t, o, h, l, c, v, step
        self.n = len(t)
        loc = [_dt.datetime.fromtimestamp(x, BERLIN) for x in t]
        self.date = [x.date() for x in loc]
        self.hm = [(x.hour, x.minute) for x in loc]
        end = [_dt.datetime.fromtimestamp(x + step, BERLIN) for x in t]
        self.end_hm = [(x.hour, x.minute) for x in end]
        self.weekday = [x.weekday() for x in loc]


def trim(b, until_ts):
    """Only the bars that are complete at until_ts (Yahoo's last bar is still forming)."""
    k = 0
    while k < b.n and b.t[k] + b.step <= until_ts:
        k += 1
    return Bars(b.t[:k], b.o[:k], b.h[:k], b.l[:k], b.c[:k], b.v[:k], b.step)


def load_yahoo(data):
    """Yahoo chart JSON -> Bars, empty bars dropped. Step = median bar spacing."""
    res = json.loads(data)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    cols = ([], [], [], [], [], [])
    for i, ts in enumerate(res.get("timestamp") or []):
        row = (ts, q["open"][i], q["high"][i], q["low"][i], q["close"][i], (q.get("volume") or [0] * (i + 1))[i] or 0)
        if None in row[1:5]:
            continue
        for col, x in zip(cols, row):
            col.append(x)
    t = cols[0]
    gaps = sorted(b - a for a, b in zip(t, t[1:]) if b > a)
    step = gaps[len(gaps) // 2] if gaps else 300
    if step >= 86400:
        step = 86400
    return Bars(*cols, step=step)


# ---------------------------------------------------------------- indicators

def ema(x, n):
    out, k, e = [], 2 / (n + 1), None
    for v in x:
        e = v if e is None else e + k * (v - e)
        out.append(e)
    return out


def sma(x, n):
    out, s = [], 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def rma(x, n):
    out, r = [], None
    for i, v in enumerate(x):
        if v is None:
            out.append(r)
            continue
        r = v if r is None else (r * (n - 1) + v) / n
        out.append(r)
    return out


def true_range(b):
    return [b.h[0] - b.l[0]] + [max(b.h[i] - b.l[i], abs(b.h[i] - b.c[i - 1]), abs(b.l[i] - b.c[i - 1])) for i in range(1, b.n)]


def atr(b, n=14):
    return rma(true_range(b), n)


def rsi(x, n=14):
    up = [0.0] + [max(x[i] - x[i - 1], 0) for i in range(1, len(x))]
    dn = [0.0] + [max(x[i - 1] - x[i], 0) for i in range(1, len(x))]
    ru, rd = rma(up, n), rma(dn, n)
    return [100.0 if d == 0 else 100 - 100 / (1 + u / d) for u, d in zip(ru, rd)]


def stdev(x, n):
    m = sma(x, n)
    out = []
    for i in range(len(x)):
        if m[i] is None:
            out.append(None)
            continue
        w = x[i - n + 1:i + 1]
        out.append(math.sqrt(sum((v - m[i]) ** 2 for v in w) / n))
    return out


def adx(b, n=14):
    pdm, ndm = [0.0], [0.0]
    for i in range(1, b.n):
        up, dn = b.h[i] - b.h[i - 1], b.l[i - 1] - b.l[i]
        pdm.append(up if up > dn and up > 0 else 0.0)
        ndm.append(dn if dn > up and dn > 0 else 0.0)
    tr = rma(true_range(b), n)
    p, m = rma(pdm, n), rma(ndm, n)
    dx = []
    for i in range(b.n):
        if not tr[i]:
            dx.append(0.0)
            continue
        pdi, ndi = 100 * p[i] / tr[i], 100 * m[i] / tr[i]
        dx.append(0.0 if pdi + ndi == 0 else 100 * abs(pdi - ndi) / (pdi + ndi))
    return rma(dx, n)


def rolling_max(x, n):
    return [max(x[max(0, i - n + 1):i + 1]) for i in range(len(x))]


def rolling_min(x, n):
    return [min(x[max(0, i - n + 1):i + 1]) for i in range(len(x))]


# ---------------------------------------------------------------- context

class Ctx:
    """Bars plus causal helpers. Indicator results are cached by key."""

    def __init__(self, bars, daily=None, extras=None):
        self.b = bars
        self.daily = daily
        self.extras = extras or {}
        self._cache = {}

    def ind(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # session structure (Berlin calendar day)
    def day_start(self):
        """index of the first bar of each bar's Berlin day"""
        def f():
            out, s = [], 0
            for i in range(self.b.n):
                if i == 0 or self.b.date[i] != self.b.date[i - 1]:
                    s = i
                out.append(s)
            return out
        return self.ind("day_start", f)

    def range_between(self, start_hm, end_hm):
        """Per bar: (high, low) of today's bars that ENDED by end_hm and started at/after start_hm,
        available only once the bar's own end >= end_hm; else (None, None)."""
        key = ("range", start_hm, end_hm)

        def f():
            b, out = self.b, []
            hi = lo = None
            for i in range(b.n):
                if i == 0 or b.date[i] != b.date[i - 1]:
                    hi = lo = None
                if start_hm <= b.hm[i] and b.end_hm[i] <= end_hm and b.end_hm[i] > b.hm[i]:
                    hi = b.h[i] if hi is None else max(hi, b.h[i])
                    lo = b.l[i] if lo is None else min(lo, b.l[i])
                ready = b.end_hm[i] >= end_hm or b.end_hm[i] < b.hm[i]
                out.append((hi, lo) if ready else (None, None))
            return out
        return self.ind(key, f)

    def vwap(self):
        """Session VWAP from the Berlin day start (typical price; equal weights if no volume)."""
        def f():
            b, out = self.b, []
            pv = vv = 0.0
            for i in range(b.n):
                if i == 0 or b.date[i] != b.date[i - 1]:
                    pv = vv = 0.0
                w = b.v[i] or 1.0
                pv += w * (b.h[i] + b.l[i] + b.c[i]) / 3
                vv += w
                out.append(pv / vv)
            return out
        return self.ind("vwap", f)

    def prev_day(self):
        """Per bar: dict(high, low, close, atr, sma20, sma50) of the last completed daily bar
        before the bar's Berlin date (from ctx.daily), or None."""
        def f():
            d = self.daily
            if d is None:
                return [None] * self.b.n
            a = atr(d, 14)
            s20, s50 = sma(d.c, 20), sma(d.c, 50)
            dates = d.date
            out = []
            for i in range(self.b.n):
                k = bisect.bisect_left(dates, self.b.date[i]) - 1
                out.append(None if k < 0 else {"high": d.h[k], "low": d.l[k], "close": d.c[k], "atr": a[k],
                                               "sma20": s20[k], "sma50": s50[k]})
            return out
        return self.ind("prev_day", f)

    def extra_close(self, name):
        """Close of extra series `name` at the last of its bars that ended by this bar's end."""
        key = ("extra", name)

        def f():
            e = self.extras[name]
            ends = [t + e.step for t in e.t]
            out = []
            for i in range(self.b.n):
                k = bisect.bisect_right(ends, self.b.t[i] + self.b.step) - 1
                out.append(None if k < 0 else e.c[k])
            return out
        return self.ind(key, f)

    def in_window(self, i):
        e = self.b.end_hm[i]
        return WINDOW[0] <= e <= WINDOW[1] and self.b.weekday[i] < 5


def signal(i, side, stop, target, tag="", **info):
    return dict(i=i, side=side, stop=stop, target=target, tag=tag, **info)


# ---------------------------------------------------------------- simulation

def simulate(ctx, signals, name, cost=COST, flat=FLAT, max_bars=None, keep_open=False, mgmt=None):
    """One trade at a time per setup. Returns list of trade dicts with r (net of cost).
    keep_open: also return a trade still open at the end of the data (result None).

    mgmt (optional trade management, all distances in R = entry-to-stop risk):
      be_r:        once price went be_r R in favour, the stop moves to entry
      trail_start: once price went this many R in favour, the stop trails ...
      trail_r:     ... trail_r R behind the best price since entry
      partial:     (fraction, at_r) - book this fraction at at_r R, the rest runs on
      overnight:   True - no flat at `flat` / day change; use max_bars to cap the hold
    Order inside a bar (conservative): flat, stop, partial, target; stop updates from a
    bar's extremes apply from the next bar on."""
    m = mgmt or {}
    be_r, trail_start, trail_r = m.get("be_r"), m.get("trail_start"), m.get("trail_r")
    part_frac, part_r = m.get("partial") or (0.0, None)
    overnight = m.get("overnight", False)
    b = ctx.b
    trades, busy_until = [], -1
    for s in sorted(signals, key=lambda s: s["i"]):
        i = s["i"]
        if i <= busy_until or not ctx.in_window(i) or (i >= b.n - 1 and not keep_open):
            continue
        side, entry, stop0, target = s["side"], b.c[i], s["stop"], s["target"]
        risk = (entry - stop0) * side
        if risk <= 0 or (target - entry) * side <= 0:
            continue
        stop, best, booked, left = stop0, entry, 0.0, 1.0
        part_px = entry + side * part_r * risk if part_r else None
        exit_i, result = None, None
        j = i + 1
        while j < b.n:
            ends_day = not overnight and (b.date[j] != b.date[i] or b.hm[j] >= flat)
            if ends_day or (max_bars and j - i > max_bars):
                booked += left * (b.c[j - 1] - entry) * side
                exit_i, result = j - 1, "flat"
                break
            if (b.l[j] <= stop) if side > 0 else (b.h[j] >= stop):
                px = min(stop, b.o[j]) if side > 0 else max(stop, b.o[j])  # a gap fills at the open
                booked += left * (px - entry) * side
                exit_i, result = j, "stop" if stop == stop0 else "trail" if (stop - entry) * side > 1e-9 else "be"
                break
            if part_px is not None and left == 1.0 and ((b.h[j] >= part_px) if side > 0 else (b.l[j] <= part_px)):
                booked += part_frac * (part_px - entry) * side
                left -= part_frac
            if (b.h[j] >= target) if side > 0 else (b.l[j] <= target):
                booked += left * (target - entry) * side
                exit_i, result = j, "target"
                break
            best = max(best, b.h[j]) if side > 0 else min(best, b.l[j])
            gain = (best - entry) * side / risk
            if be_r is not None and gain >= be_r:
                stop = max(stop, entry) if side > 0 else min(stop, entry)
            if trail_r is not None and gain >= (trail_start or 0):
                ts = best - side * trail_r * risk
                stop = max(stop, ts) if side > 0 else min(stop, ts)
            j += 1
        if exit_i is None:  # still open at the end of the data
            if keep_open:
                trades.append(dict(setup=name, tag=s.get("tag", ""), i=i, t=b.t[i], date=b.date[i].isoformat(),
                                   time="%02d:%02d" % b.end_hm[i], side=side, entry=entry, stop=stop0,
                                   target=target, risk=risk, result=None, exit_i=None, r=None))
            break
        r = (booked - cost) / risk
        trades.append(dict(setup=name, tag=s.get("tag", ""), i=i, t=b.t[i], date=b.date[i].isoformat(),
                           time="%02d:%02d" % b.end_hm[i], side=side, entry=entry, stop=stop0, target=target,
                           risk=risk, result=result, exit_i=exit_i, r=round(r, 3)))
        busy_until = exit_i
    return trades


def metrics(trades):
    n = len(trades)
    if not n:
        return dict(n=0)
    rs = [t["r"] for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [-r for r in rs if r < 0]
    eq = peak = dd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    days = sorted({t["date"] for t in trades})
    span = (_dt.date.fromisoformat(days[-1]) - _dt.date.fromisoformat(days[0])).days + 1
    return dict(n=n, win=round(len(wins) / n, 3), avg_r=round(sum(rs) / n, 3), total_r=round(sum(rs), 2),
                pf=round(sum(wins) / sum(losses), 2) if losses else float("inf"),
                max_dd=round(dd, 2), per_week=round(n / max(span / 7, 1), 2))


def split(trades, date):
    return [t for t in trades if t["date"] < date], [t for t in trades if t["date"] >= date]


def report(name, trades, split_date=None):
    def line(label, m):
        if not m.get("n"):
            return "  %-4s n=0" % label
        return "  %-4s n=%-4d win %3.0f%%  avg %+.2fR  total %+7.2fR  PF %.2f  maxDD %.1fR  %.1f/Woche" % (
            label, m["n"], m["win"] * 100, m["avg_r"], m["total_r"], m["pf"], m["max_dd"], m["per_week"])
    out = [name, line("ALL", metrics(trades))]
    if split_date:
        a, b = split(trades, split_date)
        out += [line("IS", metrics(a)), line("OOS", metrics(b))]
    return "\n".join(out)

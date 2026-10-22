"""Breakout setups for gold: session opening ranges, previous-day levels,
volatility squeeze and Donchian channel breaks. All causal: a signal at bar i
uses bars 0..i only."""

from engine import atr, ema, signal, sma, stdev


def _trend_ok(d, side, mode):
    """Daily trend filter from the last completed day: 'sma20', 'none'."""
    if mode == "none":
        return True
    if d is None or d["sma20"] is None:
        return False
    return (d["close"] > d["sma20"]) == (side > 0)


def opening_range(ctx, start=(8, 0), end=(9, 0), last_entry=(13, 0), min_w=0.1, max_w=0.8,
                  target_r=1.5, stop="mid", trend="sma20", tag="or"):
    """Close beyond today's start-end range, once per day, in the daily trend."""
    b, rng, pd = ctx.b, ctx.range_between(start, end), ctx.prev_day()
    out, taken = [], set()
    for i in range(b.n):
        hi, lo = rng[i]
        d = pd[i]
        if hi is None or d is None or not d["atr"] or b.date[i] in taken:
            continue
        if b.end_hm[i] <= end or b.end_hm[i] > last_entry:
            continue
        w = (hi - lo) / d["atr"]
        if not (min_w <= w <= max_w):
            continue
        side = 1 if b.c[i] > hi else -1 if b.c[i] < lo else 0
        if not side or not _trend_ok(d, side, trend):
            continue
        taken.add(b.date[i])
        st = (hi + lo) / 2 if stop == "mid" else (lo if side > 0 else hi)
        out.append(signal(i, side, st, b.c[i] + side * target_r * abs(b.c[i] - st), tag))
    return out


def prev_day_break(ctx, last_entry=(18, 0), stop_atr=0.35, target_r=1.5, trend="sma20", max_ext=0.3):
    """First close beyond yesterday's high/low; stop a fraction of the daily ATR away.
    Skip if the close is already far (max_ext daily ATR) past the level."""
    b, pd = ctx.b, ctx.prev_day()
    out, taken = [], set()
    for i in range(1, b.n):
        d = pd[i]
        if d is None or not d["atr"] or b.end_hm[i] > last_entry:
            continue
        for side, lvl in ((1, d["high"]), (-1, d["low"])):
            key = (b.date[i], side)
            if key in taken:
                continue
            crossed = (b.c[i] > lvl) if side > 0 else (b.c[i] < lvl)
            before = b.date[i - 1] == b.date[i] and ((b.c[i - 1] > lvl) if side > 0 else (b.c[i - 1] < lvl))
            if not crossed or before:
                continue
            taken.add(key)
            if (b.c[i] - lvl) * side > max_ext * d["atr"] or not _trend_ok(d, side, trend):
                continue
            st = b.c[i] - side * stop_atr * d["atr"]
            out.append(signal(i, side, st, b.c[i] + side * target_r * stop_atr * d["atr"], "pdhl"))
    return out


def squeeze(ctx, n=20, bb_k=2.0, kc_k=1.5, min_bars=6, stop_atr=1.5, target_r=2.0, ema_n=50):
    """Bollinger bands inside Keltner channel for min_bars, then the first close
    outside the Bollinger band in the direction of the EMA."""
    b = ctx.b
    m = ctx.ind(("sma", n), lambda: sma(b.c, n))
    sd = ctx.ind(("std", n), lambda: stdev(b.c, n))
    a = ctx.ind(("atr", n), lambda: atr(b, n))
    e = ctx.ind(("ema", ema_n), lambda: ema(b.c, ema_n))
    out, run = [], 0
    for i in range(b.n):
        if m[i] is None or a[i] is None or i < ema_n:
            continue
        up, lo = m[i] + bb_k * sd[i], m[i] - bb_k * sd[i]
        inside = up < m[i] + kc_k * a[i] and lo > m[i] - kc_k * a[i]
        if inside:
            run += 1
            continue
        if run >= min_bars:
            side = 1 if b.c[i] > up and b.c[i] > e[i] else -1 if b.c[i] < lo and b.c[i] < e[i] else 0
            if side:
                st = b.c[i] - side * stop_atr * a[i]
                out.append(signal(i, side, st, b.c[i] + side * target_r * stop_atr * a[i], "squeeze"))
        run = 0
    return out


def donchian(ctx, n=20, ema_n=50, tr_min=1.0, stop_atr=1.5, target_r=2.0):
    """Close beyond the prior n-bar high/low, with the EMA, on a bar whose true
    range is at least tr_min x ATR (real expansion, not drift)."""
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    e = ctx.ind(("ema", ema_n), lambda: ema(b.c, ema_n))
    out = []
    for i in range(max(n, ema_n) + 1, b.n):
        hh, ll = max(b.h[i - n:i]), min(b.l[i - n:i])
        tr = max(b.h[i] - b.l[i], abs(b.h[i] - b.c[i - 1]), abs(b.l[i] - b.c[i - 1]))
        if a[i] is None or tr < tr_min * a[i]:
            continue
        side = 1 if b.c[i] > hh and b.c[i] > e[i] else -1 if b.c[i] < ll and b.c[i] < e[i] else 0
        if side:
            st = b.c[i] - side * stop_atr * a[i]
            out.append(signal(i, side, st, b.c[i] + side * target_r * stop_atr * a[i], "donchian"))
    return out


def london_or(ctx, **kw):
    p = dict(start=(8, 0), end=(9, 0), last_entry=(13, 0), tag="london_or")
    p.update(kw)
    return opening_range(ctx, **p)


def ny_or(ctx, **kw):
    p = dict(start=(14, 0), end=(15, 0), last_entry=(19, 0), tag="ny_or")
    p.update(kw)
    return opening_range(ctx, **p)


# Best in-sample variant of each (1h, before 2026). None reached the keep bar
# (1h IS PF >= 1.15 at n >= 80), so none is live. london_or and prev_day_break
# were strong out of sample (2026) but negative in 2024-25: regime-dependent.
CANDIDATES = {
    "london_or": (london_or, "15m", dict(end=(10, 0), stop="edge", min_w=0.2, max_w=1.0)),
    "ny_or": (ny_or, "15m", dict(stop="edge", trend="none")),
    "prev_day_break": (prev_day_break, "15m", dict(stop_atr=0.5, target_r=1.0)),
    "squeeze": (squeeze, "15m", dict(stop_atr=1.0, target_r=1.5)),
    "donchian": (donchian, "15m", {}),
}

SETUPS = {}  # all DROP; see CANDIDATES
# IS 2024-25 PF 0.82 (no target: 1.02) but OOS 2026 PF 2.91 (no target: 3.40): regime-dependent,
# experimental. Runs without a fixed target like the live setups.
WATCH = {"london_or": (london_or, "15m", dict(CANDIDATES["london_or"][2], target_r=50))}

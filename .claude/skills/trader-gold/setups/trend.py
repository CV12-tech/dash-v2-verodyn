"""Trend-following / continuation setups for gold.

All parameters are in bars or ATRs, so every setup runs on any timeframe.
Signals use only bars 0..i (causal helpers on Ctx plus running indicators).
"""

from engine import atr, ema, signal


def _daily_trend(d):
    """+1 / -1 / 0 from the last completed daily bar: close vs SMA20 and SMA20 vs SMA50."""
    if d is None or d["sma20"] is None or d["sma50"] is None:
        return 0
    if d["close"] > d["sma20"] > d["sma50"]:
        return 1
    if d["close"] < d["sma20"] < d["sma50"]:
        return -1
    return 0


def _common(ctx):
    b = ctx.b
    return (b, ctx.ind("ema20", lambda: ema(b.c, 20)), ctx.ind("ema50", lambda: ema(b.c, 50)),
            ctx.ind("atr14", lambda: atr(b, 14)), ctx.prev_day())


def ema_pullback(ctx, lookback=5, touch=0.1, stop_pad=0.2, target_r=1.5, daily=True):
    """Trend: EMA20 > EMA50 and close > EMA50 (mirror for short), aligned with the daily
    trend. Pullback: a low within `touch` ATR of EMA20 in the last `lookback` bars.
    Entry: a bar closing above the previous bar's high and above EMA20.
    Stop: lowest low of the pullback minus `stop_pad` ATR. Target: `target_r` R."""
    b, e20, e50, a, pd = _common(ctx)
    out = []
    for i in range(60, b.n):
        if not a[i]:
            continue
        dt = _daily_trend(pd[i])
        lo_w, hi_w = min(b.l[i - lookback:i]), max(b.h[i - lookback:i])
        if e20[i] > e50[i] and b.c[i] > e50[i] and (dt == 1 or not daily):
            touched = any(b.l[k] <= e20[k] + touch * a[k] for k in range(i - lookback, i))
            if touched and b.c[i] > b.h[i - 1] and b.c[i] > e20[i]:
                stop = lo_w - stop_pad * a[i]
                out.append(signal(i, 1, stop, b.c[i] + target_r * (b.c[i] - stop), "ema_pb"))
        elif e20[i] < e50[i] and b.c[i] < e50[i] and (dt == -1 or not daily):
            touched = any(b.h[k] >= e20[k] - touch * a[k] for k in range(i - lookback, i))
            if touched and b.c[i] < b.l[i - 1] and b.c[i] < e20[i]:
                stop = hi_w + stop_pad * a[i]
                out.append(signal(i, -1, stop, b.c[i] - target_r * (stop - b.c[i]), "ema_pb"))
    return out


def vwap_pullback(ctx, lookback=4, touch=0.15, stop_pad=0.2, target_r=1.5, min_above=0.6):
    """Trend day: session VWAP slope up and price closed above VWAP on at least
    `min_above` of today's bars so far; the daily trend agrees (or is neutral).
    Pullback: a low within `touch` ATR of VWAP in the last `lookback` bars.
    Entry: close back above VWAP and above the previous high. Stop: pullback low
    minus `stop_pad` ATR. Mirror for short."""
    b, e20, e50, a, pd = _common(ctx)
    vw, ds = ctx.vwap(), ctx.day_start()
    out = []
    above = 0
    for i in range(b.n):
        if i == ds[i]:
            above = 0
        above += b.c[i] > vw[i]
        cnt = i - ds[i] + 1
        if cnt < max(lookback + 2, 3) or not a[i]:
            continue
        frac = above / cnt
        dt = _daily_trend(pd[i])
        lo_w, hi_w = min(b.l[i - lookback:i]), max(b.h[i - lookback:i])
        if frac >= min_above and vw[i] > vw[i - lookback] and dt >= 0:
            touched = any(b.l[k] <= vw[k] + touch * a[k] for k in range(i - lookback, i))
            if touched and b.c[i] > vw[i] and b.c[i] > b.h[i - 1]:
                stop = min(lo_w, b.l[i]) - stop_pad * a[i]
                out.append(signal(i, 1, stop, b.c[i] + target_r * (b.c[i] - stop), "vwap_pb"))
        elif frac <= 1 - min_above and vw[i] < vw[i - lookback] and dt <= 0:
            touched = any(b.h[k] >= vw[k] - touch * a[k] for k in range(i - lookback, i))
            if touched and b.c[i] < vw[i] and b.c[i] < b.l[i - 1]:
                stop = max(hi_w, b.h[i]) + stop_pad * a[i]
                out.append(signal(i, -1, stop, b.c[i] - target_r * (stop - b.c[i]), "vwap_pb"))
    return out


def momentum_cont(ctx, move=0.5, n_break=6, stop_atr=1.0, target_r=1.5):
    """Strong trend-day start: price has moved at least `move` daily ATR from the
    Berlin day's open in the daily trend's direction. Entry: a close above the
    highest high of the previous `n_break` bars (new high of the move). Stop:
    `stop_atr` bar-ATR below the entry. Mirror for short. One signal per side
    and day."""
    b, e20, e50, a, pd = _common(ctx)
    ds = ctx.day_start()
    out, taken = [], set()
    for i in range(n_break + 1, b.n):
        d = pd[i]
        if d is None or not d["atr"] or not a[i] or i - ds[i] < 2:
            continue
        dt = _daily_trend(d)
        day_open = b.o[ds[i]]
        mv = (b.c[i] - day_open) / d["atr"]
        key = (b.date[i], dt)
        if key in taken:
            continue
        if dt == 1 and mv >= move and b.c[i] > max(b.h[i - n_break:i]):
            stop = b.c[i] - stop_atr * a[i]
            out.append(signal(i, 1, stop, b.c[i] + target_r * (b.c[i] - stop), "mom"))
            taken.add(key)
        elif dt == -1 and mv <= -move and b.c[i] < min(b.l[i - n_break:i]):
            stop = b.c[i] + stop_atr * a[i]
            out.append(signal(i, -1, stop, b.c[i] - target_r * (stop - b.c[i]), "mom"))
            taken.add(key)
    return out


# Research verdicts (1h IS < 2026-01-01, OOS = 2026 and the last 60 days of 15m/5m):
#   trend_vwap_pullback  KEEP  IS PF 1.54 n=261, OOS PF 1.29 n=137, 15m PF 1.14
#   trend_ema_pullback   DROP  IS PF 1.23 n=179 but OOS PF 0.86 n=80
#   trend_momentum       DROP  IS PF 0.86 n=70
SETUPS = {
    "trend_vwap_pullback": (vwap_pullback, "1h", {}),
    # "trend_ema_pullback": (ema_pullback, "1h", {"target_r": 2.0}),
    # "trend_momentum": (momentum_cont, "1h", {}),
}
# Same rule on 15m: only 60 days of data (n=33, PF 1.14), so experimental.
WATCH = {"trend_vwap_pullback_15m": (vwap_pullback, "15m", {})}

"""Reversal / mean-reversion setups: liquidity sweeps, failed breakouts, range extremes."""

from engine import adx, atr, ema, rsi, signal, sma, stdev


def _trend_ok(ctx, i, side, trend):
    """trend=None: both sides; "with": only the side of the daily trend (prev close vs SMA20)."""
    if not trend:
        return True
    d = ctx.prev_day()[i]
    if d is None or d["sma20"] is None:
        return False
    up = d["close"] > d["sma20"]
    return (side > 0) == up


def _bar_atr(ctx, n=14):
    return ctx.ind(("atr", n), lambda: atr(ctx.b, n))


def _sweep(ctx, levels, i, buf):
    """Short if the bar pierced a high level and closed back below; long mirror.
    levels: (high_level, low_level). Returns side and the extreme."""
    b = ctx.b
    hi, lo = levels
    if hi is not None and b.h[i] > hi + buf and b.c[i] < hi and b.c[i] < b.o[i]:
        return -1, b.h[i]
    if lo is not None and b.l[i] < lo - buf and b.c[i] > lo and b.c[i] > b.o[i]:
        return 1, b.l[i]
    return 0, None


def sweep_pdhl(ctx, target_r=1.5, stop_buf=0.1, pierce=0.0, max_per_day=2, trend=None):
    """Sweep of the previous day's high/low that closes back inside (bearish/bullish bar)."""
    b, pd, a = ctx.b, ctx.prev_day(), _bar_atr(ctx)
    out, count, used = [], {}, set()
    for i in range(1, b.n):
        d = pd[i]
        if d is None or not a[i] or not d["atr"]:
            continue
        side, ext = _sweep(ctx, (d["high"], d["low"]), i, pierce * a[i])
        key = (b.date[i], side)
        if not side or not _trend_ok(ctx, i, side, trend) or key in used or count.get(b.date[i], 0) >= max_per_day:
            continue
        stop = ext + side * -1 * stop_buf * a[i]
        risk = (b.c[i] - stop) * side
        if risk <= 0 or risk > 2.5 * a[i]:
            continue
        used.add(key)
        count[b.date[i]] = count.get(b.date[i], 0) + 1
        out.append(signal(i, side, stop, b.c[i] + side * target_r * risk, "pdhl-sweep"))
    return out


def sweep_asia(ctx, target_r=1.5, stop_buf=0.1, pierce=0.0, trend=None):
    """After 08:00: sweep of the Asia high/low (00-08) that closes back inside the range."""
    b, rng, a = ctx.b, ctx.range_between((0, 0), (8, 0)), _bar_atr(ctx)
    out, used = [], set()
    for i in range(1, b.n):
        hi, lo = rng[i]
        if hi is None or not a[i] or b.hm[i] < (8, 0):
            continue
        side, ext = _sweep(ctx, (hi, lo), i, pierce * a[i])
        if not side or not _trend_ok(ctx, i, side, trend) or (b.date[i], side) in used:
            continue
        stop = ext - side * stop_buf * a[i]
        risk = (b.c[i] - stop) * side
        if risk <= 0 or risk > 2.5 * a[i]:
            continue
        used.add((b.date[i], side))
        out.append(signal(i, side, stop, b.c[i] + side * target_r * risk, "asia-sweep"))
    return out


def range_extreme(ctx, rsi_n=2, rsi_lo=10, adx_max=20, bb_n=20, bb_k=2.0, stop_atr=1.0, target_r=1.0, trend=None):
    """Sideways regime (ADX low): RSI(2) extreme outside a Bollinger band, fade back."""
    b, a = ctx.b, _bar_atr(ctx)
    r = ctx.ind(("rsi", rsi_n), lambda: rsi(b.c, rsi_n))
    ad = ctx.ind(("adx", 14), lambda: adx(b, 14))
    m = ctx.ind(("sma", bb_n), lambda: sma(b.c, bb_n))
    sd = ctx.ind(("sd", bb_n), lambda: stdev(b.c, bb_n))
    out = []
    for i in range(bb_n, b.n):
        if m[i] is None or sd[i] is None or not a[i] or ad[i] is None or ad[i] > adx_max:
            continue
        if r[i] < rsi_lo and b.c[i] < m[i] - bb_k * sd[i]:
            side = 1
        elif r[i] > 100 - rsi_lo and b.c[i] > m[i] + bb_k * sd[i]:
            side = -1
        else:
            continue
        if not _trend_ok(ctx, i, side, trend):
            continue
        stop = b.c[i] - side * stop_atr * a[i]
        out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "range-extreme"))
    return out


def vwap_fade(ctx, k=2.0, min_bars=6, stop_atr=0.8, target="vwap", target_r=1.0, trend=None):
    """Price stretched k sigma from the session VWAP, reversal bar closes back toward it."""
    b, vw, a = ctx.b, ctx.vwap(), _bar_atr(ctx)
    start = ctx.day_start()
    out = []
    s2 = n = 0
    for i in range(b.n):
        if i == start[i]:
            s2 = n = 0
        dev = b.c[i] - vw[i]
        s2 += dev * dev
        n += 1
        if n < min_bars or not a[i]:
            continue
        sig = (s2 / n) ** 0.5
        if sig <= 0:
            continue
        prev_dev = b.c[i - 1] - vw[i - 1]
        if prev_dev > k * sig and b.c[i] < b.o[i] and b.c[i] < b.c[i - 1]:
            side = -1
        elif prev_dev < -k * sig and b.c[i] > b.o[i] and b.c[i] > b.c[i - 1]:
            side = 1
        else:
            continue
        if not _trend_ok(ctx, i, side, trend):
            continue
        ext = max(b.h[i], b.h[i - 1]) if side < 0 else min(b.l[i], b.l[i - 1])
        stop = ext - side * 0.1 * a[i]
        risk = (b.c[i] - stop) * side
        if risk <= 0:
            continue
        tgt = vw[i] if target == "vwap" else b.c[i] + side * target_r * risk
        if (tgt - b.c[i]) * side < 0.5 * risk:
            continue
        out.append(signal(i, side, stop, tgt, "vwap-fade"))
    return out


# All four failed the keep rule (1h in-sample PF >= 1.15): in the 2024-25 gold
# bull trend, fading moves lost. Kept here for reference, not registered.
# Best in-sample variants, 1h IS PF: sweep_pdhl 0.76, sweep_asia 0.83,
# range_extreme 0.75, vwap_fade (trend "with", 1.5R) 1.02.
SETUPS = {
    # "sweep_pdhl": (sweep_pdhl, "1h", {}),
    # "sweep_asia": (sweep_asia, "1h", {"target_r": 2.0}),
    # "range_extreme": (range_extreme, "1h", {"adx_max": 25}),
    # "vwap_fade": (vwap_fade, "1h", {"trend": "with", "target": "r", "target_r": 1.5}),
}
# Closest miss: IS PF 1.02, OOS PF 1.26, 15m PF 1.47. Experimental.
WATCH = {"vwap_fade": (vwap_fade, "1h", {"trend": "with", "target": "r", "target_r": 1.5})}

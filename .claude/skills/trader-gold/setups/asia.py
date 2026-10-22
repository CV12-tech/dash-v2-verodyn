"""Asia-range breakout (the original trader-gold rule)."""

from engine import signal


def asia_breakout(ctx, min_w=0.25, max_w=1.0, target_r=1.5, last_entry=(16, 0), trend=True):
    b, rng, pd = ctx.b, ctx.range_between((0, 0), (8, 0)), ctx.prev_day()
    out, taken = [], set()
    for i in range(b.n):
        hi, lo = rng[i]
        d = pd[i]
        if hi is None or d is None or not d["atr"] or d["sma20"] is None or b.date[i] in taken:
            continue
        if b.end_hm[i] <= (8, 0) or b.end_hm[i] > last_entry:
            continue
        w = (hi - lo) / d["atr"]
        if not (min_w <= w <= max_w):
            continue
        up = d["close"] > d["sma20"]
        side = 1 if b.c[i] > hi and (up or not trend) else -1 if b.c[i] < lo and (not up or not trend) else 0
        if side:
            taken.add(b.date[i])
            stop = (hi + lo) / 2
            out.append(signal(i, side, stop, b.c[i] + side * target_r * abs(b.c[i] - stop), "asia"))
    return out


# 2.4 years of 1h bars: IS 2024-25 PF 0.88, OOS 2026 PF 1.66. Regime-dependent.
SETUPS = {}
WATCH = {}

"""Intermarket setups: gold confirmed or led by the dollar index (dxy),
10-year yield (tnx) and silver (si). All access to extras is causal via
ctx.extra_close(); a timeframe without the extra simply yields no signals."""

from engine import atr, ema, signal
from setups.asia import asia_breakout


def _extra(ctx, name):
    if name not in ctx.extras:
        return None
    return ctx.extra_close(name)


def _ret(x, i, k):
    """Relative change of series x over k bars ending at i, or None."""
    if i - k < 0 or x[i] is None or x[i - k] is None or x[i - k] == 0:
        return None
    return x[i] / x[i - k] - 1


def _hh(x, i, n):
    """Highest of x[i-n .. i-1] (excludes bar i), None if any missing."""
    w = x[max(0, i - n):i]
    if len(w) < n or any(v is None for v in w):
        return None
    return max(w)


def _ll(x, i, n):
    w = x[max(0, i - n):i]
    if len(w) < n or any(v is None for v in w):
        return None
    return min(w)


def dxy_momentum(ctx, n=12, k=4, dxy_min=0.0005, stop_atr=1.0, target_r=1.5, fast=20, slow=50):
    """Gold closes at an n-bar high (low) in an EMA uptrend (downtrend) while the
    dollar index fell (rose) at least dxy_min over the last k bars."""
    dxy = _extra(ctx, "dxy")
    if dxy is None:
        return []
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    ef = ctx.ind(("ema", fast), lambda: ema(b.c, fast))
    es = ctx.ind(("ema", slow), lambda: ema(b.c, slow))
    out = []
    for i in range(max(n, slow), b.n):
        if not ctx.in_window(i) or not a[i]:
            continue
        r = _ret(dxy, i, k)
        if r is None:
            continue
        hh, ll = max(b.h[i - n:i]), min(b.l[i - n:i])
        side = 0
        if b.c[i] > hh and ef[i] > es[i] and r <= -dxy_min:
            side = 1
        elif b.c[i] < ll and ef[i] < es[i] and r >= dxy_min:
            side = -1
        if side:
            stop = b.c[i] - side * stop_atr * a[i]
            out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "dxy_mom", dxy_ret=r))
    return out


def dxy_divergence(ctx, k=4, z=2.0, lag=0.25, stop_atr=1.0, target_r=1.5, look=100):
    """The dollar made an unusually large k-bar move (z-score vs. its own recent
    k-bar moves) while gold moved less than `lag` of what its usual inverse
    reaction would be: trade gold's catch-up move against the dollar."""
    dxy = _extra(ctx, "dxy")
    if dxy is None:
        return []
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    rets = [_ret(dxy, i, k) for i in range(b.n)]
    out = []
    for i in range(look + k, b.n):
        if not ctx.in_window(i) or not a[i] or rets[i] is None:
            continue
        hist = [x for x in rets[i - look:i] if x is not None]
        if len(hist) < look // 2:
            continue
        m = sum(hist) / len(hist)
        sd = (sum((x - m) ** 2 for x in hist) / len(hist)) ** 0.5
        if not sd:
            continue
        zz = (rets[i] - m) / sd
        if abs(zz) < z:
            continue
        side = -1 if zz > 0 else 1  # dollar up -> gold down
        gold_move = (b.c[i] - b.c[i - k]) * side  # in trade direction
        if gold_move > lag * a[i]:
            continue  # gold already reacted
        stop = b.c[i] - side * stop_atr * a[i]
        out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "dxy_div", z=round(zz, 2)))
    return out


def dxy_resilience(ctx, k=4, z=2.0, hold=0.0, stop_atr=1.0, target_r=1.5, look=100):
    """Relative strength: the dollar made an unusually large k-bar move (z-score) but
    gold did NOT react inversely (its k-bar move in the dollar's direction is at least
    `hold` ATR). Gold resisting the dollar shows its own demand: trade gold in the
    dollar's direction (dollar spikes up, gold holds -> gold long)."""
    dxy = _extra(ctx, "dxy")
    if dxy is None:
        return []
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    rets = [_ret(dxy, i, k) for i in range(b.n)]
    out = []
    for i in range(look + k, b.n):
        if not ctx.in_window(i) or not a[i] or rets[i] is None:
            continue
        hist = [x for x in rets[i - look:i] if x is not None]
        if len(hist) < look // 2:
            continue
        m = sum(hist) / len(hist)
        sd = (sum((x - m) ** 2 for x in hist) / len(hist)) ** 0.5
        if not sd:
            continue
        zz = (rets[i] - m) / sd
        if abs(zz) < z:
            continue
        side = 1 if zz > 0 else -1
        if (b.c[i] - b.c[i - k]) * side < hold * a[i]:
            continue  # gold followed the usual inverse reaction
        stop = b.c[i] - side * stop_atr * a[i]
        out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "dxy_res", z=round(zz, 2)))
    return out


def silver_lead(ctx, n=12, stop_atr=1.0, target_r=1.5, fast=20, slow=50):
    """Silver closes at a new n-bar high (low) while gold has not yet broken its own
    n-bar high (low), in gold's EMA trend direction: gold tends to follow."""
    si = _extra(ctx, "si")
    if si is None:
        return []
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    ef = ctx.ind(("ema", fast), lambda: ema(b.c, fast))
    es = ctx.ind(("ema", slow), lambda: ema(b.c, slow))
    out = []
    for i in range(max(n, slow), b.n):
        if not ctx.in_window(i) or not a[i] or si[i] is None:
            continue
        sh, sl = _hh(si, i, n), _ll(si, i, n)
        if sh is None:
            continue
        gh, gl = max(b.h[i - n:i]), min(b.l[i - n:i])
        side = 0
        if si[i] > sh and b.c[i] <= gh and ef[i] > es[i]:
            side = 1
        elif si[i] < sl and b.c[i] >= gl and ef[i] < es[i]:
            side = -1
        if side:
            stop = b.c[i] - side * stop_atr * a[i]
            out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "si_lead"))
    return out


def silver_lead_dxy(ctx, k=4, dxy_min=0.0, **lead_params):
    """silver_lead, kept only when the dollar index moved in gold's favour over k
    bars (fell for a long, rose for a short): two markets confirm gold's move."""
    dxy = _extra(ctx, "dxy")
    if dxy is None:
        return []
    out = []
    for s in silver_lead(ctx, **lead_params):
        r = _ret(dxy, s["i"], k)
        if r is not None and -r * s["side"] >= dxy_min:
            out.append(s)
    return out


def yield_filtered_trend(ctx, n=12, k=4, tnx_max=0.01, stop_atr=1.0, target_r=1.5, fast=20, slow=50):
    """n-bar breakout in EMA trend direction, skipped when the 10-year yield moved
    against gold by more than tnx_max (relative) over k bars. Needs tnx; where tnx
    has no fresh value the filter treats it as neutral."""
    tnx = _extra(ctx, "tnx")
    if tnx is None:
        return []
    b = ctx.b
    a = ctx.ind(("atr", 14), lambda: atr(b, 14))
    ef = ctx.ind(("ema", fast), lambda: ema(b.c, fast))
    es = ctx.ind(("ema", slow), lambda: ema(b.c, slow))
    out = []
    for i in range(max(n, slow), b.n):
        if not ctx.in_window(i) or not a[i]:
            continue
        hh, ll = max(b.h[i - n:i]), min(b.l[i - n:i])
        side = 1 if b.c[i] > hh and ef[i] > es[i] else -1 if b.c[i] < ll and ef[i] < es[i] else 0
        if not side:
            continue
        r = _ret(tnx, i, k) or 0.0
        if r * side > tnx_max:  # yields up hurts longs, yields down hurts shorts
            continue
        stop = b.c[i] - side * stop_atr * a[i]
        out.append(signal(i, side, stop, b.c[i] + side * target_r * stop_atr * a[i], "tnx_trend"))
    return out


def asia_breakout_dxy(ctx, k=4, dxy_min=0.0, **asia_params):
    """asia_breakout, kept only when the dollar index moved against the dollar
    side of the trade (fell for a gold long, rose for a gold short) over k bars."""
    dxy = _extra(ctx, "dxy")
    if dxy is None:
        return []
    out = []
    for s in asia_breakout(ctx, **asia_params):
        r = _ret(dxy, s["i"], k)
        if r is not None and -r * s["side"] >= dxy_min:
            out.append(s)
    return out


# All intermarket setups failed the keep rule (1h IS PF>=1.15 with n>=80 AND
# 1h OOS PF>=1.1 with n>=25); the functions stay for reference and as filters.
# IS-best params, 1h IS PF / OOS PF: dxy_momentum n=24 0.87/1.24, dxy_divergence
# 0.59/1.14, dxy_resilience k=2 1.09/0.68, silver_lead target_r=2 1.09/0.68,
# silver_lead_dxy dxy_min=0.0005 1.22/0.85, yield_filtered_trend n=24 0.87/1.13,
# asia_breakout_dxy k=8 1.00/2.05 (asia_breakout alone: 0.88/1.66).
SETUPS = {
    # "dxy_momentum": (dxy_momentum, "1h", {"n": 24}),
    # "dxy_divergence": (dxy_divergence, "1h", {}),
    # "dxy_resilience": (dxy_resilience, "1h", {"k": 2}),
    # "silver_lead": (silver_lead, "1h", {"target_r": 2.0}),
    # "silver_lead_dxy": (silver_lead_dxy, "1h", {"dxy_min": 0.0005}),
    # "yield_filtered_trend": (yield_filtered_trend, "1h", {"n": 24}),
    # "asia_breakout_dxy": (asia_breakout_dxy, "5m", {"k": 8}),
}
# Asia breakout with dollar filter and no fixed target (flat 22:00), 1h: IS PF 1.42
# (n=93, +19.8R), OOS PF 2.65 (n=49). With the old 1.5R target it was IS PF 1.00;
# the no-target change was found on the VWAP pullback's IS data, not on this setup.
SETUPS = {"asia_breakout_dxy": (asia_breakout_dxy, "1h", {"k": 8, "target_r": 50})}
WATCH = {}

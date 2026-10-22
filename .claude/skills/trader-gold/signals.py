#!/usr/bin/env python3
"""Gold breakout signals for trader-gold, with backtest and ntfy push.

Strategy (all times Europe/Berlin, 5-minute bars of COMEX gold GC=F):
  1. Asia range: high and low of the bars from 00:00 to 08:00.
  2. Only trade a "normal" range: between MIN_W and MAX_W times the daily
     ATR(14). A very narrow range breaks out on noise; a very wide one has
     already used up the day.
  3. Trend filter: BUY only when the last completed daily close is above its
     SMA20, SELL only when below.
  4. Signal: the first completed bar between 08:00 and LAST_ENTRY that
     closes above the Asia high (BUY) or below the Asia low (SELL), in the
     trend's direction. One signal per day.
  5. Stop: the middle of the Asia range. Target: TARGET_R times the risk.
     Flat at FLAT (21:00) if neither was hit.
  6. Calendar filter (live only): no signal from 30 minutes before to 15
     minutes after a High-impact USD event or a ★ Medium one.

    python3 signals.py scan                 # today's state: waiting / signal / no trade, and why
    python3 signals.py backtest             # the rules over the last 60 days of 5m bars
    python3 signals.py notify               # scan and push NEW signals and outcomes to ntfy
    python3 signals.py notify --dry-run     # print what would be pushed

ntfy: set NTFY_TOPIC (a long random name: anyone who knows it can read it)
and optionally NTFY_SERVER (default https://ntfy.sh). State for the push
lives in trader/state/gold-signals.json so a signal is pushed once.

Free, delayed, unofficial data. These are mechanical rules, not advice; the
backtest is what they did, not what they will do.
"""

import argparse
import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold  # noqa: E402

BERLIN = gold.BERLIN
ASIA = (0, 8)            # hours, Berlin
FIRST_ENTRY = 8
LAST_ENTRY = (16, 0)     # no new signal after this
FLAT = (21, 0)
MIN_W, MAX_W = 0.25, 1.0  # Asia range width in daily ATRs
TARGET_R = 1.5
BLOCK_BEFORE, BLOCK_AFTER = 30, 15  # minutes around big calendar events
CHART_60D = "https://query2.finance.yahoo.com/v8/finance/chart/GC%3DF?range=60d&interval=5m"
CHART_1Y = "https://query2.finance.yahoo.com/v8/finance/chart/GC%3DF?range=1y&interval=1d"
STATE = os.path.join(gold.STATE_DIR, "gold-signals.json")
BAR = 300


def local(ts):
    return _dt.datetime.fromtimestamp(ts, BERLIN)


def hm(ts):
    t = local(ts)
    return (t.hour, t.minute)


def daily_context(daily, day):
    """ATR14, SMA20 and last close from the daily bars completed before `day`."""
    done = [b for b in daily if local(b["t"]).date() < day]
    if len(done) < 21:
        return None
    return {"atr": gold.atr(done), "sma20": gold.sma(done, 20), "close": done[-1]["c"]}


def evaluate_day(bars, ctx, now_ts=None, params=None):
    """Run the rules on one Berlin day's 5m bars.

    bars: that day's bars, oldest first. A bar counts once it is complete,
    i.e. its start + 5 minutes <= now_ts. Returns a dict with state:
    'no-data', 'no-trade' (reason), 'waiting', or 'signal' with the trade and,
    when the day's bars go far enough, its outcome.
    """
    p = dict(min_w=MIN_W, max_w=MAX_W, target_r=TARGET_R, trend=True, last_entry=LAST_ENTRY)
    p.update(params or {})
    if now_ts is not None:
        bars = [b for b in bars if b["t"] + BAR <= now_ts]
    asia = [b for b in bars if ASIA[0] <= local(b["t"]).hour < ASIA[1]]
    if not asia or ctx is None:
        return {"state": "no-data", "reason": "keine Asien-Kerzen oder zu wenig Tagesdaten"}
    hi, lo = max(b["h"] for b in asia), min(b["l"] for b in asia)
    width = hi - lo
    out = {"asia_high": hi, "asia_low": lo, "width": width, "atr": ctx["atr"],
           "width_atr": width / ctx["atr"], "sma20": ctx["sma20"], "prev_close": ctx["close"]}
    trend = "up" if ctx["close"] > ctx["sma20"] else "down"
    out["trend"] = trend
    if now_ts is not None and local(now_ts).hour < ASIA[1]:
        return dict(out, state="waiting", reason="Asien-Session läuft noch (bis 08:00)")
    if out["width_atr"] < p["min_w"]:
        return dict(out, state="no-trade", reason="Asien-Spanne zu eng (%.2f ATR < %.2f)" % (out["width_atr"], p["min_w"]))
    if out["width_atr"] > p["max_w"]:
        return dict(out, state="no-trade", reason="Asien-Spanne zu weit (%.2f ATR > %.2f)" % (out["width_atr"], p["max_w"]))
    session = [b for b in bars if hm(b["t"]) >= (FIRST_ENTRY, 0) and hm(b["t"]) < FLAT]
    entry_bar = side = None
    for b in session:
        if hm(b["t"]) >= p["last_entry"]:
            break
        if b["c"] > hi and (trend == "up" or not p["trend"]):
            entry_bar, side = b, "BUY"
            break
        if b["c"] < lo and (trend == "down" or not p["trend"]):
            entry_bar, side = b, "SELL"
            break
    if entry_bar is None:
        done_window = now_ts is None or hm(now_ts) >= p["last_entry"]
        if done_window:
            return dict(out, state="no-trade", reason="kein Ausbruch in Trendrichtung bis %02d:%02d" % p["last_entry"])
        level = hi if trend == "up" else lo
        return dict(out, state="waiting", reason="warte auf 5-Min-Schluss %s %s (Trend %s)" % (
            "über" if trend == "up" else "unter", gold.money(level), "auf" if trend == "up" else "ab"))
    entry = entry_bar["c"]
    stop = round((hi + lo) / 2, 1)
    risk = entry - stop if side == "BUY" else stop - entry
    target = round(entry + p["target_r"] * risk if side == "BUY" else entry - p["target_r"] * risk, 1)
    sig = {"side": side, "time": local(entry_bar["t"] + BAR).isoformat(), "bar": entry_bar["t"],
           "entry": entry, "stop": stop, "target": target, "risk": round(risk, 2)}
    out.update(state="signal", signal=sig)
    out["outcome"] = outcome(session, entry_bar["t"], sig)
    return out


def outcome(session, entry_t, sig):
    """Walk the bars after the entry bar: target, stop or flat at FLAT.
    A bar that touches both counts as the stop (conservative)."""
    after = [b for b in session if b["t"] > entry_t]
    for b in after:
        if sig["side"] == "BUY":
            hit_stop, hit_tgt = b["l"] <= sig["stop"], b["h"] >= sig["target"]
        else:
            hit_stop, hit_tgt = b["h"] >= sig["stop"], b["l"] <= sig["target"]
        if hit_stop:
            return {"result": "stop", "r": -1.0, "time": local(b["t"]).isoformat()}
        if hit_tgt:
            return {"result": "target", "r": round((sig["target"] - sig["entry"]) / sig["risk"] * (1 if sig["side"] == "BUY" else -1), 2),
                    "time": local(b["t"]).isoformat()}
    if after and hm(after[-1]["t"] + BAR) >= FLAT:
        last = after[-1]["c"]
        r = (last - sig["entry"]) / sig["risk"] * (1 if sig["side"] == "BUY" else -1)
        return {"result": "flat", "r": round(r, 2), "time": local(after[-1]["t"] + BAR).isoformat()}
    return None  # still open


def by_day(bars):
    days = {}
    for b in bars:
        days.setdefault(local(b["t"]).date(), []).append(b)
    return days


def blocked_by_calendar(events, now):
    for e in events:
        if not (e["impact"] == "High" or e["gold_mover"]):
            continue
        t = _dt.datetime.fromisoformat(e["time"])
        if -BLOCK_AFTER <= (t - now).total_seconds() / 60 <= BLOCK_BEFORE:
            return e
    return None


# ---------------------------------------------------------------- commands

def load(fetcher, now):
    _, intraday = gold.parse_chart(fetcher.get(CHART_60D if not fetcher.offline else None, "chart-60d.json"))
    _, daily = gold.parse_chart(fetcher.get(CHART_1Y if not fetcher.offline else None, "chart-1y.json"))
    return intraday, daily


def scan(fetcher, now):
    intraday, daily = load(fetcher, now)
    day = now.astimezone(BERLIN).date()
    res = evaluate_day(by_day(intraday).get(day, []), daily_context(daily, day), now.timestamp())
    res["day"] = day.isoformat()
    try:
        events = gold.calendar(fetcher, now, impacts=("High", "Medium"), days=1)
    except (gold.FetchError, ValueError) as e:
        events, res["calendar_error"] = [], str(e)
    ev = blocked_by_calendar(events, now)
    if ev and res["state"] in ("signal", "waiting"):
        res["blocked_by"] = ev
    nxt = [e for e in events if not e["past"] and (e["impact"] == "High" or e["gold_mover"])]
    res["next_event"] = nxt[0] if nxt else None
    try:
        items, _, _ = gold.news(fetcher, now, hours=6, show_all=True, remember=False)
        res["headline"] = items[0] if items else None
    except Exception:  # news is context only
        res["headline"] = None
    return res


def backtest(fetcher, now, params=None):
    intraday, daily = load(fetcher, now)
    trades, skipped = [], {}
    today = now.astimezone(BERLIN).date()
    for day, bars in sorted(by_day(intraday).items()):
        if day >= today or day.weekday() >= 5:
            continue
        r = evaluate_day(bars, daily_context(daily, day), params=params)
        if r["state"] == "signal" and r["outcome"]:
            trades.append(dict(r["signal"], day=day.isoformat(), **{"result": r["outcome"]["result"], "r": r["outcome"]["r"]}))
        else:
            key = r.get("reason", r["state"]).split(" (")[0]
            skipped[key] = skipped.get(key, 0) + 1
    n = len(trades)
    wins = sum(1 for t in trades if t["r"] > 0)
    total = sum(t["r"] for t in trades)
    eq = peak = dd = 0.0
    for t in trades:
        eq += t["r"]
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    return {"trades": trades, "n": n, "wins": wins, "win_rate": wins / n if n else None,
            "total_r": round(total, 2), "avg_r": round(total / n, 2) if n else None,
            "max_drawdown_r": round(dd, 2), "skipped": skipped,
            "by_result": {k: sum(1 for t in trades if t["result"] == k) for k in ("target", "stop", "flat")}}


def render_backtest(bt):
    lines = ["BACKTEST Asien-Breakout, GC=F 5-Min, letzte ~60 Tage (Stopp Mitte Asien-Spanne, Ziel %.1fR, flat 21:00):" % TARGET_R]
    for t in bt["trades"]:
        lines.append("  %s %-4s Einstieg %s  Stopp %s  Ziel %s  -> %-6s %+.2fR" % (
            t["day"], t["side"], gold.money(t["entry"]), gold.money(t["stop"]), gold.money(t["target"]), t["result"], t["r"]))
    if bt["n"]:
        lines.append("  %d Trades: %d Ziel, %d Stopp, %d flat. Trefferquote %.0f %%, Summe %+.2fR, Schnitt %+.2fR, "
                     "max. Rückgang %.2fR." % (bt["n"], bt["by_result"]["target"], bt["by_result"]["stop"],
                                               bt["by_result"]["flat"], bt["win_rate"] * 100, bt["total_r"],
                                               bt["avg_r"], bt["max_drawdown_r"]))
    lines.append("  Ohne Trade: " + ", ".join("%s: %d" % kv for kv in sorted(bt["skipped"].items())))
    lines.append("  Ohne Kalenderfilter, Spreads und Slippage gerechnet. Vergangenheit ist keine Prognose.")
    return "\n".join(lines)


def render_scan(r):
    t = ["GOLD-SIGNAL %s: %s" % (r["day"], r["state"].upper())]
    if "asia_high" in r:
        t.append("  Asien %s – %s (%.2f ATR), Trend %s (Schluss %s vs SMA20 %s)" % (
            gold.money(r["asia_low"]), gold.money(r["asia_high"]), r["width_atr"],
            "auf" if r["trend"] == "up" else "ab", gold.money(r["prev_close"]), gold.money(r["sma20"])))
    if r.get("reason"):
        t.append("  " + r["reason"])
    s = r.get("signal")
    if s:
        t.append("  %s um %s: Einstieg %s  Stopp %s  Ziel %s  (Risiko %s je Unze)" % (
            s["side"], s["time"][11:16], gold.money(s["entry"]), gold.money(s["stop"]), gold.money(s["target"]), gold.money(s["risk"])))
        o = r.get("outcome")
        t.append("  Stand: " + ("offen" if not o else "%s um %s (%+.2fR)" % (o["result"], o["time"][11:16], o["r"])))
    if r.get("blocked_by"):
        e = r["blocked_by"]
        t.append("  GESPERRT: %s um %s – kein Einstieg rund um den Termin" % (e["title"], e["time"][11:16]))
    if r.get("next_event"):
        e = r["next_event"]
        t.append("  Nächster wichtiger Termin: %s %s (%s)" % (e["time"][11:16], e["title"], gold.IMPACT_DE[e["impact"]]))
    if r.get("headline"):
        t.append("  News: %s" % r["headline"]["title"])
    return "\n".join(t)


# ---------------------------------------------------------------- push

def push_messages(r, state):
    """What to push for this scan, given what was pushed already. Mutates state."""
    msgs = []
    day = r["day"]
    sent = state.setdefault(day, [])
    s = r.get("signal")
    if r["state"] == "signal" and not r.get("blocked_by") and "signal" not in sent:
        sent.append("signal")
        side_de = "KAUFEN" if s["side"] == "BUY" else "VERKAUFEN"
        body = "Einstieg %s | Stopp %s | Ziel %s | Risiko %s/oz\nAsien %s–%s, Trend %s." % (
            gold.money(s["entry"]), gold.money(s["stop"]), gold.money(s["target"]), gold.money(s["risk"]),
            gold.money(r["asia_low"]), gold.money(r["asia_high"]), "auf" if r["trend"] == "up" else "ab")
        if r.get("next_event"):
            body += "\nTermin %s: %s" % (r["next_event"]["time"][11:16], r["next_event"]["title"])
        if r.get("headline"):
            body += "\nNews: %s" % r["headline"]["title"]
        msgs.append({"title": "Gold %s-Signal %s" % (side_de, s["time"][11:16]), "body": body,
                     "priority": "high", "tags": "chart_with_upwards_trend" if s["side"] == "BUY" else "chart_with_downwards_trend"})
    if r["state"] == "signal" and r.get("blocked_by") and "blocked" not in sent and "signal" not in sent:
        sent.append("blocked")
        e = r["blocked_by"]
        msgs.append({"title": "Gold: Ausbruch, aber Termin", "priority": "default", "tags": "warning",
                     "body": "%s-Ausbruch, gesperrt wegen %s um %s. Kein Einstieg." % (s["side"], e["title"], e["time"][11:16])})
    o = r.get("outcome")
    if o and "signal" in sent and "outcome" not in sent:
        sent.append("outcome")
        word = {"target": "ZIEL erreicht", "stop": "STOPP ausgelöst", "flat": "Feierabend: glattstellen"}[o["result"]]
        msgs.append({"title": "Gold %s: %s" % ("Kauf" if s["side"] == "BUY" else "Verkauf", word), "priority": "high" if o["result"] == "flat" else "default",
                     "tags": {"target": "white_check_mark", "stop": "x", "flat": "bell"}[o["result"]],
                     "body": "%s um %s, Ergebnis %+.2fR (Einstieg %s)." % (word, o["time"][11:16], o["r"], gold.money(s["entry"]))})
    for k in sorted(state)[:-10]:  # keep ten days
        del state[k]
    return msgs


def send_ntfy(msg, topic, server):
    req = urllib.request.Request("%s/%s" % (server.rstrip("/"), topic), data=msg["body"].encode("utf-8"), headers={
        "Title": msg["title"].encode("utf-8").decode("latin-1"), "Priority": msg["priority"], "Tags": msg["tags"]})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status


def main(argv=None):
    p = argparse.ArgumentParser(description="Gold-Breakout-Signale (XAU/USD via GC=F): scan, backtest, notify.")
    p.add_argument("cmd", choices=["scan", "backtest", "notify"])
    p.add_argument("--json", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="notify: nur anzeigen, nichts senden")
    p.add_argument("--no-trend", action="store_true", help="backtest: ohne Trendfilter")
    p.add_argument("--target-r", type=float, default=TARGET_R)
    p.add_argument("--offline", metavar="DIR")
    p.add_argument("--now")
    p.add_argument("--state", default=STATE)
    a = p.parse_args(argv)
    now = _dt.datetime.fromisoformat(a.now) if a.now else _dt.datetime.now(_dt.timezone.utc)
    f = gold.Fetcher(a.offline)
    try:
        if a.cmd == "backtest":
            bt = backtest(f, now, {"trend": not a.no_trend, "target_r": a.target_r})
            print(json.dumps(bt, indent=1, default=str) if a.json else render_backtest(bt))
            return 0
        r = scan(f, now)
    except gold.FetchError as e:
        print("FEHLER: %s" % e, file=sys.stderr)
        return 1
    if a.cmd == "scan":
        print(json.dumps(r, indent=1, ensure_ascii=False, default=str) if a.json else render_scan(r))
        return 0
    state = gold.load_json(a.state, {})
    msgs = push_messages(r, state)
    topic = os.environ.get("NTFY_TOPIC")
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
    print(render_scan(r))
    if msgs and not topic and not a.dry_run:
        print("FEHLER: NTFY_TOPIC ist nicht gesetzt, %d Push(es) nicht gesendet." % len(msgs), file=sys.stderr)
        return 1
    for m in msgs:
        if a.dry_run:
            print("\n[PUSH Probelauf] %s\n%s" % (m["title"], m["body"]))
        else:
            try:
                send_ntfy(m, topic, server)
                print("\n[PUSH gesendet] %s" % m["title"])
            except (urllib.error.URLError, OSError) as e:
                print("FEHLER: ntfy: %s" % e, file=sys.stderr)
                return 1
    if not msgs:
        print("\nKein neuer Push.")
    if not a.dry_run:
        gold.save_json(a.state, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())

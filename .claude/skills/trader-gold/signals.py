#!/usr/bin/env python3
"""Live gold signals for trader-gold: every active setup, one push per signal.

Runs every setup registered in setups/*.py (SETUPS) on fresh Yahoo bars of
COMEX gold GC=F, plus the Dollar index, the 10-year yield and silver for the
setups that use them. Signals only between 08:00 and 20:00 German time (the
engine enforces it), open trades are flat by 22:00.

    python3 signals.py scan                 # today's signals and their state
    python3 signals.py notify               # push NEW signals and outcomes to ntfy
    python3 signals.py notify --dry-run     # print what would be pushed
    python3 signals.py backtest             # all setups on ~2 years of 1h + 60 days of 15m/5m

Quality: each push carries the setup's out-of-sample record from
setups/stats.json (written by research.py --write-stats) and how many setups
agree. No entry is pushed from 30 minutes before to 15 minutes after a High
or ★ calendar event; a warning is pushed instead.

ntfy: NTFY_TOPIC (secret, a long random name) and optionally NTFY_SERVER.
State: trader/state/gold-signals.json, so every signal and outcome is pushed once.

Free, delayed, unofficial data; mechanical rules, not advice.
"""

import argparse
import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine  # noqa: E402
import gold  # noqa: E402
import research  # noqa: E402

BERLIN = gold.BERLIN
SYMBOLS = {"gc": "GC%3DF", "dxy": "DX-Y.NYB", "tnx": "%5ETNX", "si": "SI%3DF"}
LIVE_RANGE = {"5m": "5d", "15m": "1mo", "1h": "6mo"}
CHART = "https://query2.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=%s"
STATE = os.path.join(gold.STATE_DIR, "gold-signals.json")
STATS = os.path.join(HERE, "setups", "stats.json")
BLOCK_BEFORE, BLOCK_AFTER = 30, 15  # minutes around big calendar events
MAX_AGE = 45                        # minutes: older signals are recorded, not pushed
CONFLUENCE = 60                     # minutes: same-side signals this close count together
NAMES_DE = {
    "trend_vwap_pullback": "VWAP-Pullback im Trend",
    "trend_vwap_pullback_15m": "VWAP-Pullback 15m",
    "vwap_fade": "VWAP-Fade",
    "asia_breakout_dxy": "Asien-Breakout + Dollar",
    "london_or": "London-Opening-Range",
}


def label(name):
    return NAMES_DE.get(name, name.replace("_", " "))


# ---------------------------------------------------------------- data

def load_live(fetcher, now, tfs, ranges=LIVE_RANGE):
    """Contexts per timeframe from Yahoo, trimmed to bars complete at `now`."""
    ts = now.timestamp()
    daily = engine.trim(engine.load_yahoo(fetcher.get(CHART % (SYMBOLS["gc"], "2y", "1d"), "gc-1d.json")), ts + 86400)
    ctxs = {}
    for tf in tfs:
        bars = engine.trim(engine.load_yahoo(fetcher.get(CHART % (SYMBOLS["gc"], ranges[tf], tf), "gc-%s.json" % tf)), ts)
        extras = {}
        for k in ("dxy", "tnx", "si"):
            try:
                extras[k] = engine.trim(engine.load_yahoo(fetcher.get(CHART % (SYMBOLS[k], ranges[tf], tf), "%s-%s.json" % (k, tf))), ts)
            except (gold.FetchError, KeyError, IndexError, TypeError, ValueError):
                pass  # setups treat a missing extra as "no signal"
        ctxs[tf] = engine.Ctx(bars, daily=daily, extras=extras)
    return ctxs


def load_stats(path=STATS):
    return gold.load_json(path, {})


def is_watch(stat):
    return (stat or {}).get("tier") == "watch"


def stars(stat, agree):
    """1-3 stars from the out-of-sample profit factor, +1 when setups agree.
    Experimental (watch) setups get one star at most."""
    if is_watch(stat):
        return 1
    pf = ((stat or {}).get("oos") or {}).get("pf") or 0
    s = 3 if pf >= 1.5 else 2 if pf >= 1.25 else 1
    return min(3, s + (1 if agree > 1 else 0))


# ---------------------------------------------------------------- scan

def scan(fetcher, now, registry=None):
    reg = registry if registry is not None else research.all_setups()
    tfs = sorted({tf for _, tf, _ in reg.values()})
    ctxs = load_live(fetcher, now, tfs)
    today = now.astimezone(BERLIN).date().isoformat()
    trades = []
    for name, (fn, tf, params) in sorted(reg.items()):
        ctx = ctxs[tf]
        for t in engine.simulate(ctx, fn(ctx, **params), name, keep_open=True):
            if t["date"] != today:
                continue
            t["tf"] = tf
            t["key"] = "%s|%s|%d" % (name, tf, t["t"])
            t["signal_time"] = _dt.datetime.fromtimestamp(t["t"] + ctx.b.step, BERLIN).isoformat()
            if t["exit_i"] is not None:
                t["exit_time"] = "%02d:%02d" % ctx.b.end_hm[t["exit_i"]]
            trades.append(t)
    trades.sort(key=lambda t: t["signal_time"])
    res = {"day": today, "trades": trades, "setups": sorted(reg), "now": now.isoformat()}
    try:
        events = gold.calendar(fetcher, now, impacts=("High", "Medium"), days=1)
    except (gold.FetchError, ValueError) as e:
        events, res["calendar_error"] = [], str(e)
    res["blocked_by"] = blocked_by_calendar(events, now)
    nxt = [e for e in events if not e["past"] and (e["impact"] == "High" or e["gold_mover"])]
    res["next_event"] = nxt[0] if nxt else None
    try:
        items, _, _ = gold.news(fetcher, now, hours=6, show_all=True, remember=False)
        res["headline"] = items[0] if items else None
    except Exception:  # news is context only
        res["headline"] = None
    return res


def blocked_by_calendar(events, now):
    for e in events:
        if not (e["impact"] == "High" or e["gold_mover"]):
            continue
        t = _dt.datetime.fromisoformat(e["time"])
        if -BLOCK_AFTER <= (t - now).total_seconds() / 60 <= BLOCK_BEFORE:
            return e
    return None


def agreeing(t, trades):
    """Setups with a same-side signal within CONFLUENCE minutes of t."""
    t0 = _dt.datetime.fromisoformat(t["signal_time"])
    return sorted({o["setup"] for o in trades if o["side"] == t["side"]
                   and abs((_dt.datetime.fromisoformat(o["signal_time"]) - t0).total_seconds()) <= CONFLUENCE * 60})


def side_de(side):
    return "KAUFEN" if side > 0 else "VERKAUFEN"


def render_scan(r, stats):
    out = ["GOLD-SIGNALE %s (%d Setups aktiv, Fenster 08:00–20:00)" % (r["day"], len(r["setups"]))]
    if not r["trades"]:
        out.append("  Heute noch kein Signal.")
    for t in r["trades"]:
        st = stats.get(t["setup"], {})
        state = "offen" if t["result"] is None else "%s um %s (%+.2fR)" % (
            {"target": "Ziel", "stop": "Stopp", "flat": "flat"}[t["result"]], t["exit_time"], t["r"])
        out.append("  %s %-9s %-24s %3s  Einstieg %s  Stopp %s  Ziel %s  %s  %s" % (
            t["signal_time"][11:16], side_de(t["side"]), label(t["setup"]), t["tf"], gold.money(t["entry"]),
            gold.money(t["stop"]), gold.money(t["target"]), "★" * stars(st, len(agreeing(t, r["trades"]))), state))
    if r.get("blocked_by"):
        e = r["blocked_by"]
        out.append("  GESPERRT: %s um %s – keine neuen Einstiege rund um den Termin" % (e["title"], e["time"][11:16]))
    if r.get("next_event"):
        e = r["next_event"]
        out.append("  Nächster wichtiger Termin: %s %s (%s)" % (e["time"][11:16], e["title"], gold.IMPACT_DE[e["impact"]]))
    if r.get("headline"):
        out.append("  News: %s" % r["headline"]["title"])
    return "\n".join(out)


# ---------------------------------------------------------------- push

def stat_line(st):
    o = (st or {}).get("oos") or {}
    if not o.get("n"):
        return "ohne Teststatistik"
    line = "Test 2026: %d Trades, %d %% Treffer, PF %.2f" % (o["n"], round(o["win"] * 100), o["pf"])
    if is_watch(st):
        i = (st or {}).get("is") or {}
        line = "EXPERIMENTELL, 2024-25 PF %.2f, %s" % (i.get("pf") or 0, line)
    return line


def push_messages(r, state, stats, now):
    """Messages for new signals and finished trades. Mutates state."""
    sent = state.setdefault("sent", {})
    msgs, fresh = [], []
    for t in r["trades"]:
        if t["key"] in sent:
            continue
        age = (now - _dt.datetime.fromisoformat(t["signal_time"])).total_seconds() / 60
        sent[t["key"]] = {"day": r["day"], "pushed": age <= MAX_AGE and not r.get("blocked_by")}
        if age > MAX_AGE:
            continue
        fresh.append(t)
    for side in (1, -1):
        group = [t for t in fresh if t["side"] == side]
        if not group:
            continue
        watch_only = all(is_watch(stats.get(t["setup"])) for t in group)
        if r.get("blocked_by"):
            e = r["blocked_by"]
            msgs.append({"title": "Gold %s-Signal gesperrt: %s %s" % (side_de(side), e["time"][11:16], e["title"]),
                         "priority": "default", "tags": "warning",
                         "body": "%s. Kein Einstieg rund um den Termin." % ", ".join(label(t["setup"]) for t in group)})
            continue
        best = max(group, key=lambda t: (not is_watch(stats.get(t["setup"])),
                                         (stats.get(t["setup"], {}).get("oos") or {}).get("pf") or 0))
        agree = agreeing(best, r["trades"])
        lines = ["Einstieg %s | Stopp %s | Ziel %s | Risiko %s/oz" % (
            gold.money(best["entry"]), gold.money(best["stop"]), gold.money(best["target"]), gold.money(best["risk"]))]
        for t in group:
            lines.append("%s (%s): %s" % (label(t["setup"]), t["tf"], stat_line(stats.get(t["setup"]))))
        if len(agree) > 1:
            lines.append("Bestätigt von %d Setups: %s" % (len(agree), ", ".join(label(a) for a in agree)))
        if r.get("next_event"):
            lines.append("Termin %s: %s" % (r["next_event"]["time"][11:16], r["next_event"]["title"]))
        if r.get("headline"):
            lines.append("News: %s" % r["headline"]["title"])
        msgs.append({"title": "Gold %s%s %s %s" % ("Beobachtung: " if watch_only else "", side_de(side),
                                                    best["signal_time"][11:16],
                                                    "★" * stars(stats.get(best["setup"]), len(agree))),
                     "body": "\n".join(lines), "priority": "low" if watch_only else "high",
                     "tags": "chart_with_upwards_trend" if side > 0 else "chart_with_downwards_trend"})
    for t in r["trades"]:
        rec = sent.get(t["key"])
        if t["result"] is None or not rec or not rec.get("pushed") or rec.get("outcome"):
            continue
        rec["outcome"] = True
        word = {"target": "ZIEL erreicht", "stop": "STOPP ausgelöst", "flat": "glattgestellt (22:00)"}[t["result"]]
        msgs.append({"title": "Gold %s %s: %s" % ("Kauf" if t["side"] > 0 else "Verkauf", t["signal_time"][11:16], word),
                     "priority": "default", "tags": {"target": "white_check_mark", "stop": "x", "flat": "bell"}[t["result"]],
                     "body": "%s (%s): %s um %s, Ergebnis %+.2fR (Einstieg %s)." % (
                         label(t["setup"]), t["tf"], word, t["exit_time"], t["r"], gold.money(t["entry"]))})
    keep = sorted({v["day"] for v in sent.values()})[-5:]
    state["sent"] = {k: v for k, v in sent.items() if v["day"] in keep}
    return msgs


def send_ntfy(msg, topic, server):
    req = urllib.request.Request("%s/%s" % (server.rstrip("/"), topic), data=msg["body"].encode("utf-8"), headers={
        "Title": msg["title"].encode("utf-8").decode("latin-1"), "Priority": msg["priority"], "Tags": msg["tags"]})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status


# ---------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(description="Gold-Signale aller aktiven Setups: scan, notify, backtest.")
    p.add_argument("cmd", choices=["scan", "notify", "backtest"])
    p.add_argument("--json", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="notify: nur anzeigen, nichts senden")
    p.add_argument("--offline", metavar="DIR", help="Yahoo-JSON aus DIR (gc-1h.json, dxy-15m.json, ...)")
    p.add_argument("--now")
    p.add_argument("--state", default=STATE)
    a = p.parse_args(argv)
    now = _dt.datetime.fromisoformat(a.now) if a.now else _dt.datetime.now(_dt.timezone.utc)
    f = gold.Fetcher(a.offline)
    stats = load_stats()
    try:
        if a.cmd == "backtest":
            data = {}
            for tf, rng in (("1h", "730d"), ("15m", "60d"), ("5m", "60d"), ("1d", "5y")):
                for k in ("gc", "dxy", "tnx", "si") if tf != "1d" else ("gc",):
                    data["%s-%s" % (k, tf)] = engine.load_yahoo(f.get(CHART % (SYMBOLS[k], rng, tf), "%s-%s.json" % (k, tf)))
            research.run(data)
            return 0
        r = scan(f, now)
    except gold.FetchError as e:
        print("FEHLER: %s" % e, file=sys.stderr)
        return 1
    if a.cmd == "scan":
        print(json.dumps(r, indent=1, ensure_ascii=False, default=str) if a.json else render_scan(r, stats))
        return 0
    state = gold.load_json(a.state, {})
    msgs = push_messages(r, state, stats, now)
    topic = os.environ.get("NTFY_TOPIC")
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
    print(render_scan(r, stats))
    if msgs and not topic and not a.dry_run:
        print("FEHLER: NTFY_TOPIC ist nicht gesetzt, %d Push(es) nicht gesendet." % len(msgs), file=sys.stderr)
        return 1
    for m in msgs:
        if a.dry_run:
            print("\n[PUSH Probelauf] %s\n%s" % (m["title"], m["body"]))
            continue
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

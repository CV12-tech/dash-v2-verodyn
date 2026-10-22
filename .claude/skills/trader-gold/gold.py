#!/usr/bin/env python3
"""Gold desk for trader-gold (XAU/USD). Standard library only, Python 3.9+.

One market, three feeds: the gold price with its key levels, gold news, and
the economic calendar events that move gold. Times print in German time
(Europe/Berlin).

    python3 gold.py                      # briefing: price + levels + news + calendar
    python3 gold.py quote                # price, day range, change
    python3 gold.py levels               # ATR, 20-day high/low, averages, Asia range
    python3 gold.py news --hours 24      # new gold headlines (--all: seen ones too)
    python3 gold.py calendar --days 7    # USD high/medium impact events this week
    python3 gold.py calendar --countries USD,EUR,CNY --impact High

Sources:
  - Price: Yahoo Finance chart endpoint for the COMEX gold future GC=F
    (front month). Yahoo has no spot XAU/USD symbol any more; the future
    trades a few dollars above spot and moves with it. Unofficial, can lag.
    https://query2.finance.yahoo.com/v8/finance/chart/GC=F?range=5d&interval=5m
  - News: Yahoo Finance headline RSS for GC=F. It syndicates Investing.com's
    gold reports; those are marked [Investing.com].
    https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US
  - Calendar: ForexFactory's free weekly export (Investing.com has no API
    and its terms forbid scraping). Cached 30 minutes in
    trader/state/gold-calendar.json because the export is rate-limited.
    https://nfs.faireconomy.media/ff_calendar_thisweek.json

State: trader/state/gold-news.json remembers shown headlines (7 days).
Offline: --offline DIR reads chart-intraday.json, chart-daily.json, news.xml
and calendar.json from DIR. The tests use it.

Prices are free, delayed and unofficial; nothing here is advice.
"""

import argparse
import datetime as _dt
import email.utils
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

SYMBOL = "GC=F"
CHART = "https://query2.finance.yahoo.com/v8/finance/chart/GC%%3DF?range=%s&interval=%s"
NEWS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US"
CALENDAR = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
UA = "Mozilla/5.0 (compatible; trader-gold/1.0)"
BERLIN = ZoneInfo("Europe/Berlin")
STATE_DIR = "trader/state"
NEWS_STATE = os.path.join(STATE_DIR, "gold-news.json")
CAL_CACHE = os.path.join(STATE_DIR, "gold-calendar.json")
CAL_TTL = 30 * 60
KEEP_DAYS = 7
IMPACTS = ["High", "Medium", "Low", "Holiday"]
IMPACT_DE = {"High": "hoch", "Medium": "mittel", "Low": "niedrig", "Holiday": "Feiertag"}

# Releases that reliably move gold: rates, inflation, jobs, growth, the dollar.
GOLD_MOVERS = re.compile(
    r"FOMC|Federal Funds|Fed |Powell|CPI|PCE|PPI|Non-Farm|Nonfarm|NFP|Unemployment|"
    r"Jobless|JOLTS|ADP|Average Hourly|GDP|Retail Sales|ISM|Consumer Sentiment|"
    r"Inflation|Interest Rate|Treasury", re.I)

NEWS_TAGS = [
    ("Fed/Zinsen", r"\bFed\b|FOMC|Powell|rate (cut|hike)|interest rate|yields?\b|Treasur"),
    ("Inflation", r"inflation|\bCPI\b|\bPCE\b|\bPPI\b"),
    ("Dollar", r"dollar|\bDXY\b|greenback|\bUSD\b"),
    ("Geopolitik", r"war\b|tension|conflict|Middle East|Gulf|Iran|Israel|Russia|Ukraine|China|tariff|sanction"),
    ("Zentralbanken", r"central bank|PBOC|\bECB\b|reserves"),
    ("Nachfrage", r"gold ETF|ETF (in|out)flows|central bank (buying|purchases)|jewel|physical demand|bullion demand"),
    ("Arbeitsmarkt", r"payroll|jobs\b|jobless|unemployment|labor"),
]
MACRO_TAGS = {"Fed/Zinsen", "Inflation", "Dollar", "Zentralbanken", "Arbeitsmarkt", "Nachfrage"}
# A headline about the gold price itself, as opposed to a mining company.
GOLD_PRICE = re.compile(
    r"XAU|bullion|gold (price|futures|prices|market)|precious metals|safe[- ]haven|metals? prices|"
    r"\bgold\b (slides|slips|falls|drops|dips|rises|edges|jumps|climbs|gains|rallies|hits|tumbles|"
    r"steadies|retreats|extends|holds|surges|sinks|rebounds|eases|firms)", re.I)


class FetchError(Exception):
    pass


class Fetcher:
    def __init__(self, offline=None):
        self.offline = offline

    def get(self, url, name):
        if self.offline:
            path = os.path.join(self.offline, name)
            if not os.path.exists(path):
                raise FetchError("offline file missing: %s" % path)
            with open(path, "rb") as f:
                return f.read()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            raise FetchError("%s antwortet HTTP %s" % (url.split("/")[2], e.code))
        except (urllib.error.URLError, OSError) as e:
            reason = getattr(e, "reason", e)
            raise FetchError("%s nicht erreichbar: %s" % (url.split("/")[2], reason))


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def berlin(ts):
    return _dt.datetime.fromtimestamp(ts, BERLIN)


WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def fmt_time(dt):
    dt = dt.astimezone(BERLIN)
    return "%s %s" % (WEEKDAYS[dt.weekday()][:2], dt.strftime("%d.%m. %H:%M"))


def de(x, fmt="{:+,.2f}"):
    return fmt.format(x).replace(",", "X").replace(".", ",").replace("X", ".")


def money(x):
    return "—" if x is None else "$" + ("{:,.2f}".format(x)).replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- price

def parse_chart(data):
    """Yahoo chart JSON -> (meta, bars) with bars as dicts, empty bars dropped."""
    chart = json.loads(data)["chart"]
    if chart.get("error") or not chart.get("result"):
        raise FetchError("Yahoo liefert keine Daten für %s: %s" % (SYMBOL, chart.get("error")))
    res = chart["result"][0]
    q = res["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(res.get("timestamp") or []):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append({"t": ts, "o": o, "h": h, "l": l, "c": c, "v": (q.get("volume") or [0] * (i + 1))[i] or 0})
    return res["meta"], bars


def quote(fetcher):
    meta, bars = parse_chart(fetcher.get(CHART % ("5d", "5m"), "chart-intraday.json"))
    if not bars:
        raise FetchError("keine Kerzen für %s" % SYMBOL)
    last = bars[-1]
    price = meta.get("regularMarketPrice") or last["c"]
    prev = meta.get("previousClose") or meta.get("chartPreviousClose")
    now_ts = meta.get("regularMarketTime") or last["t"]
    day = [b for b in bars if b["t"] > now_ts - 24 * 3600]
    out = {
        "symbol": SYMBOL, "name": meta.get("shortName"), "price": price,
        "prev_close": prev,
        "change": None if prev is None else round(price - prev, 2),
        "change_pct": None if not prev else round((price - prev) / prev * 100, 2),
        "high_24h": max(b["h"] for b in day), "low_24h": min(b["l"] for b in day),
        "time": berlin(now_ts).isoformat(),
        "high_52w": meta.get("fiftyTwoWeekHigh"), "low_52w": meta.get("fiftyTwoWeekLow"),
    }
    out["asia"] = session_range(bars, now_ts, 0, 8)
    return out


def session_range(bars, now_ts, start_h, end_h):
    """High/low of today's bars between start_h and end_h, German time."""
    today = berlin(now_ts).date()
    sel = [b for b in bars if berlin(b["t"]).date() == today and start_h <= berlin(b["t"]).hour < end_h]
    if not sel:
        return None
    return {"high": max(b["h"] for b in sel), "low": min(b["l"] for b in sel),
            "from": "%02d:00" % start_h, "to": "%02d:00" % end_h}


def atr(bars, n=14):
    if len(bars) < n + 1:
        return None
    trs = [max(b["h"] - b["l"], abs(b["h"] - p["c"]), abs(b["l"] - p["c"]))
           for p, b in zip(bars[:-1], bars[1:])]
    return sum(trs[-n:]) / n


def sma(bars, n):
    return None if len(bars) < n else sum(b["c"] for b in bars[-n:]) / n


def levels(fetcher):
    _, daily = parse_chart(fetcher.get(CHART % ("6mo", "1d"), "chart-daily.json"))
    if len(daily) < 2:
        raise FetchError("zu wenige Tageskerzen für %s" % SYMBOL)
    done = daily[:-1]  # the last daily bar is today's, still forming
    last20 = done[-20:]
    return {
        "atr14": atr(done), "sma20": sma(done, 20), "sma50": sma(done, 50),
        "high20": max(b["h"] for b in last20), "low20": min(b["l"] for b in last20),
        "prev_high": done[-1]["h"], "prev_low": done[-1]["l"], "prev_close": done[-1]["c"],
    }


def render_quote(q, lv=None):
    lines = []
    chg = "" if q["change"] is None else " (%s / %s %%)" % (de(q["change"]), de(q["change_pct"]))
    lines.append("GOLD %s  %s%s  Stand %s" % (q["name"] or SYMBOL, money(q["price"]), chg,
                                             fmt_time(_dt.datetime.fromisoformat(q["time"]))))
    lines.append("  24h: Hoch %s  Tief %s   52 Wochen: %s – %s" % (
        money(q["high_24h"]), money(q["low_24h"]), money(q["low_52w"]), money(q["high_52w"])))
    if q.get("asia"):
        a = q["asia"]
        lines.append("  Asien-Session heute (%s–%s): Hoch %s  Tief %s" % (a["from"], a["to"], money(a["high"]), money(a["low"])))
    if lv:
        lines.append("  Vortag: Hoch %s  Tief %s  Schluss %s" % (money(lv["prev_high"]), money(lv["prev_low"]), money(lv["prev_close"])))
        lines.append("  20 Tage: Hoch %s  Tief %s   SMA20 %s  SMA50 %s" % (
            money(lv["high20"]), money(lv["low20"]), money(lv["sma20"]), money(lv["sma50"])))
        if lv["atr14"]:
            lines.append("  ATR(14, täglich): %s  = übliche Tagesspanne" % money(lv["atr14"]))
            for name, ref in (("SMA20", lv["sma20"]), ("SMA50", lv["sma50"])):
                if ref:
                    lines.append("  Abstand zu %s: %s ATR" % (name, de((q["price"] - ref) / lv["atr14"])))
    lines.append("  Quelle: COMEX-Future %s (Yahoo, verzögert, inoffiziell). Spot XAU/USD liegt meist "
                 "ein paar Dollar darunter." % SYMBOL)
    return "\n".join(lines)


# ---------------------------------------------------------------- news

def parse_news(data):
    root = ET.fromstring(data)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        desc = (it.findtext("description") or "").strip()
        link = (it.findtext("link") or "").strip()
        when = it.findtext("pubDate")
        try:
            dt = email.utils.parsedate_to_datetime(when)
        except (TypeError, ValueError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        text = title + " " + desc
        source = "Investing.com" if desc.startswith("Investing.com") else "Yahoo"
        items.append({
            "id": hashlib.sha1((link or title).encode()).hexdigest()[:16],
            "title": title, "summary": desc, "link": link, "time": dt.isoformat(),
            "source": source,
            "tags": [t for t, rx in NEWS_TAGS if re.search(rx, text, re.I)],
        })
        tags = items[-1]["tags"]
        items[-1]["relevant"] = bool(GOLD_PRICE.search(text)) or bool(MACRO_TAGS.intersection(tags))
    items.sort(key=lambda i: i["time"], reverse=True)
    return items


def news(fetcher, now, hours=24, show_all=False, state_path=NEWS_STATE, remember=True, everything=False):
    items = parse_news(fetcher.get(NEWS, "news.xml"))
    cutoff = now - _dt.timedelta(hours=hours)
    items = [i for i in items if _dt.datetime.fromisoformat(i["time"]) >= cutoff]
    hidden = 0 if everything else sum(1 for i in items if not i["relevant"])
    if not everything:
        items = [i for i in items if i["relevant"]]
    state = load_json(state_path, {"seen": {}})
    fresh = items if show_all else [i for i in items if i["id"] not in state["seen"]]
    if remember:
        keep = now - _dt.timedelta(days=KEEP_DAYS)
        seen = {k: v for k, v in state["seen"].items() if _dt.datetime.fromisoformat(v) >= keep}
        for i in items:
            seen.setdefault(i["id"], now.isoformat())
        save_json(state_path, {"seen": seen})
    return fresh, len(items), hidden


def render_news(items, total, hours, hidden=0):
    note = "" if not hidden else "  %d Meldungen zu Minenaktien u. Ä. ausgeblendet (--everything zeigt sie)." % hidden
    if not items:
        return "NEWS: nichts Neues (%d Meldungen in den letzten %dh schon gezeigt; --all zeigt sie).%s" % (total, hours, note)
    lines = ["NEWS zu Goldpreis und Makro (%d neu, letzte %dh):" % (len(items), hours)]
    for i in items:
        tags = (" [" + ", ".join(i["tags"]) + "]") if i["tags"] else ""
        src = " [Investing.com]" if i["source"] == "Investing.com" else ""
        lines.append("  %s  %s%s%s" % (fmt_time(_dt.datetime.fromisoformat(i["time"])), i["title"], src, tags))
        lines.append("      %s" % i["link"])
    if note:
        lines.append(note)
    return "\n".join(lines)


# ---------------------------------------------------------------- calendar

def calendar_raw(fetcher, now, cache_path=CAL_CACHE):
    if not fetcher.offline:
        cached = load_json(cache_path, None)
        if cached and now.timestamp() - cached.get("fetched", 0) < CAL_TTL:
            return cached["events"]
    events = json.loads(fetcher.get(CALENDAR, "calendar.json"))
    if not fetcher.offline:
        save_json(cache_path, {"fetched": now.timestamp(), "events": events})
    return events


def calendar(fetcher, now, countries=("USD",), impacts=("High", "Medium"), days=7):
    out = []
    end = now + _dt.timedelta(days=days)
    start = now.astimezone(BERLIN).replace(hour=0, minute=0, second=0, microsecond=0)
    for e in calendar_raw(fetcher, now):
        if e.get("country") not in countries or e.get("impact") not in impacts:
            continue
        try:
            dt = _dt.datetime.fromisoformat(e["date"])
        except (KeyError, ValueError):
            continue
        if not (start <= dt <= end):
            continue
        out.append({
            "time": dt.astimezone(BERLIN).isoformat(), "country": e["country"],
            "title": e.get("title", ""), "impact": e["impact"],
            "forecast": e.get("forecast") or "", "previous": e.get("previous") or "",
            "actual": e.get("actual") or "",
            "gold_mover": bool(GOLD_MOVERS.search(e.get("title", ""))),
            "past": dt < now,
        })
    out.sort(key=lambda e: e["time"])
    return out


def render_calendar(events, now):
    if not events:
        return "KALENDER: keine passenden Termine im Zeitraum."
    lines = ["KALENDER (deutsche Zeit, ★ = bewegt Gold typischerweise):"]
    nxt = next((e for e in events if not e["past"]), None)
    day = None
    for e in events:
        dt = _dt.datetime.fromisoformat(e["time"])
        if dt.date() != day:
            day = dt.date()
            lines.append("  %s %s%s" % (WEEKDAYS[dt.weekday()], dt.strftime("%d.%m."), "  (heute)" if day == now.astimezone(BERLIN).date() else ""))
        mark = "★" if e["gold_mover"] else " "
        nums = "  Prognose %s  Vorher %s" % (e["forecast"] or "—", e["previous"] or "—")
        if e["actual"]:
            nums = "  Ist %s" % e["actual"] + nums
        flag = ""
        if e is nxt:
            mins = int((dt - now).total_seconds() // 60)
            flag = "  ← NÄCHSTER, in %dh %02dmin" % (mins // 60, mins % 60)
        lines.append("    %s %s %s %-7s %s%s%s" % (mark, dt.strftime("%H:%M"), e["country"],
                                                 IMPACT_DE[e["impact"]], e["title"], nums, flag))
    lines.append("  Quelle: ForexFactory-Wochenexport. Zeiten und Prognosen vor Handel gegenprüfen.")
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(description="Gold desk (XAU/USD): Kurs, Marken, News, Wirtschaftskalender.")
    p.add_argument("cmd", nargs="?", default="brief", choices=["brief", "quote", "levels", "news", "calendar"])
    p.add_argument("--hours", type=int, default=24, help="News der letzten N Stunden (Standard 24)")
    p.add_argument("--all", action="store_true", help="auch schon gezeigte News")
    p.add_argument("--everything", action="store_true", help="auch News zu Minenaktien u. Ä.")
    p.add_argument("--days", type=int, default=7, help="Kalender: N Tage voraus (Standard 7)")
    p.add_argument("--countries", default="USD", help="Kalender: Währungen, z. B. USD,EUR,CNY")
    p.add_argument("--impact", default="High,Medium", help="Kalender: High,Medium,Low,Holiday")
    p.add_argument("--json", action="store_true")
    p.add_argument("--offline", metavar="DIR")
    p.add_argument("--now", help="ISO-Zeit statt jetzt (Tests)")
    a = p.parse_args(argv)

    now = _dt.datetime.fromisoformat(a.now) if a.now else _dt.datetime.now(_dt.timezone.utc)
    f = Fetcher(a.offline)
    result, text, errors = {}, [], []
    want = {"brief": ["quote", "news", "calendar"], "quote": ["quote"], "levels": ["quote"],
            "news": ["news"], "calendar": ["calendar"]}[a.cmd]

    if "quote" in want:
        try:
            q = quote(f)
            lv = None
            if a.cmd in ("brief", "levels"):
                try:
                    lv = levels(f)
                except FetchError as e:
                    errors.append(str(e))
            result["quote"], result["levels"] = q, lv
            text.append(render_quote(q, lv))
        except FetchError as e:
            errors.append(str(e))
    if "news" in want:
        try:
            items, total, hidden = news(f, now, a.hours, a.all, remember=not a.offline, everything=a.everything)
            result["news"] = items
            text.append(render_news(items, total, a.hours, hidden))
        except (FetchError, ET.ParseError) as e:
            errors.append("News: %s" % e)
    if "calendar" in want:
        try:
            ev = calendar(f, now, tuple(a.countries.upper().split(",")),
                          tuple(s.strip().capitalize() for s in a.impact.split(",")), a.days)
            result["calendar"] = ev
            text.append(render_calendar(ev, now))
        except (FetchError, ValueError) as e:
            errors.append("Kalender: %s" % e)

    if a.json:
        result["errors"] = errors
        print(json.dumps(result, indent=1, ensure_ascii=False))
    else:
        print("\n\n".join(text))
        for e in errors:
            print("FEHLER: %s" % e, file=sys.stderr)
        print("\nKostenlose, verzögerte, inoffizielle Daten. Keine Anlageberatung.")
    return 1 if errors and not result else 0


if __name__ == "__main__":
    sys.exit(main())

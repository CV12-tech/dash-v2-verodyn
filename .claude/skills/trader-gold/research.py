#!/usr/bin/env python3
"""Run setups over saved data.

    python3 research.py DATA_DIR [setup ...]          # report every setup (live and watch)
    python3 research.py DATA_DIR --write-stats        # also write setups/stats.json for the pushes

DATA_DIR holds Yahoo chart JSON named <series>-<tf>.json: gc-5m, gc-15m,
gc-1h, gc-1d, dxy-*, tnx-*, si-*. In-sample is 1h before SPLIT_1H; 1h from
SPLIT_1H on is out-of-sample, and the last 60 days of 5m/15m are a second
check.
"""

import importlib
import json
import os
import pkgutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import Ctx, load_yahoo, metrics, report, simulate, split  # noqa: E402

SPLIT_1H = "2026-01-01"
STATS = os.path.join(HERE, "setups", "stats.json")


def load_dir(d):
    out = {}
    for f in os.listdir(d):
        if f.endswith(".json"):
            with open(os.path.join(d, f), "rb") as fh:
                out[f[:-5]] = load_yahoo(fh.read())
    return out


def contexts(data):
    ctxs = {}
    for tf in ("5m", "15m", "1h"):
        if "gc-" + tf in data:
            extras = {k.split("-")[0]: v for k, v in data.items() if k.endswith("-" + tf) and not k.startswith("gc")}
            ctxs[tf] = Ctx(data["gc-" + tf], daily=data.get("gc-1d"), extras=extras)
    return ctxs


def all_setups(watch=True):
    """{name: (fn, tf, params)} from setups/*.py; watch=True adds the WATCH tier."""
    import setups
    reg = {}
    for m in pkgutil.iter_modules(setups.__path__):
        mod = importlib.import_module("setups." + m.name)
        reg.update(mod.SETUPS)
        if watch:
            reg.update(getattr(mod, "WATCH", {}))
    return reg


def watch_names():
    return set(all_setups(True)) - set(all_setups(False))


def run(data, names=None, write_stats=False):
    ctxs = contexts(data)
    reg = all_setups()
    watch = watch_names()
    stats = {}
    for name in names or sorted(reg):
        fn, live_tf, params = reg[name]
        st = {"tf": live_tf, "tier": "watch" if name in watch else "live"}
        for tf in ("1h", "15m", "5m"):
            ctx = ctxs.get(tf)
            if ctx is None:
                continue
            trades = simulate(ctx, fn(ctx, **params), name)
            print(report("%s @ %s%s" % (name, tf, " (Live)" if tf == live_tf else ""), trades,
                         SPLIT_1H if tf == "1h" else None))
            if tf == "1h":
                a, b = split(trades, SPLIT_1H)
                st["is"], st["oos"] = metrics(a), metrics(b)
            else:
                st[tf] = metrics(trades)
        stats[name] = st
    if write_stats:
        with open(STATS, "w") as f:
            json.dump(stats, f, indent=1, default=str)
        print("-> %s" % STATS)
    return stats


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run(load_dir(args[0]), args[1:] or None, write_stats="--write-stats" in sys.argv)


if __name__ == "__main__":
    main()

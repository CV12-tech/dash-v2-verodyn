"""Setup registry for trader-gold.

Each module defines SETUPS = {name: (fn, timeframe, params)} for setups that
passed the out-of-sample check (pushed with high priority) and may define
WATCH in the same shape for near misses that are pushed as experimental."""

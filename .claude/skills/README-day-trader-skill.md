# Day Trader skill pack

The `trader-*` folders are vendored from
https://github.com/Jakeschincariol/day-trader-skill at commit 3d0f4ef
(MIT, see `LICENSE-day-trader-skill`). The upstream README has the full guide.

Skills write their working files to a `trader/` folder at the repo root,
which is git-ignored because it holds your account size, limits and positions.

Setup:
- SEC tools (news, analyst): set `SEC_USER_AGENT="Your Name you@example.com"`
  or put `"sec_user_agent"` in `trader/config.json`.
- Broker: add Alpaca's MCP server with paper keys, see
  `trader-broker/claude_desktop_config.example.json`. Never paste keys in chat.

To update: re-clone upstream and copy the `trader-*` folders over these.

## trader-gold (own addition, not upstream)

`/trader-gold` is a gold (XAU/USD) desk built for this repo: price and levels
from Yahoo's GC=F future, gold and macro news, and the ForexFactory economic
calendar in German time. It needs `nfs.faireconomy.media` allowed for the
calendar. Tests: `python3 -m unittest discover -s .claude/skills/trader-gold/tests`.

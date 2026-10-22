---
name: trader-gold
description: >-
  Gold-Desk für XAU/USD. Zeigt den Goldpreis (COMEX-Future GC=F) mit
  24h-Spanne, Asien-Session, Vortag, 20-Tage-Hoch/Tief, SMA20/50 und ATR,
  die neuen Gold- und Makro-News (Yahoo, inkl. Investing.com-Berichte,
  Minenaktien-Rauschen gefiltert) und den Wirtschaftskalender mit den
  USD-Terminen, die Gold bewegen (CPI, PCE, NFP, FOMC, Jobless Claims ...),
  alles in deutscher Zeit. Use when the user says "Gold", "XAU/USD", "XAUUSD",
  "Goldpreis", "wie steht Gold", "Gold-News", "Wirtschaftskalender",
  "Termine heute", "was steht heute an", "Briefing", "Morgen-Briefing",
  "economic calendar", "gold news", or asks about the market when only gold
  is being traded.
argument-hint: "[quote|levels|news|calendar]"
---

# trader-gold

Der Nutzer handelt nur einen Markt: **XAU/USD**. Antworte auf Deutsch.

Tool in diesem Ordner (Python-Standardbibliothek, keine Keys):

```bash
python3 "${CLAUDE_SKILL_DIR}/gold.py"                    # Briefing: Kurs + Marken + News + Kalender
python3 "${CLAUDE_SKILL_DIR}/gold.py" quote              # nur Kurs
python3 "${CLAUDE_SKILL_DIR}/gold.py" levels             # Kurs + Marken (ATR, 20 Tage, SMAs, Vortag)
python3 "${CLAUDE_SKILL_DIR}/gold.py" news --hours 12     # neue Meldungen (--all: auch gezeigte, --everything: auch Minenaktien)
python3 "${CLAUDE_SKILL_DIR}/gold.py" calendar --days 3  # USD, Wichtigkeit hoch + mittel
python3 "${CLAUDE_SKILL_DIR}/gold.py" calendar --countries USD,EUR,CNY --impact High
python3 "${CLAUDE_SKILL_DIR}/gold.py" --json             # maschinenlesbar
```

Run it from the project root: state lands in `trader/state/` (git-ignored).

## Quellen

| was | Quelle | Hinweis |
| --- | --- | --- |
| Kurs, Kerzen | Yahoo-Chart für `GC=F` (COMEX Gold, Frontmonat) | Yahoo hat kein Spot-XAU/USD mehr. Der Future liegt meist ein paar Dollar über Spot, bewegt sich aber gleich. Verzögert, inoffiziell. |
| News | Yahoo-RSS für `GC=F` | enthält Investing.com-Goldberichte, markiert `[Investing.com]` |
| Kalender | ForexFactory-Wochenexport `nfs.faireconomy.media` | 30 Min. gecacht (Rate-Limit). Domain muss in der Netzwerkfreigabe stehen. |
| Ersatz | FMP-Connector `mcp__FMP__commodity` (`commodities-quote-short`, Symbol `GCUSD`) | wenn Yahoo ausfällt; News/Kalender braucht einen höheren FMP-Tarif |

investing.com selbst wird nicht abgerufen: keine API, Scraping laut Nutzungsbedingungen verboten.

## Regeln

- **Erst die Zahlen, dann die Deutung.** Kurs, Spanne und nächster ★-Termin zuerst.
  Danach höchstens zwei Sätze, was die News sagen, mit Quelle und Link.
- **Schlagzeilen sind Hinweise, keine Fakten.** Vor einer Aussage den Artikel öffnen.
  Paywall nicht gelesen → sagen.
- **Termine sind Risiko.** Steht ein ★-Termin (hoch) in den nächsten 60 Minuten an,
  sag das deutlich: Spreads weiten sich, Stopps können durchrutschen.
- **ATR einordnen.** Die heutige Spanne (24h Hoch − Tief) gegen die ATR stellen:
  ist der Tagesrahmen schon ausgeschöpft?
- **Keine Prognosen, keine Empfehlung.** Was ist, nicht was kommen wird.
- **Fehler offen nennen.** Meldet das Tool `FEHLER: ... nicht erreichbar`, sag welche
  Domain fehlt (Netzwerkfreigabe) und mache mit dem Rest weiter. Nie Daten erfinden.

## Signale und Push (signals.py, engine.py, setups/)

Mechanische Regeln, keine KI-Vorhersage. Signale nur für Kerzen, die 08:00–20:00
deutscher Zeit schließen; offene Trades sind um 22:00 flat. Die Live-Setups haben kein
festes Ziel: Gewinner laufen bis 22:00, Verlierer enden am Stopp (`target_r=50`). Jede Strategie liegt in
`setups/*.py` und wird von `engine.py` gleich simuliert (Einstieg zum Schlusskurs,
Kerze mit Stopp und Ziel zählt als Stopp, Gap durch den Stopp zum Eröffnungskurs,
0,40 $/oz Kosten).

Zwei Stufen:
- `SETUPS` (live, Push mit hoher Priorität): bestanden 2024–25 (PF ≥ 1,15, n ≥ 80) UND
  2026 (PF ≥ 1,1, n ≥ 25). Zusammen ~3 Signale/Woche:
  - **VWAP-Pullback im Trend (1h)**, nur Signale bis 12:00: 2024–25 PF 1,85 (145), 2026 PF 2,23 (74)
  - **Asien-Breakout + Dollar (1h)**: 2024–25 PF 1,42 (93), 2026 PF 2,65 (49)
  - Paket: +127 R in 2,4 Jahren, jedes Jahr positiv, größter Rückgang −10,7 R
- `WATCH` (experimentell, Push mit niedriger Priorität, max. ★): VWAP-Fade (1h),
  London-Opening-Range (15m), VWAP-Pullback 15m.

Optimierung 10/2026 (gewählt auf 1h 2024–25, danach auf 2026 geprüft): kein festes Ziel
statt 1,5 R (hilft in beiden Zeiträumen); VWAP-Pullback-Signale nach 12:00 haben keine
Kante (2026 PF 0,87). Verworfen, weil 2026 nicht bestätigt oder ohne Effekt: Dollar-Filter
auf dem VWAP-Pullback, Stopp auf Einstand, nachlaufender Stopp, Teilgewinne. Über Nacht
halten bringt kaum mehr, kostet aber Swap und Gap-Risiko.

Push-Qualität: ★ aus dem PF im Prüfzeitraum 2026 (`setups/stats.json`), +1 wenn mehrere
Setups binnen 60 Min. in dieselbe Richtung zeigen. Kalendersperre 30 Min. vor bis 15 Min.
nach einem hohen oder ★-Termin.

```bash
python3 "${CLAUDE_SKILL_DIR}/signals.py" scan              # heutige Signale und Stand
python3 "${CLAUDE_SKILL_DIR}/signals.py" notify --dry-run  # was gepusht würde
python3 "${CLAUDE_SKILL_DIR}/signals.py" backtest          # alle Setups, ~2 J. 1h + 60 Tage 15m/5m
python3 "${CLAUDE_SKILL_DIR}/research.py" DATA_DIR --write-stats   # Statistik für die Sterne neu
```

Neue Strategie: Funktion `setup(ctx, **params) -> [engine.signal(...)]` in `setups/`,
erst in `WATCH`, nach bestandener Prüfung in `SETUPS`. Der Test
`tests/test_signals.py` prüft automatisch, dass kein Setup in die Zukunft schaut.
Getunt wird nur auf 1h vor 2026; 2026 bleibt Prüfzeitraum.

Push: `.github/workflows/gold-signals.yml` läuft werktags alle 15 Min. und schickt
neue Signale und deren Ergebnis an ntfy (Repo-Secret `NTFY_TOPIC`). Jeder Push kommt einmal.

Beim Nennen von Backtest-Zahlen immer dazu sagen: Kosten geschätzt, Regimewechsel möglich,
Vergangenheit ist keine Prognose.

## Echtzeit über TradingView

`tradingview/gold_signals.pine` enthält beide Live-Setups als einen TradingView-Indikator
(Pine v5, 1h-Chart OANDA:XAUUSD, Dollar-Index TVC:DXY). TradingView prüft jede Kerze auf seinen Servern und
schickt Alarme in Echtzeit an die TradingView-App, per Webhook auch an ntfy
(`https://ntfy.sh/<NTFY_TOPIC>`, Webhooks brauchen einen bezahlten Tarif).
TradingView wird nie gecrawlt: keine API, Scraping verstößt gegen die Nutzungsbedingungen.
Der Kalender ist in Pine nicht verfügbar; vor einem Einstieg `gold.py calendar` prüfen.

## Zusammenspiel mit dem restlichen Pack

Die übrigen `trader-*`-Skills sind für US-Aktien gebaut (NYSE-Zeiten, Alpaca-Aktienorders,
nur Long). Für Gold sind sie nicht direkt verwendbar; Positionsgröße und Stopp bei Gold
rechnen sich über Kontraktgröße bzw. Lot (1 Lot XAU/USD = 100 oz bei den meisten
CFD-Brokern, Future GC = 100 oz, Micro MGC = 10 oz). Frag nach Broker und Instrument,
bevor du eine Positionsgröße nennst.

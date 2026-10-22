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

## Signale und Push (signals.py)

Mechanische Regeln, keine KI-Vorhersage. Alle Zeiten Berlin, 5-Min-Kerzen GC=F:

1. Asien-Spanne = Hoch/Tief 00:00–08:00. Gehandelt nur bei 0,25–1,0 Tages-ATR.
2. Trendfilter: KAUF nur wenn letzter Tagesschluss > SMA20, VERKAUF nur wenn darunter.
3. Signal: erster abgeschlossener 5-Min-Schluss zwischen 08:00 und 16:00 über dem
   Asien-Hoch (Kauf) bzw. unter dem Asien-Tief (Verkauf). Ein Signal pro Tag.
4. Stopp = Mitte der Asien-Spanne, Ziel = 1,5 R, sonst flat um 21:00.
5. Kalendersperre: kein Einstieg 30 Min. vor bis 15 Min. nach einem hohen oder ★-Termin.

```bash
python3 "${CLAUDE_SKILL_DIR}/signals.py" scan              # heutiger Stand und warum
python3 "${CLAUDE_SKILL_DIR}/signals.py" backtest          # Regeln auf ~60 Tage 5-Min-Daten
python3 "${CLAUDE_SKILL_DIR}/signals.py" backtest --no-trend --target-r 2
python3 "${CLAUDE_SKILL_DIR}/signals.py" notify --dry-run  # was gepusht würde
```

Push: `.github/workflows/gold-signals.yml` läuft werktags alle 15 Min. und schickt
neue Signale und deren Ergebnis (Ziel, Stopp, Feierabend) an ntfy, Thema aus dem
Repo-Secret `NTFY_TOPIC`. Jeder Push kommt einmal.

Beim Nennen von Backtest-Zahlen immer dazu sagen: kleine Stichprobe, ohne Spread und
Slippage, ohne Kalendersperre (ForexFactory hat keine Historie), Vergangenheit ist
keine Prognose.

## Zusammenspiel mit dem restlichen Pack

Die übrigen `trader-*`-Skills sind für US-Aktien gebaut (NYSE-Zeiten, Alpaca-Aktienorders,
nur Long). Für Gold sind sie nicht direkt verwendbar; Positionsgröße und Stopp bei Gold
rechnen sich über Kontraktgröße bzw. Lot (1 Lot XAU/USD = 100 oz bei den meisten
CFD-Brokern, Future GC = 100 oz, Micro MGC = 10 oz). Frag nach Broker und Instrument,
bevor du eine Positionsgröße nennst.

# Wishlist — deferred items pending paid/better data access

Items below are things we'd add or improve if paid/institutional data access becomes available. Not built into v1 because free-tier data can't support them reliably.

## Data sources
- **Bloomberg Terminal / FactSet / S&P Capital IQ (sp-global plugin)** — real fundamentals, real-time quotes, consensus estimates. Would replace Yahoo Finance scraping and manual WebSearch estimate-gathering.
- **LSEG/Refinitiv (`lseg` plugin, claude-for-financial-services marketplace)** — bond pricing, yield curves, FX carry, options valuation. Correct tool for Point 4 (fixed income) once available.
- **MarketChameleon / Unusual Whales / CBOE DataShop** — real single-name options volume/OI spike detection. Currently approximated with free aggregate-only signals (VIX term structure, CBOE total put/call ratio) — no per-stock granularity.
- **Crunchbase / PitchBook** — structured private-company funding round data for Point 2 (trend monitor) drilldowns. Currently sourced via WebSearch news mentions only — less complete, less structured.
- **CoinPaprika MCP** (`coinpaprika/claude-marketplace`, free, not installed) — crypto/DeFi market data. Only relevant if a crypto shock is driving Point 1's "other markets" trigger, or if Point 2 grows a dedicated crypto/blockchain-infra sector. Skipped for v1 since WebSearch fallback already catches shocks large enough to matter.
- **Paid free-tier upgrades** (Alpha Vantage, Financial Modeling Prep, Finnhub) — would need account signup + API key from user. Not required for v1; current free/unauthenticated sources (Yahoo Finance query endpoints, FRED CSV, NASDAQ Trader symbol directory, SEC EDGAR) cover Phase 1 scope.

- **Real fundamentals (trailing/forward P/E, EV/EBITDA) at universe scale** — Yahoo's `.info` endpoint has these fields but is slow/rate-limit-prone across ~1500 tickers for free. The "value/fundamental discount" recommendation bucket currently uses a 52-week-high-discount proxy (`pipeline/build_recommendations.py`) instead of true P/E-vs-history/peers. A paid fundamentals API (FMP, Alpha Vantage premium) or `.info` calls limited to a small pre-screened shortlist would fix this properly.

## Features
- **Interactive per-security price charts on Point 3** — tried this (Chart.js modal, "Chart" buttons everywhere) but pulled it back out: coverage was necessarily limited to the ~52 "featured" tickers that happen to appear in a gainers/losers/recommendations pull, so most names (sector tables, freshly-added portfolio tickers) showed "not available" instead of a chart — inconsistent enough that it wasn't worth shipping. Point 1 keeps its version since every series there has full history unconditionally. Revisit for Point 3 only once there's a way to fetch 1y history for the full ~1500-name universe (bigger/slower pre-bake) or on-demand per click (needs a live capability, not just a bigger pre-bake).
- **Automated cron refresh** — v1 is on-demand only (user-triggered). Move to scheduled daily regeneration once data pipeline and format are validated.
- **Live "Ask Claude" drill-down capability** — v1 drill-downs are pre-baked at pipeline run for items actually shown. A live on-demand query capability would let a user ask about any item not already featured, at the cost of per-click latency/API spend.
- **International index coverage** — v1 tracks US indices only (S&P 500, Nasdaq, Dow, Russell 2000, VIX); a foreign index only surfaces when it's driving that day's story, not as a standing tile.
- **Structured credit (ABS/CMBS/CLO) dedicated data feed** — no plugin or free source found covering this; Point 4 methodology is hand-built from FRED spread series, Fed/rating-agency commentary, and news. An `lseg` subscription (see above) would be the natural upgrade.

## Known data-freshness gaps (free tier)
- **FRED WTI crude series (DCOILWTICO) implausible day-to-day swings** (first encountered 2026-10-01
  pull) — the daily series printed $85.23 (2026-09-25), $99.37 (2026-09-28), then $96.16 (2026-09-29),
  swings no independent source corroborates: Investing.com's historical WTI data shows a comparatively
  narrow $89-94 band across that same window (Sept 25 ~$92.41, Sept 28 ~$92.60-93.58, Sept 29 close
  ~$89.38-90.54), and Robinhood's intraday WTI prediction-market data for both Sept 25 and Sept 29
  clusters tightly around those same independently-reported levels throughout each trading day. Real
  oil-market volatility was genuinely elevated this stretch (the Brent-WTI spread blew out to ~$12.83,
  its widest since May, as Brent drew a geopolitical premium from stalled Hormuz reopening talks while
  WTI weakened on US diesel-export-ban talk and rising Saudi/UAE exports) - so this isn't a quiet week
  for oil, but FRED's specific day-over-day dollar levels over Sept 25-29 don't match that real story
  either. Read as a data-quality issue (possibly a contract-date misalignment) in FRED's free daily
  series rather than a genuine multi-day round-trip of that magnitude. This pull's oil_move materiality
  flag still fires (FRED's own -3.2% day change) and happens to roughly match the real, independently-
  reported ~3.5-3.8% WTI decline on Sept 29 - so the flag's narrative cites the real, dated news
  driving that actual decline rather than FRED's specific (likely wrong) dollar levels. A paid
  real-time commodities feed (or even a second free cross-check source pulled automatically rather
  than by hand) would catch this kind of single-series anomaly before it reaches the dashboard.
- **yfinance bulk equity-history lag** (first encountered 2026-09-22 pull) — the free Yahoo Finance `yf.download` bulk endpoint `fetch_price_history.py` uses for the ~1,500-name universe can lag a full trading day behind the individual index tickers (`^GSPC`, `^IXIC`, etc.) `fetch_indices.py` pulls separately. On the first 2026-09-22 pull, run ~4.5 hours after Monday's close, every individual-equity daily bar was still `NaN` for Monday while the index tickers already had Monday's close — so Point 3's movers/gainers/losers table initially reflected Friday's session even though Point 1's index-level flags were already Monday-fresh (a later same-day re-pull, ~2 hours on, caught up once Yahoo did). **Now mitigated in code, not just docs**: `fetch_price_history.py` compares its own data's as-of date against `indices.json`, retries once, and sets a `stale` flag (`data/point3/aggregates.json`'s `equity_data_stale`) that `build_final_payloads.py` surfaces as an automatic freshness-note caveat when no hand-written override exists — see CLAUDE.md's "Equity-data freshness self-check" section. This doesn't eliminate the underlying Yahoo lag (a paid fundamentals/price API would), just makes it visible and self-documenting instead of a silent multi-hour trap a curator has to notice by hand; still re-run `fetch_price_history.py` later in the day if `equity_data_stale` comes back `true` and today's exact movers matter.

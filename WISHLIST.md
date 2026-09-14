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

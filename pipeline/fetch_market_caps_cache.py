"""Slow, once-in-a-while market cap cache builder. Market cap changes slowly
(shares outstanding rarely moves day to day), so this does NOT need to run on
every dashboard refresh - fetch_price_history.py (fast, bulk) handles the
price/day-change numbers that DO need to be fresh every pull. Run this
roughly weekly to keep the $2B+ cap filter and sector-cap-weighting accurate.

Uses yfinance.Tickers().fast_info per ticker (the only way to get market cap
for free - Yahoo's raw v7 quote endpoint now 401s without an auth crumb).
Slow (~10-15 min for 1500 tickers) and rate-limit-prone, hence the caching.
"""
import json
import sys
import time

import yfinance as yf

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BATCH = 20
PER_TICKER_DELAY = 0.35
PER_BATCH_DELAY = 1.5


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def fetch_one(sym, tk):
    fi = tk.tickers[sym].fast_info
    return {"market_cap": fi.get("marketCap")}


def fetch_via_yfinance(tickers):
    """yfinance.Tickers fast_info - manages Yahoo's crumb/cookie auth internally
    (the raw v7 quote endpoint now 401s without one)."""
    results = {}
    failed = []
    rate_limited = False
    for batch in chunks(tickers, BATCH):
        tk = yf.Tickers(" ".join(batch))
        for sym in batch:
            try:
                results[sym] = fetch_one(sym, tk)
            except Exception as e:
                failed.append(sym)
                if "Rate limit" in str(e) or "Too Many" in str(e):
                    rate_limited = True
            time.sleep(PER_TICKER_DELAY)
        print(f"  batch done ({len(results)} ok, {len(failed)} failed so far)", file=sys.stderr)
        if rate_limited:
            print("  RATE LIMITED - backing off 30s", file=sys.stderr)
            time.sleep(30)
            rate_limited = False
        else:
            time.sleep(PER_BATCH_DELAY)
    # one retry pass for failures (often transient rate-limit blips)
    if failed:
        print(f"Retrying {len(failed)} failed tickers after cooldown...", file=sys.stderr)
        time.sleep(15)
        for batch in chunks(failed, BATCH):
            tk = yf.Tickers(" ".join(batch))
            for sym in batch:
                try:
                    results[sym] = fetch_one(sym, tk)
                except Exception:
                    pass
                time.sleep(PER_TICKER_DELAY)
            time.sleep(PER_BATCH_DELAY)
    return results


def main():
    from datetime import datetime, timezone

    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = json.load(f)["universe"]
    tickers = [u["ticker"] for u in universe]
    print(f"Fetching market caps for {len(tickers)} tickers...", file=sys.stderr)

    results = fetch_via_yfinance(tickers)

    print(f"Got market caps for {len(results)}/{len(tickers)}", file=sys.stderr)
    out = {"as_of": datetime.now(timezone.utc).isoformat(), "market_caps": results}
    with open("data/point3/market_caps_cache.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Wrote data/point3/market_caps_cache.json", file=sys.stderr)


if __name__ == "__main__":
    main()

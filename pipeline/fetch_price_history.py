"""Fast bulk price/volume pull for the whole universe via yf.download (one
batched, internally-threaded call per chunk) instead of per-ticker fast_info
calls. This is the script that runs on every on-demand refresh - fast enough
to not make "pull the dashboard" a 10-minute wait. Market cap (slow-changing)
is cached separately by fetch_market_caps.py and merged in later.
"""
import json
import sys

import yfinance as yf

CHUNK = 200  # yf.download handles a list fine; chunk to keep any one call small


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def main():
    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = json.load(f)["universe"]
    tickers = [u["ticker"] for u in universe]
    print(f"Bulk price/volume pull for {len(tickers)} tickers...", file=sys.stderr)

    results = {}
    for batch in chunks(tickers, CHUNK):
        print(f"  downloading batch of {len(batch)}...", file=sys.stderr)
        data = yf.download(
            batch, period="1y", interval="1d", group_by="ticker",
            threads=True, progress=False, auto_adjust=False,
        )
        for t in batch:
            try:
                if len(batch) == 1:
                    sub = data
                else:
                    sub = data[t]
                closes = sub["Close"].dropna()
                volumes = sub["Volume"].dropna()
                if closes.empty:
                    continue
                last = float(closes.iloc[-1])
                prev = float(closes.iloc[-2]) if len(closes) > 1 else last
                day_chg_pct = (last - prev) / prev * 100 if prev else None
                five_ago = float(closes.iloc[-6]) if len(closes) > 5 else float(closes.iloc[0])
                five_day_chg_pct = (last - five_ago) / five_ago * 100 if five_ago else None
                last_vol = int(volumes.iloc[-1]) if not volumes.empty else None
                avg_vol = int(volumes.tail(60).mean()) if not volumes.empty else None
                year_high = float(closes.max())
                year_low = float(closes.min())
                pct_off_high = (last - year_high) / year_high * 100 if year_high else None
                results[t] = {
                    "price": round(last, 4),
                    "day_chg_pct": round(day_chg_pct, 3) if day_chg_pct is not None else None,
                    "five_day_chg_pct": round(five_day_chg_pct, 3) if five_day_chg_pct is not None else None,
                    "volume": last_vol,
                    "avg_volume": avg_vol,
                    "year_high": round(year_high, 4),
                    "year_low": round(year_low, 4),
                    "pct_off_52wk_high": round(pct_off_high, 2) if pct_off_high is not None else None,
                }
            except Exception as e:
                print(f"  skip {t}: {e}", file=sys.stderr)

    print(f"Got price history for {len(results)}/{len(tickers)}", file=sys.stderr)
    with open("data/point3/price_history.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Wrote data/point3/price_history.json", file=sys.stderr)


if __name__ == "__main__":
    main()

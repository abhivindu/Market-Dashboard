"""Fetch 1-year daily close history for every ticker actually shown on the
Point 3 dashboard (gainers, losers, volume outliers, recommendation picks) -
the "featured" set that needs an interactive chart. Bulk yf.download, same
fast path as fetch_price_history.py. Portfolio holdings added manually by
the user (outside this featured set) won't have a chart until they appear
in a future gainers/losers/recommendations pull - documented limitation.
"""
import json
import sys

import yfinance as yf


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def collect_featured_tickers():
    tickers = set()
    with open("data/point3/aggregates.json", encoding="utf-8") as f:
        agg = json.load(f)
    for m in agg.get("top_gainers", []):
        tickers.add(m["ticker"])
    for m in agg.get("top_losers", []):
        tickers.add(m["ticker"])
    for m in agg.get("volume_outliers", []):
        tickers.add(m["ticker"])
    try:
        with open("data/point3/recommendations_shortlist.json", encoding="utf-8") as f:
            recs = json.load(f)
        for bucket in ("bounce", "value", "speculative"):
            for r in recs.get(bucket, []):
                tickers.add(r["ticker"])
    except FileNotFoundError:
        pass
    return sorted(tickers)


def main():
    tickers = collect_featured_tickers()
    print(f"Fetching 1y history for {len(tickers)} featured tickers...", file=sys.stderr)

    results = {}
    for batch in chunks(tickers, 100):
        data = yf.download(
            batch, period="1y", interval="1d", group_by="ticker",
            threads=True, progress=False, auto_adjust=False,
        )
        for t in batch:
            try:
                sub = data[t] if len(batch) > 1 else data
                closes = sub["Close"].dropna()
                if closes.empty:
                    continue
                # thin to ~120 points max (still plenty for an interactive chart, keeps payload small)
                step = max(1, len(closes) // 120)
                thinned = closes.iloc[::step]
                results[t] = [
                    {"date": d.strftime("%Y-%m-%d"), "close": round(float(c), 2)}
                    for d, c in thinned.items()
                ]
            except Exception as e:
                print(f"  skip {t}: {e}", file=sys.stderr)

    print(f"Got history for {len(results)}/{len(tickers)}", file=sys.stderr)
    with open("data/point3/featured_history.json", "w", encoding="utf-8") as f:
        json.dump(results, f)
    print("Wrote data/point3/featured_history.json", file=sys.stderr)


if __name__ == "__main__":
    main()

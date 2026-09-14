"""Pull index-level data (S&P 500, Nasdaq, Dow, Russell 2000, VIX) via yfinance.
Free, unofficial Yahoo Finance API - no key required.
"""
import json
import sys
from datetime import datetime, timezone

import yfinance as yf

INDICES = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
    "RUSSELL2000": "^RUT",
    "VIX": "^VIX",
}


def fetch_index(name, ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1mo", interval="1d")
    if hist.empty:
        return None
    closes = hist["Close"]
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) > 1 else last
    day_chg_pct = (last - prev) / prev * 100 if prev else 0.0
    # 5-day change
    five_ago = float(closes.iloc[-6]) if len(closes) > 5 else float(closes.iloc[0])
    five_day_chg_pct = (last - five_ago) / five_ago * 100 if five_ago else 0.0
    # 1-month change
    first = float(closes.iloc[0])
    month_chg_pct = (last - first) / first * 100 if first else 0.0
    return {
        "name": name,
        "ticker": ticker,
        "last": round(last, 2),
        "day_chg_pct": round(day_chg_pct, 3),
        "five_day_chg_pct": round(five_day_chg_pct, 3),
        "month_chg_pct": round(month_chg_pct, 3),
        "history": [
            {"date": d.strftime("%Y-%m-%d"), "close": round(float(c), 2)}
            for d, c in closes.items()
        ],
    }


def main():
    out = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "indices": {},
    }
    for name, ticker in INDICES.items():
        print(f"Fetching {name} ({ticker})...", file=sys.stderr)
        data = fetch_index(name, ticker)
        if data:
            out["indices"][name] = data
        else:
            print(f"  WARNING: no data for {name}", file=sys.stderr)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

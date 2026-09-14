"""Pull macro/rates series from FRED's free CSV endpoint (no key required)
and CBOE put/call ratio for the options-aggregate section.
"""
import io
import json
import sys
from datetime import datetime, timezone

import pandas as pd
import requests
import yfinance as yf

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

FRED_SERIES = {
    # benchmark rates
    "DGS3MO": "3-Month Treasury Yield",
    "DGS2": "2-Year Treasury Yield",
    "DGS10": "10-Year Treasury Yield",
    "DGS30": "30-Year Treasury Yield",
    "DFF": "Effective Federal Funds Rate",
    "SOFR": "Secured Overnight Financing Rate",
    # spreads (yield-curve + credit)
    "T10Y2Y": "10Y-2Y Treasury Spread",
    "T10Y3M": "10Y-3M Treasury Spread",
    "BAMLC0A0CM": "ICE BofA US Corporate Index OAS (IG credit spread)",
    "BAMLC0A4CBBB": "ICE BofA BBB US Corporate Index OAS (credit spread)",
    "BAMLH0A0HYM2": "ICE BofA US High Yield Index OAS (credit spread)",
    # commodities / FX (WTI here; gold/silver fetched separately via Yahoo)
    "DCOILWTICO": "WTI Crude Oil Price",
    "DTWEXBGS": "Trade-Weighted US Dollar Index",
}

YAHOO_COMMODITIES = {
    "GOLD": ("GC=F", "Gold (COMEX front-month)"),
    "SILVER": ("SI=F", "Silver (COMEX front-month)"),
}


def fetch_fred_series(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df = df.tail(60)  # last ~60 observations
    return df


def series_summary(df, label, series_id):
    if df.empty:
        return None
    last_row = df.iloc[-1]
    last_val = float(last_row["value"])
    prev_val = float(df.iloc[-2]["value"]) if len(df) > 1 else last_val
    chg = last_val - prev_val
    month_ago_val = float(df.iloc[-22]["value"]) if len(df) > 22 else float(df.iloc[0]["value"])
    month_chg = last_val - month_ago_val
    return {
        "series_id": series_id,
        "label": label,
        "last_value": round(last_val, 4),
        "last_date": str(last_row["date"]),
        "day_chg": round(chg, 4),
        "month_chg": round(month_chg, 4),
        "history": [
            {"date": str(r["date"]), "value": round(float(r["value"]), 4)}
            for _, r in df.iterrows()
        ],
    }


def fetch_yahoo_commodity(ticker, label):
    """Gold/silver via Yahoo Finance futures (GC=F, SI=F) - FRED's free gold/silver
    fixing series were discontinued, so this is the free/unauthenticated route."""
    hist = yf.Ticker(ticker).history(period="3mo", interval="1d")
    if hist.empty:
        return None
    closes = hist["Close"].dropna()
    last_val = float(closes.iloc[-1])
    prev_val = float(closes.iloc[-2]) if len(closes) > 1 else last_val
    chg = last_val - prev_val
    month_ago_val = float(closes.iloc[-22]) if len(closes) > 22 else float(closes.iloc[0])
    month_chg = last_val - month_ago_val
    return {
        "series_id": ticker,
        "label": label,
        "last_value": round(last_val, 2),
        "last_date": closes.index[-1].strftime("%Y-%m-%d"),
        "day_chg": round(chg, 2),
        "month_chg": round(month_chg, 2),
        "history": [
            {"date": d.strftime("%Y-%m-%d"), "value": round(float(c), 2)}
            for d, c in closes.tail(60).items()
        ],
    }


def fetch_vol_term_structure():
    """VIX term structure (spot vs 9-day vs 3-month) via yfinance - free.
    CBOE's own put/call CSV endpoint blocks non-browser requests (403), so this
    is the aggregate vol signal used instead: contango (VIX < VIX3M) = calm,
    backwardation (VIX > VIX3M) = stress/fear priced into near-term options.
    """
    tickers = {"VIX": "^VIX", "VIX9D": "^VIX9D", "VIX3M": "^VIX3M"}
    out = {}
    for name, t in tickers.items():
        try:
            hist = yf.Ticker(t).history(period="3mo", interval="1d")
            if hist.empty:
                continue
            closes = hist["Close"]
            out[name] = {
                "last_value": round(float(closes.iloc[-1]), 2),
                "history": [
                    {"date": d.strftime("%Y-%m-%d"), "value": round(float(c), 2)}
                    for d, c in closes.tail(60).items()
                ],
            }
        except Exception as e:
            print(f"  WARNING: {t} fetch failed: {e}", file=sys.stderr)
    if "VIX" in out and "VIX3M" in out:
        vix = out["VIX"]["last_value"]
        vix3m = out["VIX3M"]["last_value"]
        out["structure"] = "backwardation (stress)" if vix > vix3m else "contango (calm)"
        out["vix_minus_vix3m"] = round(vix - vix3m, 2)
    return out if out else None


def main():
    out = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "series": {},
    }
    for series_id, label in FRED_SERIES.items():
        print(f"Fetching FRED {series_id} ({label})...", file=sys.stderr)
        try:
            df = fetch_fred_series(series_id)
            summary = series_summary(df, label, series_id)
            if summary:
                out["series"][series_id] = summary
        except Exception as e:
            print(f"  WARNING: {series_id} failed: {e}", file=sys.stderr)

    for key, (ticker, label) in YAHOO_COMMODITIES.items():
        print(f"Fetching {label} ({ticker}) via Yahoo...", file=sys.stderr)
        try:
            summary = fetch_yahoo_commodity(ticker, label)
            if summary:
                out["series"][key] = summary
        except Exception as e:
            print(f"  WARNING: {key} failed: {e}", file=sys.stderr)

    print("Fetching VIX term structure...", file=sys.stderr)
    vol = fetch_vol_term_structure()
    if vol:
        out["vol_term_structure"] = vol

    with open("data/point1/macro.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Wrote data/point1/macro.json", file=sys.stderr)


if __name__ == "__main__":
    main()

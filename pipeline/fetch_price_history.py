"""Fast bulk price/volume pull for the whole universe via yf.download (one
batched, internally-threaded call per chunk) instead of per-ticker fast_info
calls. This is the script that runs on every on-demand refresh - fast enough
to not make "pull the dashboard" a 10-minute wait. Market cap (slow-changing)
is cached separately by fetch_market_caps.py and merged in later.

Known gap (see WISHLIST.md): Yahoo's bulk `yf.download` endpoint used here
can lag a full trading day behind the individual index tickers (^GSPC etc.)
that fetch_indices.py pulls separately - e.g. still serving Friday's close
hours after Monday's close for the ~1,500-name universe while ^GSPC already
has Monday. This script now detects that by comparing the most common
last-bar date across tickers ("as_of_date", stored in the output's "_meta")
against data/point3/indices.json's latest date, retries once, and prints a
loud warning (rather than silently writing stale-but-plausible data) if the
gap persists - re-run this script again later if that happens.
"""
import json
import sys
import time
from collections import Counter

import yfinance as yf

CHUNK = 200  # yf.download handles a list fine; chunk to keep any one call small
RETRY_WAIT_SECONDS = 90


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def fetch_all(tickers):
    """Returns (results dict, Counter of each ticker's last-bar date)."""
    results = {}
    date_counts = Counter()
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
                last_date = closes.index[-1].strftime("%Y-%m-%d")
                date_counts[last_date] += 1
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
                    "last_date": last_date,
                }
            except Exception as e:
                print(f"  skip {t}: {e}", file=sys.stderr)
    return results, date_counts


def expected_latest_date():
    """Best-effort: the latest trading day per the index tickers, which
    Yahoo tends to update faster than the bulk equity endpoint. Returns
    None if indices.json isn't there yet or is unreadable - the caller
    just skips the staleness check in that case."""
    try:
        with open("data/point3/indices.json", encoding="utf-8") as f:
            indices = json.load(f)["indices"]
        return max(idx["history"][-1]["date"] for idx in indices.values() if idx.get("history"))
    except Exception:
        return None


def main():
    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = json.load(f)["universe"]
    tickers = [u["ticker"] for u in universe]
    print(f"Bulk price/volume pull for {len(tickers)} tickers...", file=sys.stderr)

    results, date_counts = fetch_all(tickers)
    as_of_date = date_counts.most_common(1)[0][0] if date_counts else None
    expected = expected_latest_date()
    stale = bool(expected and as_of_date and as_of_date < expected)

    if stale:
        print(
            f"  WARNING: bulk equity data's most common last-bar date is {as_of_date}, "
            f"but index tickers already have {expected} - Yahoo's bulk endpoint is lagging. "
            f"Retrying once after {RETRY_WAIT_SECONDS}s...",
            file=sys.stderr,
        )
        time.sleep(RETRY_WAIT_SECONDS)
        results, date_counts = fetch_all(tickers)
        as_of_date = date_counts.most_common(1)[0][0] if date_counts else None
        stale = bool(expected and as_of_date and as_of_date < expected)
        if stale:
            print(
                f"  WARNING: still stale after retry ({as_of_date} vs expected {expected}). "
                f"Proceeding with what's available - re-run this script again later (Yahoo's "
                f"bulk endpoint sometimes takes hours to catch up) and rebuild data/point3/* "
                f"if today's movers matter.",
                file=sys.stderr,
            )
        else:
            print(f"  Retry caught up: as_of_date is now {as_of_date}.", file=sys.stderr)

    print(f"Got price history for {len(results)}/{len(tickers)} (as_of_date: {as_of_date})", file=sys.stderr)
    output = {
        "_meta": {
            "as_of_date": as_of_date,
            "expected_date": expected,
            "stale": stale,
        },
        **results,
    }
    with open("data/point3/price_history.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print("Wrote data/point3/price_history.json", file=sys.stderr)


if __name__ == "__main__":
    main()

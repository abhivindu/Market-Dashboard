"""Pull upcoming earnings calendar via Nasdaq's free public calendar API
(no key required). Filters to our S&P 1500 universe so the calendar only
shows names we can actually build a drill-down for.
"""
import json
import sys
import time
from datetime import datetime, timedelta

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

DAYS_AHEAD = 10


def fetch_day(date_str):
    url = "https://api.nasdaq.com/api/calendar/earnings"
    try:
        r = requests.get(url, params={"date": date_str}, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        rows = (data.get("data") or {}).get("rows") or []
        return rows
    except Exception as e:
        print(f"  WARNING: earnings fetch failed for {date_str}: {e}", file=sys.stderr)
        return []


def main():
    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = {u["ticker"] for u in json.load(f)["universe"]}

    today = datetime.now()
    all_entries = []
    for i in range(DAYS_AHEAD):
        day = today + timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        print(f"Fetching earnings calendar for {date_str}...", file=sys.stderr)
        rows = fetch_day(date_str)
        for row in rows:
            symbol = row.get("symbol", "").upper()
            if symbol not in universe:
                continue
            all_entries.append(
                {
                    "date": date_str,
                    "ticker": symbol,
                    "company": row.get("name"),
                    "time": row.get("time"),  # e.g. "time-after-hours"
                    "eps_forecast": row.get("epsForecast"),
                    "last_year_eps": row.get("lastYearEPS"),
                    "market_cap": row.get("marketCap"),
                }
            )
        time.sleep(0.5)

    print(f"Found {len(all_entries)} in-universe earnings entries over next {DAYS_AHEAD} days", file=sys.stderr)
    with open("data/point3/earnings_calendar.json", "w", encoding="utf-8") as f:
        json.dump({"as_of": today.isoformat(), "entries": all_entries}, f, indent=2)
    print("Wrote data/point3/earnings_calendar.json", file=sys.stderr)


if __name__ == "__main__":
    main()

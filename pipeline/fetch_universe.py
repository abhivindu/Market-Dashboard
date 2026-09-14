"""Build equity universe: S&P 1500 (500+400+600) constituents w/ GICS sector,
via Wikipedia (free, no key). This approximates the >$2B mid+large-cap, some
small-cap NYSE/Nasdaq universe without needing a per-ticker market-cap scan
of the entire US market (see WISHLIST.md for full-market-scan upgrade path).
"""
import io
import json
import sys
import time

import pandas as pd
import requests
import yfinance as yf

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

WIKI_TABLES = {
    "SP500": ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 0, "Symbol", "GICS Sector", "Security"),
    "SP400": ("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", 0, "Symbol", "GICS Sector", "Security"),
    "SP600": ("https://en.wikipedia.org/wiki/List_of_S%26P_600_companies", 0, "Symbol", "GICS Sector", "Security"),
}


def fetch_constituents():
    rows = []
    for index_name, (url, table_idx, sym_col, sector_col, name_col) in WIKI_TABLES.items():
        print(f"Fetching {index_name} constituents from Wikipedia...", file=sys.stderr)
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        df = tables[table_idx]
        for _, r in df.iterrows():
            sym = str(r[sym_col]).replace(".", "-").strip()
            sector = str(r.get(sector_col, "Unknown"))
            name = str(r.get(name_col, sym))
            rows.append({"ticker": sym, "sector": sector, "name": name, "index": index_name})
    # de-dup (a ticker shouldn't be in 2 indices, but just in case)
    seen = {}
    for r in rows:
        seen[r["ticker"]] = r
    return list(seen.values())


def main():
    universe = fetch_constituents()
    print(f"Universe size: {len(universe)}", file=sys.stderr)
    out = {"universe": universe}
    with open("data/point3/universe.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Wrote data/point3/universe.json", file=sys.stderr)


if __name__ == "__main__":
    main()

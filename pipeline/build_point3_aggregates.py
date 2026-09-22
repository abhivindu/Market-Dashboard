"""Combine universe + market-cap cache + fresh price history into:
market-cap-weighted sector rollups, top movers ($2B+ cap filter), and
volume outliers, for the Point 3 dashboard.
"""
import json
import sys

MIN_MARKET_CAP = 2_000_000_000
TOP_N_MOVERS = 15


def main():
    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = json.load(f)["universe"]
    with open("data/point3/market_caps_cache.json", encoding="utf-8") as f:
        cap_cache = json.load(f)
    with open("data/point3/price_history.json", encoding="utf-8") as f:
        prices = json.load(f)

    market_caps = cap_cache["market_caps"]
    equity_meta = prices.get("_meta", {})
    print(f"Using market cap cache as of {cap_cache['as_of']}", file=sys.stderr)
    if equity_meta.get("stale"):
        print(
            f"  NOTE: equity price data as_of_date ({equity_meta.get('as_of_date')}) lags the "
            f"index data ({equity_meta.get('expected_date')}) - see fetch_price_history.py's "
            f"warning above.",
            file=sys.stderr,
        )

    merged = []
    for u in universe:
        ticker = u["ticker"]
        cap_row = market_caps.get(ticker)
        price_row = prices.get(ticker)
        if not cap_row or not price_row:
            continue
        cap = cap_row.get("market_cap")
        if cap is None or cap < MIN_MARKET_CAP:
            continue
        if price_row.get("day_chg_pct") is None:
            continue
        merged.append(
            {
                "ticker": ticker,
                "sector": u["sector"],
                "name": u.get("name", ticker),
                "price": price_row.get("price"),
                "day_chg_pct": price_row.get("day_chg_pct"),
                "five_day_chg_pct": price_row.get("five_day_chg_pct"),
                "market_cap": cap,
                "volume": price_row.get("volume"),
                "avg_volume": price_row.get("avg_volume"),
            }
        )

    print(f"Merged {len(merged)} names above ${MIN_MARKET_CAP/1e9:.0f}B cap", file=sys.stderr)

    # --- sector rollups: market-cap-weighted average day change ---
    sectors = {}
    for row in merged:
        s = sectors.setdefault(row["sector"], {"total_cap": 0.0, "weighted_sum": 0.0, "members": []})
        s["total_cap"] += row["market_cap"]
        s["weighted_sum"] += row["market_cap"] * row["day_chg_pct"]
        s["members"].append(row)

    sector_rollup = []
    for sector, s in sectors.items():
        wavg = s["weighted_sum"] / s["total_cap"] if s["total_cap"] else 0.0
        members_sorted = sorted(
            s["members"],
            key=lambda r: r["market_cap"] * r["day_chg_pct"],
            reverse=True,
        )
        for m in members_sorted:
            m["contribution_pct"] = round((m["market_cap"] / s["total_cap"]) * m["day_chg_pct"], 4)
        sector_rollup.append(
            {
                "sector": sector,
                "day_chg_pct_weighted": round(wavg, 3),
                "total_market_cap": s["total_cap"],
                "member_count": len(s["members"]),
                "members": members_sorted,
            }
        )
    sector_rollup.sort(key=lambda s: s["day_chg_pct_weighted"], reverse=True)

    # --- movers: top gainers / losers by day_chg_pct ---
    gainers = sorted(merged, key=lambda r: r["day_chg_pct"], reverse=True)[:TOP_N_MOVERS]
    losers = sorted(merged, key=lambda r: r["day_chg_pct"])[:TOP_N_MOVERS]

    # --- volume outliers (free-data proxy for "unusual activity") ---
    vol_outliers = [
        r for r in merged
        if r.get("volume") and r.get("avg_volume") and r["avg_volume"] > 0
        and r["volume"] / r["avg_volume"] >= 2.0
    ]
    for r in vol_outliers:
        r["volume_vs_avg_ratio"] = round(r["volume"] / r["avg_volume"], 2)
    vol_outliers.sort(key=lambda r: r["volume_vs_avg_ratio"], reverse=True)

    # --- bounce-candidate screen: down >15% in 5 days, still investment grade cap ---
    bounce_candidates = sorted(
        [r for r in merged if r.get("five_day_chg_pct") is not None and r["five_day_chg_pct"] <= -15],
        key=lambda r: r["five_day_chg_pct"],
    )

    # --- market breadth (advancers/decliners across the full filtered universe) ---
    advancers = sum(1 for r in merged if r["day_chg_pct"] > 0)
    decliners = sum(1 for r in merged if r["day_chg_pct"] < 0)
    unchanged = len(merged) - advancers - decliners
    breadth = {"advancers": advancers, "decliners": decliners, "unchanged": unchanged, "total": len(merged)}

    # --- flat ticker index: every filtered name, for drill-down lookups (index tiles, portfolio) ---
    ticker_index = {
        r["ticker"]: {
            "name": r["name"], "sector": r["sector"], "price": r["price"],
            "day_chg_pct": r["day_chg_pct"], "five_day_chg_pct": r.get("five_day_chg_pct"),
            "market_cap": r["market_cap"],
        }
        for r in merged
    }

    out = {
        "min_market_cap_filter": MIN_MARKET_CAP,
        "market_cap_cache_as_of": cap_cache["as_of"],
        "equity_data_as_of": equity_meta.get("as_of_date"),
        "equity_data_stale": equity_meta.get("stale", False),
        "equity_data_expected_date": equity_meta.get("expected_date"),
        "universe_count_after_filter": len(merged),
        "sector_rollup": sector_rollup,
        "top_gainers": gainers,
        "top_losers": losers,
        "volume_outliers": vol_outliers[:20],
        "bounce_candidates": bounce_candidates[:20],
        "breadth": breadth,
        "ticker_index": ticker_index,
    }
    with open("data/point3/aggregates.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Wrote data/point3/aggregates.json", file=sys.stderr)
    print(
        f"Sectors: {len(sector_rollup)}, gainers: {len(gainers)}, losers: {len(losers)}, "
        f"vol outliers: {len(vol_outliers)}, bounce candidates: {len(bounce_candidates)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

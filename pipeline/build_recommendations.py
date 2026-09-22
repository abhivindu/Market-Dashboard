"""Three-bucket daily recommendation screen, run after build_point3_aggregates.py.

Methodology (documented here since it's cited on every pick in the artifact):

1. BOUNCE (oversold, short-term): five_day_chg_pct <= -15% vs the name's own
   price - a sharp, recent drop. Top 5 most-oversold. Claude reviews each via
   news search before finalizing to screen out names down on genuine
   fundamental deterioration (fraud, guidance cut, etc.) rather than
   overreaction - that qualitative pass happens after this numeric shortlist,
   not in this script.

2. VALUE (fundamental discount) - the pct_off_52wk_high <= -25% (meaningfully
   discounted from its own highs) AND five_day_chg_pct > -10% (the drop isn't
   this week's acute shock - already digested, more likely a sustained
   re-rating than a bounce candidate) AND market-cap-top-half-of-sector proxy
   still does the first-pass screen across the full universe (real P/E at
   that scale is genuinely not free - Yahoo's .info endpoint is slow/rate-
   limit-prone for 1500 tickers, see WISHLIST.md). But per WISHLIST.md's own
   suggested fix, the TOP_N*3 most-discounted survivors of that screen (a
   small, safe shortlist) get real trailingPE/forwardPE via yfinance .info,
   and the final 5 are picked by lowest trailingPE among those with a valid,
   positive one (i.e. genuinely cheap on earnings, not just off its own
   high) - falling back to the discount-only ranking to fill any remaining
   slots if fewer than 5 names have usable PE data.

3. SPECULATIVE (momentum + attention): volume >= 2x its 3-month average AND
   day_chg_pct > 0 (buying pressure, not panic selling) - a free-data proxy
   for "unusual options activity" per WISHLIST.md. Top 5 by volume ratio.

All three buckets exclude tickers already claimed by an earlier bucket so
the 15 names are 15 distinct ideas, not overlapping angles on the same name.
"""
import json
import sys
import time

import yfinance as yf

TOP_N = 5
VALUE_SHORTLIST_SIZE = TOP_N * 3  # small, safe pool for real .info fundamentals calls


def fetch_pe(ticker):
    """Real trailingPE/forwardPE for one ticker via yfinance .info - only ever
    called on the small VALUE_SHORTLIST_SIZE pool, never the full universe."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
        }
    except Exception as e:
        print(f"  WARNING: .info fetch failed for {ticker}: {e}", file=sys.stderr)
        return {"trailing_pe": None, "forward_pe": None}


def main():
    with open("data/point3/aggregates.json", encoding="utf-8") as f:
        agg = json.load(f)
    with open("data/point3/price_history.json", encoding="utf-8") as f:
        prices = json.load(f)
    with open("data/point3/universe.json", encoding="utf-8") as f:
        universe = {u["ticker"]: u for u in json.load(f)["universe"]}
    with open("data/point3/market_caps_cache.json", encoding="utf-8") as f:
        market_caps = json.load(f)["market_caps"]

    claimed = set()

    # --- 1. Bounce ---
    bounce = agg["bounce_candidates"][:TOP_N]
    for r in bounce:
        claimed.add(r["ticker"])

    # --- 2. Value (52wk-discount proxy) ---
    # sector median market cap, to require "top half of sector by cap"
    sector_caps = {}
    for t, u in universe.items():
        cap_row = market_caps.get(t)
        if cap_row and cap_row.get("market_cap"):
            sector_caps.setdefault(u["sector"], []).append(cap_row["market_cap"])
    sector_median_cap = {s: sorted(caps)[len(caps) // 2] for s, caps in sector_caps.items() if caps}

    value_candidates = []
    for t, u in universe.items():
        if t in claimed:
            continue
        cap_row = market_caps.get(t)
        price_row = prices.get(t)
        if not cap_row or not price_row:
            continue
        cap = cap_row.get("market_cap")
        pct_off_high = price_row.get("pct_off_52wk_high")
        five_day = price_row.get("five_day_chg_pct")
        if cap is None or pct_off_high is None or five_day is None:
            continue
        if cap < 2_000_000_000:
            continue
        median_cap = sector_median_cap.get(u["sector"], 0)
        if cap < median_cap:
            continue  # top half of sector by cap only
        if pct_off_high <= -25 and five_day > -10:
            value_candidates.append(
                {
                    "ticker": t,
                    "name": u.get("name", t),
                    "sector": u["sector"],
                    "market_cap": cap,
                    "pct_off_52wk_high": pct_off_high,
                    "five_day_chg_pct": five_day,
                    "price": price_row.get("price"),
                }
            )
    value_candidates.sort(key=lambda r: r["pct_off_52wk_high"])
    shortlist = value_candidates[:VALUE_SHORTLIST_SIZE]
    print(f"Fetching real PE for {len(shortlist)} value-bucket shortlist candidates...", file=sys.stderr)
    for r in shortlist:
        pe = fetch_pe(r["ticker"])
        r["trailing_pe"] = pe["trailing_pe"]
        r["forward_pe"] = pe["forward_pe"]
        time.sleep(0.3)

    with_pe = sorted(
        (r for r in shortlist if r.get("trailing_pe") and r["trailing_pe"] > 0),
        key=lambda r: r["trailing_pe"],
    )
    value = with_pe[:TOP_N]
    if len(value) < TOP_N:
        # not enough names had usable PE data - fill remaining slots from the
        # discount-only ranking (still real, just not PE-confirmed for these)
        picked = {r["ticker"] for r in value}
        for r in shortlist:
            if len(value) >= TOP_N:
                break
            if r["ticker"] not in picked:
                value.append(r)
                picked.add(r["ticker"])
    for r in value:
        claimed.add(r["ticker"])

    # --- 3. Speculative (volume + momentum) ---
    spec_candidates = [
        r for r in agg["volume_outliers"]
        if r["ticker"] not in claimed and r["day_chg_pct"] > 0
    ]
    spec_candidates.sort(key=lambda r: r["volume_vs_avg_ratio"], reverse=True)
    speculative = spec_candidates[:TOP_N]
    for r in speculative:
        claimed.add(r["ticker"])

    out = {
        "methodology_note": "See pipeline/build_recommendations.py docstring for full criteria. Value bucket picks are ranked by real trailingPE (via yfinance .info) among a shortlist pre-screened by 52wk-discount, not the discount proxy alone.",
        "bounce": bounce,
        "value": value,
        "speculative": speculative,
    }
    with open("data/point3/recommendations_shortlist.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Bounce: {len(bounce)}, Value: {len(value)}, Speculative: {len(speculative)}", file=sys.stderr)
    print("Wrote data/point3/recommendations_shortlist.json", file=sys.stderr)
    print("NOTE: this is the numeric shortlist only - qualitative news review", file=sys.stderr)
    print("(driver, thesis, alignment verdict) still needed before publishing.", file=sys.stderr)


if __name__ == "__main__":
    main()

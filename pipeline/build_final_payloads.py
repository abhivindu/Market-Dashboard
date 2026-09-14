"""Assemble final Point 1 and Point 3 JSON payloads for the artifacts.
Merges mechanical/computed data (always present, guarantees every section has
a drill-down) with a hand-curated "content overrides" file holding real
news-researched narrative/citations for the highest-value items (macro
flags, top movers, recommendation picks) - see content_overrides.json.
Mechanical-only sections (sector member tables, earnings calendar, vol
aggregate) don't need overrides per the confirmed drill-down template.
"""
import json
import os


def load(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def main():
    overrides = load("data/content_overrides.json", {"macro_flags": {}, "movers": {}, "recommendations": {}})

    # ---------- POINT 1 ----------
    macro = load("data/point1/macro.json")
    materiality = load("data/point1/materiality_flags.json", {"flags": []})
    for flag in materiality["flags"]:
        key = f"{flag['type']}:{flag['series']}"
        ov = overrides["macro_flags"].get(key, {})
        flag["narrative"] = ov.get("narrative", "Research pending - mechanical flag only.")
        flag["citations"] = ov.get("citations", [])
        flag["reaction_assessment"] = ov.get("reaction_assessment", "not yet assessed")

    point1_payload = {
        "as_of": macro["as_of"],
        "macro_series": macro["series"],
        "vol_term_structure": macro.get("vol_term_structure", {}),
        "material_events": materiality["flags"],
    }
    with open("data/point1/final_payload.json", "w") as f:
        json.dump(point1_payload, f, indent=2)
    print(f"Point 1 payload: {len(materiality['flags'])} material events")

    # ---------- POINT 3 ----------
    indices = load("data/point3/indices.json")
    aggregates = load("data/point3/aggregates.json")
    earnings = load("data/point3/earnings_calendar.json")
    recs = load("data/point3/recommendations_shortlist.json")

    def enrich_mover(m, bucket):
        key = m["ticker"]
        ov = overrides["movers"].get(key, {})
        m["narrative"] = ov.get("narrative", "Research pending.")
        m["citations"] = ov.get("citations", [])
        m["verdict"] = ov.get("verdict", "not yet assessed")
        return m

    for m in aggregates.get("top_gainers", []):
        enrich_mover(m, "gainer")
    for m in aggregates.get("top_losers", []):
        enrich_mover(m, "loser")

    if recs:
        for bucket_name in ("bounce", "value", "speculative"):
            for r in recs.get(bucket_name, []):
                key = r["ticker"]
                ov = overrides["recommendations"].get(key, {})
                r["thesis"] = ov.get("thesis", "Research pending.")
                r["citations"] = ov.get("citations", [])
                r["verdict"] = ov.get("verdict", "not yet assessed")
                r["bucket"] = bucket_name

    macro_for_vol = load("data/point1/macro.json", {})

    point3_payload = {
        "as_of": indices["as_of"],
        "indices": indices["indices"],
        "sector_rollup": aggregates["sector_rollup"],
        "top_gainers": aggregates["top_gainers"],
        "top_losers": aggregates["top_losers"],
        "volume_outliers": aggregates["volume_outliers"],
        "breadth": aggregates.get("breadth", {}),
        "ticker_index": aggregates.get("ticker_index", {}),
        "vol_term_structure": macro_for_vol.get("vol_term_structure", {}),
        "earnings_calendar": earnings["entries"] if earnings else [],
        "recommendations": recs if recs else {"bounce": [], "value": [], "speculative": []},
        "min_market_cap_filter": aggregates["min_market_cap_filter"],
        "market_cap_cache_as_of": aggregates["market_cap_cache_as_of"],
    }
    with open("data/point3/final_payload.json", "w") as f:
        json.dump(point3_payload, f, indent=2)
    print(f"Point 3 payload: {len(aggregates['sector_rollup'])} sectors, "
          f"{len(aggregates['top_gainers'])} gainers, {len(aggregates['top_losers'])} losers")


if __name__ == "__main__":
    main()

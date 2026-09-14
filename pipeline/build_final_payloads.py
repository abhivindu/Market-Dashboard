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
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def diff_point1(previous, current_flags):
    """Compare this pull's material-event flags against the prior pull's
    (read from the final_payload.json that's about to be overwritten - it
    naturally holds "last pull's" state until this run replaces it).
    Returns a dict the template renders as a "since last pull" callout.
    """
    if previous is None:
        return {
            "has_previous": False,
            "previous_as_of": None,
            "newly_flagged": [],
            "resolved": [],
        }

    def key(e):
        return (e["type"], e["series"])

    prev_events = {key(e): e for e in previous.get("material_events", [])}
    current_keys = {key(e) for e in current_flags}

    newly_flagged = [e for e in current_flags if key(e) not in prev_events]
    resolved = [e for k, e in prev_events.items() if k not in current_keys]

    return {
        "has_previous": True,
        "previous_as_of": previous.get("as_of"),
        "newly_flagged": newly_flagged,
        "resolved": resolved,
    }


def build_since_last_pull_blurb(diff, override_blurb):
    """Mechanical fallback if no hand-authored override is set for this pull -
    keeps the callout meaningful even before I've done the research pass."""
    if override_blurb:
        return override_blurb
    if not diff["has_previous"]:
        return "First pull recorded - nothing to compare against yet."
    if not diff["newly_flagged"] and not diff["resolved"]:
        return "No new material events since the last pull - today's read is materially the same as last time."
    parts = []
    if diff["newly_flagged"]:
        parts.append("New: " + "; ".join(e["detail"] for e in diff["newly_flagged"]))
    if diff["resolved"]:
        parts.append("Faded below threshold: " + "; ".join(e["detail"] for e in diff["resolved"]))
    return " ".join(parts)


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

    previous_point1 = load("data/point1/final_payload.json")  # still holds last pull's data at this point
    diff = diff_point1(previous_point1, materiality["flags"])
    diff["blurb"] = build_since_last_pull_blurb(diff, overrides.get("point1_since_last_pull"))

    point1_payload = {
        "as_of": macro["as_of"],
        "synthesis": overrides.get("point1_synthesis", ""),
        "since_last_pull": diff,
        "macro_series": macro["series"],
        "vol_term_structure": macro.get("vol_term_structure", {}),
        "material_events": materiality["flags"],
    }
    with open("data/point1/final_payload.json", "w", encoding="utf-8") as f:
        json.dump(point1_payload, f, indent=2)
    print(f"Point 1 payload: {len(materiality['flags'])} material events "
          f"({len(diff['newly_flagged'])} new, {len(diff['resolved'])} resolved since last pull)")

    # ---------- POINT 3 ----------
    indices = load("data/point3/indices.json")
    aggregates = load("data/point3/aggregates.json")
    earnings = load("data/point3/earnings_calendar.json")
    recs = load("data/point3/recommendations_shortlist.json")

    def enrich_mover(m, bucket):
        key = m["ticker"]
        ov = overrides["movers"].get(key)
        if ov is None:
            # some tickers were researched under recommendations (thesis) rather than
            # movers (narrative) - same underlying research, different field name
            rec_ov = overrides["recommendations"].get(key)
            ov = {"narrative": rec_ov["thesis"], "citations": rec_ov["citations"], "verdict": rec_ov["verdict"]} if rec_ov else {}
        m["narrative"] = ov.get("narrative", "Research pending.")
        m["citations"] = ov.get("citations", [])
        m["verdict"] = ov.get("verdict", "not yet assessed")
        return m

    for m in aggregates.get("top_gainers", []):
        enrich_mover(m, "gainer")
    for m in aggregates.get("top_losers", []):
        enrich_mover(m, "loser")
    for m in aggregates.get("volume_outliers", []):
        enrich_mover(m, "volume_outlier")

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
    with open("data/point3/final_payload.json", "w", encoding="utf-8") as f:
        json.dump(point3_payload, f, indent=2)
    print(f"Point 3 payload: {len(aggregates['sector_rollup'])} sectors, "
          f"{len(aggregates['top_gainers'])} gainers, {len(aggregates['top_losers'])} losers")


if __name__ == "__main__":
    main()

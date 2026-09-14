"""Apply the Point 1 materiality filter (confirmed thresholds) to macro.json
+ indices.json, producing a flagged list. Narrative/citations/verdict get
attached afterward via news research (WebSearch), not automated here -
Python can compute "did X move enough to matter", not "why".

Thresholds:
- index: >1% intraday move, or >2% over the pull's lookback (5-day)
- 10yr yield: >10bps day change
- oil (WTI): >3% day change
- credit spreads: flagged if day_chg is large relative to typical daily moves
  (>3bps IG, >8bps HY - these series move in small increments normally)
- FOMC/Fed events: not detectable from price data - flagged manually when
  known (e.g. meeting week) since this is calendar knowledge, not a series.
"""
import json


def pct(a, b):
    return (a - b) / b * 100 if b else 0.0


def main():
    with open("data/point1/macro.json") as f:
        macro = json.load(f)
    with open("data/point3/indices.json") as f:
        indices = json.load(f)

    flags = []

    for name, idx in indices["indices"].items():
        if name == "VIX":
            continue  # VIX has no "material move" threshold - it IS the vol signal
        if abs(idx["day_chg_pct"]) > 1.0:
            flags.append(
                {
                    "type": "index_day_move",
                    "series": name,
                    "value": idx["day_chg_pct"],
                    "detail": f"{name} moved {idx['day_chg_pct']:+.2f}% intraday (threshold: >1%)",
                }
            )
        if abs(idx["five_day_chg_pct"]) > 2.0:
            flags.append(
                {
                    "type": "index_5day_move",
                    "series": name,
                    "value": idx["five_day_chg_pct"],
                    "detail": f"{name} moved {idx['five_day_chg_pct']:+.2f}% over 5 days (threshold: >2%)",
                }
            )

    series = macro["series"]
    if "DGS10" in series and abs(series["DGS10"]["day_chg"]) * 100 > 10:
        flags.append(
            {
                "type": "yield_move",
                "series": "DGS10",
                "value": series["DGS10"]["day_chg"],
                "detail": f"10yr yield moved {series['DGS10']['day_chg']*100:+.0f}bps day/day (threshold: >10bps)",
            }
        )

    if "DCOILWTICO" in series:
        oil = series["DCOILWTICO"]
        # approximate day_chg_pct since series stores absolute day_chg
        prev = oil["last_value"] - oil["day_chg"]
        chg_pct = pct(oil["last_value"], prev)
        if abs(chg_pct) > 3.0:
            flags.append(
                {
                    "type": "oil_move",
                    "series": "DCOILWTICO",
                    "value": chg_pct,
                    "detail": f"WTI crude moved {chg_pct:+.2f}% (threshold: >3%)",
                }
            )

    if "BAMLC0A0CM" in series and abs(series["BAMLC0A0CM"]["day_chg"]) * 100 > 3:
        flags.append(
            {
                "type": "credit_spread_move",
                "series": "BAMLC0A0CM (IG OAS)",
                "value": series["BAMLC0A0CM"]["day_chg"],
                "detail": f"IG credit spread moved {series['BAMLC0A0CM']['day_chg']*100:+.0f}bps (threshold: >3bps)",
            }
        )
    if "BAMLH0A0HYM2" in series and abs(series["BAMLH0A0HYM2"]["day_chg"]) * 100 > 8:
        flags.append(
            {
                "type": "credit_spread_move",
                "series": "BAMLH0A0HYM2 (HY OAS)",
                "value": series["BAMLH0A0HYM2"]["day_chg"],
                "detail": f"HY credit spread moved {series['BAMLH0A0HYM2']['day_chg']*100:+.0f}bps (threshold: >8bps)",
            }
        )

    with open("data/point1/materiality_flags.json", "w") as f:
        json.dump({"flags": flags}, f, indent=2)
    print(f"Flagged {len(flags)} material moves")
    for fl in flags:
        print(" -", fl["detail"])


if __name__ == "__main__":
    main()

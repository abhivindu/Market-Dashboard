"""Render the Point 1 (macro one-pager) artifact HTML from final_payload.json.
Pure templating - all data comes from the JSON, nothing hardcoded here.
"""
import json

from render_common import svg_sparkline


TEMPLATE = """<!doctype html>
<title>Market Signal</title>
<style>
:root{{
  --paper:#EFF1EE; --surface:#FFFFFF; --surface-2:#F7F8F5;
  --ink:#141A2B; --ink-soft:#535A6B; --ink-faint:#8991A3;
  --accent:#A9762F; --accent-soft:#F0E4CE;
  --positive:#1F7A5C; --positive-soft:#E3F0EA;
  --negative:#B3402F; --negative-soft:#F7E7E2;
  --line:rgba(20,26,43,0.13); --line-strong:rgba(20,26,43,0.24);
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    --paper:#0D111C; --surface:#161C2B; --surface-2:#11162280;
    --ink:#E9E6DC; --ink-soft:#AEB4C4; --ink-faint:#767D8E;
    --accent:#D9A14A; --accent-soft:#3A2E17;
    --positive:#4FB897; --positive-soft:#12271F;
    --negative:#E58176; --negative-soft:#2B1712;
    --line:rgba(233,230,220,0.14); --line-strong:rgba(233,230,220,0.26);
  }}
}}
:root[data-theme="dark"]{{
  --paper:#0D111C; --surface:#161C2B; --surface-2:#11162280;
  --ink:#E9E6DC; --ink-soft:#AEB4C4; --ink-faint:#767D8E;
  --accent:#D9A14A; --accent-soft:#3A2E17;
  --positive:#4FB897; --positive-soft:#12271F;
  --negative:#E58176; --negative-soft:#2B1712;
  --line:rgba(233,230,220,0.14); --line-strong:rgba(233,230,220,0.26);
}}
*{{box-sizing:border-box;}}
body{{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:'Public Sans',system-ui,-apple-system,sans-serif;
  padding:0 20px; padding-block:32px;
}}
.wrap{{max-width:840px; margin:0 auto;}}
h1,h2,h3{{font-family:'Fraunces',Georgia,serif; text-wrap:balance; margin:0;}}
.mono{{font-family:'IBM Plex Mono',ui-monospace,monospace; font-variant-numeric:tabular-nums;}}
.masthead{{display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:8px 24px; padding-bottom:18px; margin-bottom:24px; position:relative;}}
.masthead::after{{content:""; position:absolute; left:0; right:0; bottom:0; height:3px; background:linear-gradient(90deg, var(--ink) 0%, var(--ink) 60%, var(--accent) 100%);}}
.masthead h1{{font-size:2.15rem; font-weight:600; letter-spacing:-0.015em;}}
.masthead .meta{{color:var(--ink-faint); font-size:0.78rem; text-align:right; line-height:1.5;}}
.eyebrow{{text-transform:uppercase; letter-spacing:0.09em; font-size:0.72rem; color:var(--accent); font-weight:600; margin-bottom:6px;}}
.rates-strip{{display:grid; grid-template-columns:repeat(auto-fit,minmax(122px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:12px; overflow:hidden; margin-bottom:32px; box-shadow:0 1px 2px rgba(20,26,43,0.04);}}
.rate-cell{{background:var(--surface); padding:13px 15px 11px;}}
.rate-cell .label{{font-size:0.66rem; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:5px;}}
.rate-cell .value-row{{display:flex; align-items:flex-end; justify-content:space-between; gap:8px;}}
.rate-cell .value{{font-size:1.2rem; font-weight:600; letter-spacing:-0.01em;}}
.rate-cell .chg{{font-size:0.74rem; margin-top:3px;}}
.up{{color:var(--positive);}} .down{{color:var(--negative);}}
section{{margin-bottom:34px;}}
.section-title{{font-size:1.1rem; font-weight:600; margin-bottom:5px; letter-spacing:-0.005em;}}
.section-sub{{color:var(--ink-soft); font-size:0.85rem; margin-bottom:18px; max-width:62ch; line-height:1.5;}}
.event{{border:1px solid var(--line); border-radius:12px; background:var(--surface); margin-bottom:10px; overflow:hidden; transition:border-color 0.15s ease, box-shadow 0.15s ease;}}
.event:hover{{border-color:var(--line-strong); box-shadow:0 2px 8px rgba(20,26,43,0.06);}}
.event-head{{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:15px 18px; cursor:pointer; user-select:none;}}
.event-head:hover{{background:var(--surface-2);}}
.event-head .headline{{font-size:0.96rem; font-weight:500; flex:1;}}
.event-head .metric{{font-size:0.95rem; font-weight:600; white-space:nowrap;}}
.chevron{{color:var(--ink-faint); transition:transform 0.18s ease; flex-shrink:0;}}
.event[open] .chevron{{transform:rotate(90deg);}}
.event-body{{padding:0 18px 18px; border-top:1px solid var(--line);}}
.event-body p{{font-size:0.9rem; line-height:1.55; color:var(--ink-soft); margin:14px 0 10px;}}
.assessment{{display:inline-block; font-size:0.72rem; padding:3px 10px; border-radius:999px; background:var(--accent-soft); color:var(--accent); font-weight:600; margin-bottom:10px;}}
.citations{{display:flex; flex-direction:column; gap:6px; margin-top:10px;}}
.citations a{{color:var(--ink); font-size:0.82rem; text-decoration:none; border-bottom:1px solid var(--line-strong);}}
.citations a:hover{{color:var(--accent); border-color:var(--accent);}}
summary::-webkit-details-marker{{display:none;}}
.vol-badge{{display:flex; align-items:center; gap:14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); padding:16px 18px;}}
.vol-badge .tag{{font-size:0.72rem; padding:4px 12px; border-radius:999px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;}}
.tag.calm{{background:var(--positive-soft); color:var(--positive);}}
.tag.stress{{background:var(--negative-soft); color:var(--negative);}}
.vol-nums{{display:flex; gap:20px; margin-left:auto;}}
.vol-nums div{{text-align:right;}}
.vol-nums .l{{font-size:0.68rem; color:var(--ink-faint); text-transform:uppercase;}}
.vol-nums .v{{font-size:1rem; font-weight:600;}}
footer{{color:var(--ink-faint); font-size:0.75rem; border-top:1px solid var(--line); padding-top:16px; margin-top:8px;}}
@media (max-width:480px){{ .masthead{{flex-direction:column;}} .masthead .meta{{text-align:left;}} }}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="wrap">
  <div class="masthead">
    <h1>Market Signal</h1>
    <div class="meta">Macro &amp; rates one-pager<br>As of {as_of_display}</div>
  </div>

  <div class="rates-strip">
    {rate_cells}
  </div>

  <section>
    <div class="section-title">Material events</div>
    <div class="section-sub">Filtered to moves that cleared threshold — index &gt;1% intraday / &gt;2% over 5 days, 10yr yield &gt;10bps, oil &gt;3%, credit spreads &gt;3bps (IG) / &gt;8bps (HY), or a live Fed/FOMC event. Click any event for driver, sources, and whether the reaction looks proportionate.</div>
    {events_html}
  </section>

  <section>
    <div class="section-title">Volatility term structure</div>
    <div class="section-sub">VIX vs. its 3-month forward (VIX3M) — contango means calm markets, backwardation means near-term fear is priced above longer-term fear.</div>
    <div class="vol-badge">
      <span class="tag {vol_tag_class}">{vol_structure}</span>
      <div class="vol-nums">
        <div><div class="l">VIX</div><div class="v mono">{vix_val}</div></div>
        <div><div class="l">VIX3M</div><div class="v mono">{vix3m_val}</div></div>
        <div><div class="l">Spread</div><div class="v mono">{vix_spread}</div></div>
      </div>
    </div>
  </section>

  <footer>
    Data: FRED (yields, credit spreads, oil, dollar index), CBOE via Yahoo Finance (VIX term structure). Free/unauthenticated sources — see WISHLIST.md for planned upgrades. Generated by pipeline/render_point1_html.py.
  </footer>
</div>
"""

EVENT_TEMPLATE = """
<details class="event">
  <summary class="event-head">
    <span class="headline">{detail}</span>
    <span class="metric mono {metric_class}">{metric_display}</span>
    <span class="chevron">&#9656;</span>
  </summary>
  <div class="event-body">
    <span class="assessment">{reaction_assessment}</span>
    <p>{narrative}</p>
    <div class="citations">{citation_links}</div>
  </div>
</details>
"""


def fmt_pct(v):
    return f"{v:+.2f}%"


def fmt_bps(v):
    return f"{v*100:+.0f}bps"


def rate_cell(label, value, unit, chg=None, chg_unit="", history=None):
    chg_html = ""
    if chg is not None:
        cls = "up" if chg > 0 else ("down" if chg < 0 else "")
        chg_html = f'<div class="chg mono {cls}">{chg:+.2f}{chg_unit} 1d</div>'
    spark = ""
    if history:
        vals = [h["value"] for h in history[-30:]]
        cls = "up" if (chg or 0) >= 0 else "down"
        color = "var(--positive)" if cls == "up" else "var(--negative)"
        spark = svg_sparkline(vals, width=52, height=22, color=color)
    return f"""<div class="rate-cell">
      <div class="label">{label}</div>
      <div class="value-row">
        <div class="value mono">{value}{unit}</div>
        {spark}
      </div>
      {chg_html}
    </div>"""


def render_event(flag):
    if "index" in flag["type"]:
        metric_display = fmt_pct(flag["value"])
        metric_class = "up" if flag["value"] > 0 else "down"
    elif flag["type"] in ("yield_move", "credit_spread_move"):
        metric_display = fmt_bps(flag["value"])
        metric_class = "up" if flag["value"] > 0 else "down"
    else:
        metric_display = fmt_pct(flag["value"])
        metric_class = "up" if flag["value"] > 0 else "down"

    citation_links = "\n".join(
        f'<a href="{c["url"]}" target="_blank" rel="noopener">{c["title"]}</a>'
        for c in flag.get("citations", [])
    ) or '<span style="color:var(--ink-faint); font-size:0.82rem;">No sources attached yet.</span>'

    return EVENT_TEMPLATE.format(
        detail=flag["detail"],
        metric_display=metric_display,
        metric_class=metric_class,
        reaction_assessment=flag.get("reaction_assessment", "not yet assessed"),
        narrative=flag.get("narrative", "Research pending."),
        citation_links=citation_links,
    )


def main():
    with open("data/point1/final_payload.json") as f:
        payload = json.load(f)

    series = payload["macro_series"]
    as_of = payload["as_of"][:16].replace("T", " ") + " UTC"

    cells = [
        rate_cell("10Y Yield", series["DGS10"]["last_value"], "%", series["DGS10"]["day_chg"], "pp", series["DGS10"]["history"]),
        rate_cell("2Y Yield", series["DGS2"]["last_value"], "%", series["DGS2"]["day_chg"], "pp", series["DGS2"]["history"]),
        rate_cell("3M Yield", series["DGS3MO"]["last_value"], "%", series["DGS3MO"]["day_chg"], "pp", series["DGS3MO"]["history"]),
        rate_cell("10Y-2Y Spread", series["T10Y2Y"]["last_value"], "pp", series["T10Y2Y"]["day_chg"], "pp", series["T10Y2Y"]["history"]),
        rate_cell("IG Credit OAS", series["BAMLC0A0CM"]["last_value"], "pp", series["BAMLC0A0CM"]["day_chg"], "pp", series["BAMLC0A0CM"]["history"]),
        rate_cell("HY Credit OAS", series["BAMLH0A0HYM2"]["last_value"], "pp", series["BAMLH0A0HYM2"]["day_chg"], "pp", series["BAMLH0A0HYM2"]["history"]),
        rate_cell("WTI Crude", series["DCOILWTICO"]["last_value"], "", series["DCOILWTICO"]["day_chg"], "", series["DCOILWTICO"]["history"]),
        rate_cell("USD Index", series["DTWEXBGS"]["last_value"], "", series["DTWEXBGS"]["day_chg"], "", series["DTWEXBGS"]["history"]),
    ]

    events = payload["material_events"]
    events_html = "\n".join(render_event(e) for e in events) if events else '<div class="section-sub">No material moves cleared threshold on this pull.</div>'

    vol = payload.get("vol_term_structure", {})
    vol_structure = vol.get("structure", "n/a")
    vol_tag_class = "stress" if "backwardation" in vol_structure else "calm"

    html = TEMPLATE.format(
        as_of_display=as_of,
        rate_cells="\n".join(cells),
        events_html=events_html,
        vol_structure=vol_structure,
        vol_tag_class=vol_tag_class,
        vix_val=vol.get("VIX", {}).get("last_value", "n/a"),
        vix3m_val=vol.get("VIX3M", {}).get("last_value", "n/a"),
        vix_spread=vol.get("vix_minus_vix3m", "n/a"),
    )

    with open("artifacts/point1.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote artifacts/point1.html")


if __name__ == "__main__":
    main()

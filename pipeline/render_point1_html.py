"""Render the Point 1 (macro one-pager) artifact HTML from final_payload.json.
Pure templating - all data comes from the JSON, nothing hardcoded here.

Layout: masthead -> lede synthesis paragraph -> three labeled stat clusters
(Benchmark Rates, Spreads, Commodities & FX) -> volatility read -> material
events -> footer. The lede is the thing that makes this read as a "concise report"
rather than a stat dump - it's the one piece of hand-authored narrative per
pull, carried in content_overrides.json under "point1_synthesis".
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
  padding:0 20px; padding-block:36px;
}}
.wrap{{max-width:800px; margin:0 auto;}}
h1,h2,h3{{font-family:'Fraunces',Georgia,serif; text-wrap:balance; margin:0;}}
.mono{{font-family:'IBM Plex Mono',ui-monospace,monospace; font-variant-numeric:tabular-nums;}}

.masthead{{display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:8px 24px; padding-bottom:16px; margin-bottom:22px; position:relative;}}
.masthead::after{{content:""; position:absolute; left:0; right:0; bottom:0; height:3px; background:linear-gradient(90deg, var(--ink) 0%, var(--ink) 55%, var(--accent) 100%);}}
.masthead-left{{display:flex; align-items:baseline; gap:12px;}}
.masthead h1{{font-size:2.1rem; font-weight:600; letter-spacing:-0.015em;}}
.masthead .kicker{{font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--accent); font-weight:600;}}
.masthead .meta{{color:var(--ink-faint); font-size:0.78rem; text-align:right; line-height:1.5;}}

.lede{{font-family:'Fraunces',Georgia,serif; font-size:1.15rem; font-weight:400; line-height:1.62; color:var(--ink); margin:0 0 36px; max-width:66ch;}}
.lede strong{{font-weight:600;}}

.since-pull{{border-left:3px solid var(--accent); background:var(--accent-soft); border-radius:0 10px 10px 0; padding:12px 16px; margin-bottom:24px; max-width:66ch;}}
.since-pull.quiet{{border-left-color:var(--line-strong); background:var(--surface-2);}}
.since-pull .eyebrow{{margin-bottom:5px; display:block;}}
.since-pull.quiet .eyebrow{{color:var(--ink-faint);}}
.since-pull p{{font-size:0.88rem; line-height:1.55; color:var(--ink-soft); margin:0;}}
.since-pull .prev-date{{color:var(--ink-faint); font-size:0.74rem; margin-top:6px;}}

.cluster-row{{display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; margin-bottom:32px; align-items:start;}}
@media (max-width:680px){{ .cluster-row{{grid-template-columns:1fr;}} }}
.cluster{{border:1px solid var(--line); border-radius:12px; background:var(--surface); overflow:hidden; box-shadow:0 1px 2px rgba(20,26,43,0.04);}}
.cluster-head{{font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-faint); font-weight:600; padding:11px 15px 9px; border-bottom:1px solid var(--line);}}
.rate-row{{display:flex; align-items:center; justify-content:space-between; gap:10px; padding:10px 15px; border-bottom:1px solid var(--line); cursor:pointer; transition:background 0.12s ease;}}
.rate-row:hover{{background:var(--surface-2);}}
.rate-row:last-child{{border-bottom:none;}}
.rate-row .rlabel{{font-size:0.78rem; color:var(--ink-soft); flex-shrink:0;}}
.rate-row .rspark{{flex-shrink:0;}}
.rate-row .rval-wrap{{text-align:right; flex-shrink:0;}}
.rate-row .value{{font-size:0.98rem; font-weight:600; letter-spacing:-0.005em;}}
.rate-row .chg{{font-size:0.7rem; margin-top:1px;}}
.up{{color:var(--positive);}} .down{{color:var(--negative);}}

section{{margin-bottom:32px;}}
.section-title{{font-size:1.08rem; font-weight:600; margin-bottom:5px; letter-spacing:-0.005em;}}
.section-sub{{color:var(--ink-soft); font-size:0.85rem; margin-bottom:16px; max-width:62ch; line-height:1.5;}}

.event{{border:1px solid var(--line); border-radius:12px; background:var(--surface); margin-bottom:10px; overflow:hidden; transition:border-color 0.15s ease, box-shadow 0.15s ease;}}
.event:hover{{border-color:var(--line-strong); box-shadow:0 2px 8px rgba(20,26,43,0.06);}}
.event-head{{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:14px 18px; cursor:pointer; user-select:none;}}
.event-head:hover{{background:var(--surface-2);}}
.event-head .headline{{font-size:0.94rem; font-weight:500; flex:1;}}
.event-head .metric{{font-size:0.92rem; font-weight:600; white-space:nowrap;}}
.chevron{{color:var(--ink-faint); transition:transform 0.18s ease; flex-shrink:0;}}
.event[open] .chevron{{transform:rotate(90deg);}}
.event-body{{padding:0 18px 18px; border-top:1px solid var(--line);}}
.event-body p{{font-size:0.88rem; line-height:1.55; color:var(--ink-soft); margin:14px 0 10px;}}
.assessment{{display:inline-block; font-size:0.7rem; padding:3px 10px; border-radius:999px; background:var(--accent-soft); color:var(--accent); font-weight:600; margin-bottom:10px; margin-top:12px;}}
.citations{{display:flex; flex-direction:column; gap:6px; margin-top:10px;}}
.citations .cite-row{{display:flex; align-items:baseline; gap:8px; flex-wrap:wrap;}}
.citations a{{color:var(--ink); font-size:0.8rem; text-decoration:none; border-bottom:1px solid var(--line-strong); width:fit-content;}}
.citations a:hover{{color:var(--accent); border-color:var(--accent);}}
.citations .cite-date{{font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:var(--ink-faint);}}
summary::-webkit-details-marker{{display:none;}}
summary{{list-style:none;}}
summary::marker{{content:"";}}

.vol-badge{{display:flex; align-items:center; gap:14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); padding:15px 18px; flex-wrap:wrap; box-shadow:0 1px 2px rgba(20,26,43,0.04);}}
.vol-badge .tag{{font-size:0.7rem; padding:4px 12px; border-radius:999px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;}}
.tag.calm{{background:var(--positive-soft); color:var(--positive);}}
.tag.stress{{background:var(--negative-soft); color:var(--negative);}}
.vol-nums{{display:flex; gap:22px; margin-left:auto;}}
.vol-nums div{{text-align:right;}}
.vol-nums .l{{font-size:0.66rem; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.04em;}}
.vol-nums .v{{font-size:0.98rem; font-weight:600; margin-top:2px;}}

footer{{color:var(--ink-faint); font-size:0.74rem; border-top:1px solid var(--line); padding-top:16px; margin-top:6px; line-height:1.6;}}
@media (max-width:480px){{ .masthead{{flex-direction:column;}} .masthead .meta{{text-align:left;}} }}

.chart-overlay{{position:fixed; inset:0; background:rgba(10,12,20,0.5); display:flex; align-items:center; justify-content:center; padding:20px; z-index:100;}}
.chart-overlay[hidden]{{display:none;}}
.chart-modal{{background:var(--surface); border-radius:14px; border:1px solid var(--line-strong); width:100%; max-width:620px; padding:20px 22px 16px; box-shadow:0 12px 40px rgba(10,12,20,0.25);}}
.chart-modal-head{{display:flex; justify-content:space-between; align-items:baseline; margin-bottom:14px;}}
.chart-modal-head h3{{font-size:1.05rem; font-weight:600;}}
.chart-modal-close{{background:none; border:none; font:inherit; font-size:0.85rem; color:var(--ink-faint); cursor:pointer; padding:4px 8px;}}
.chart-modal-close:hover{{color:var(--ink);}}
.chart-canvas-wrap{{position:relative; height:260px;}}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="wrap">
  <div class="masthead">
    <div class="masthead-left">
      <h1>Market Signal</h1>
    </div>
    <div class="meta">{event_count} material event{event_plural} flagged<br>As of {as_of_display}</div>
  </div>

  <div class="since-pull{since_pull_quiet_class}">
    <span class="eyebrow">Since last pull</span>
    <p>{since_pull_blurb}</p>
    {since_pull_prev_date}
  </div>

  <p class="lede">{synthesis}</p>

  <div class="cluster-row">
    <div class="cluster">
      <div class="cluster-head">Benchmark rates</div>
      {rate_rows}
    </div>
    <div class="cluster">
      <div class="cluster-head">Spreads</div>
      {spread_rows}
    </div>
    <div class="cluster">
      <div class="cluster-head">Commodities &amp; FX</div>
      {commodity_rows}
    </div>
  </div>

  <section>
    <div class="section-title">Volatility term structure</div>
    <div class="section-sub">VIX vs. its 3-month forward (VIX3M) &mdash; contango means calm markets, backwardation means near-term fear is priced above longer-term fear.</div>
    <div class="vol-badge">
      <span class="tag {vol_tag_class}">{vol_structure}</span>
      <div class="vol-nums">
        <div><div class="l">VIX</div><div class="v mono">{vix_val}</div></div>
        <div><div class="l">VIX3M</div><div class="v mono">{vix3m_val}</div></div>
        <div><div class="l">Spread</div><div class="v mono">{vix_spread}</div></div>
      </div>
    </div>
  </section>

  <section>
    <div class="section-title">Material events</div>
    <div class="section-sub">Filtered to moves that cleared threshold &mdash; index &gt;1% intraday / &gt;2% over 5 days, 10yr yield &gt;10bps, oil &gt;3%, credit spreads &gt;3bps (IG) / &gt;8bps (HY), or a live Fed/FOMC event. Click any event for driver, sources, and whether the reaction looks proportionate.</div>
    {events_html}
  </section>

  <footer>
    Data: FRED (yields, credit spreads, oil, dollar index), CBOE via Yahoo Finance (VIX term structure). Free/unauthenticated sources &mdash; see WISHLIST.md for planned upgrades. Generated by pipeline/render_point1_html.py.
  </footer>
</div>

<div class="chart-overlay" id="chart-overlay" hidden>
  <div class="chart-modal">
    <div class="chart-modal-head">
      <h3 id="chart-modal-title">Series</h3>
      <button class="chart-modal-close" id="chart-modal-close">Close &times;</button>
    </div>
    <div class="chart-canvas-wrap"><canvas id="chart-canvas"></canvas></div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<script>
const CHART_SERIES = {chart_series_json};
let activeChart = null;

function cssVar(name) {{
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}}

function openChart(key) {{
  const s = CHART_SERIES[key];
  if (!s) return;
  document.getElementById('chart-modal-title').textContent = s.label;
  document.getElementById('chart-overlay').hidden = false;
  const ctx = document.getElementById('chart-canvas').getContext('2d');
  const ink = cssVar('--ink'), inkFaint = cssVar('--ink-faint'), line = cssVar('--line'), accent = cssVar('--accent');
  if (activeChart) activeChart.destroy();
  activeChart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: s.history.map(h => h.date),
      datasets: [{{
        label: s.label,
        data: s.history.map(h => h.value),
        borderColor: accent,
        backgroundColor: accent + '22',
        fill: true,
        tension: 0.15,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => `${{s.label}}: ${{ctx.parsed.y}}${{s.unit || ''}}`
          }}
        }}
      }},
      scales: {{
        x: {{ ticks: {{ color: inkFaint, maxTicksLimit: 8 }}, grid: {{ color: line }} }},
        y: {{ ticks: {{ color: inkFaint, callback: (v) => v + (s.unit || '') }}, grid: {{ color: line }} }}
      }}
    }}
  }});
}}

document.querySelectorAll('[data-series]').forEach(el => {{
  el.addEventListener('click', () => openChart(el.dataset.series));
}});
document.getElementById('chart-modal-close').addEventListener('click', () => {{
  document.getElementById('chart-overlay').hidden = true;
}});
document.getElementById('chart-overlay').addEventListener('click', (e) => {{
  if (e.target.id === 'chart-overlay') document.getElementById('chart-overlay').hidden = true;
}});
</script>
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


def rate_row(label, value, unit, chg=None, chg_unit="", history=None):
    chg_html = ""
    if chg is not None:
        cls = "up" if chg > 0 else ("down" if chg < 0 else "")
        chg_html = f'<div class="chg mono {cls}">{chg:+.2f}{chg_unit} 1d</div>'
    spark = ""
    if history:
        vals = [h["value"] for h in history[-30:]]
        cls = "up" if (chg or 0) >= 0 else "down"
        color = "var(--positive)" if cls == "up" else "var(--negative)"
        spark = f'<span class="rspark">{svg_sparkline(vals, width=44, height=20, color=color)}</span>'
    return f"""<div class="rate-row" data-series="{label}">
      <span class="rlabel">{label}</span>
      {spark}
      <span class="rval-wrap">
        <div class="value mono">{value}{unit}</div>
        {chg_html}
      </span>
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
        f'<div class="cite-row"><a href="{c["url"]}" target="_blank" rel="noopener">{c["title"]}</a>'
        f'<span class="cite-date">{c.get("date", "n/d")}</span></div>'
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
    with open("data/point1/final_payload.json", encoding="utf-8") as f:
        payload = json.load(f)

    series = payload["macro_series"]
    as_of = payload["as_of"][:16].replace("T", " ") + " UTC"

    rate_rows = "\n".join([
        rate_row("3M", series["DGS3MO"]["last_value"], "%", series["DGS3MO"]["day_chg"], "pp", series["DGS3MO"]["history"]),
        rate_row("2Y", series["DGS2"]["last_value"], "%", series["DGS2"]["day_chg"], "pp", series["DGS2"]["history"]),
        rate_row("10Y", series["DGS10"]["last_value"], "%", series["DGS10"]["day_chg"], "pp", series["DGS10"]["history"]),
        rate_row("30Y", series["DGS30"]["last_value"], "%", series["DGS30"]["day_chg"], "pp", series["DGS30"]["history"]),
        rate_row("Fed Funds", series["DFF"]["last_value"], "%", series["DFF"]["day_chg"], "pp", series["DFF"]["history"]),
        rate_row("SOFR", series["SOFR"]["last_value"], "%", series["SOFR"]["day_chg"], "pp", series["SOFR"]["history"]),
    ])
    spread_rows = "\n".join([
        rate_row("10Y-2Y", series["T10Y2Y"]["last_value"], "pp", series["T10Y2Y"]["day_chg"], "pp", series["T10Y2Y"]["history"]),
        rate_row("10Y-3M", series["T10Y3M"]["last_value"], "pp", series["T10Y3M"]["day_chg"], "pp", series["T10Y3M"]["history"]),
        rate_row("IG OAS", series["BAMLC0A0CM"]["last_value"], "pp", series["BAMLC0A0CM"]["day_chg"], "pp", series["BAMLC0A0CM"]["history"]),
        rate_row("BBB OAS", series["BAMLC0A4CBBB"]["last_value"], "pp", series["BAMLC0A4CBBB"]["day_chg"], "pp", series["BAMLC0A4CBBB"]["history"]),
        rate_row("HY OAS", series["BAMLH0A0HYM2"]["last_value"], "pp", series["BAMLH0A0HYM2"]["day_chg"], "pp", series["BAMLH0A0HYM2"]["history"]),
    ])
    commodity_rows = "\n".join([
        rate_row("WTI Crude", series["DCOILWTICO"]["last_value"], "", series["DCOILWTICO"]["day_chg"], "", series["DCOILWTICO"]["history"]),
        rate_row("Gold", series["GOLD"]["last_value"], "", series["GOLD"]["day_chg"], "", series["GOLD"]["history"]),
        rate_row("Silver", series["SILVER"]["last_value"], "", series["SILVER"]["day_chg"], "", series["SILVER"]["history"]),
        rate_row("USD Index", series["DTWEXBGS"]["last_value"], "", series["DTWEXBGS"]["day_chg"], "", series["DTWEXBGS"]["history"]),
    ])

    chart_series = {
        "3M": {"label": series["DGS3MO"]["label"], "unit": "%", "history": series["DGS3MO"]["history"]},
        "2Y": {"label": series["DGS2"]["label"], "unit": "%", "history": series["DGS2"]["history"]},
        "10Y": {"label": series["DGS10"]["label"], "unit": "%", "history": series["DGS10"]["history"]},
        "30Y": {"label": series["DGS30"]["label"], "unit": "%", "history": series["DGS30"]["history"]},
        "Fed Funds": {"label": series["DFF"]["label"], "unit": "%", "history": series["DFF"]["history"]},
        "SOFR": {"label": series["SOFR"]["label"], "unit": "%", "history": series["SOFR"]["history"]},
        "10Y-2Y": {"label": series["T10Y2Y"]["label"], "unit": "pp", "history": series["T10Y2Y"]["history"]},
        "10Y-3M": {"label": series["T10Y3M"]["label"], "unit": "pp", "history": series["T10Y3M"]["history"]},
        "IG OAS": {"label": series["BAMLC0A0CM"]["label"], "unit": "pp", "history": series["BAMLC0A0CM"]["history"]},
        "BBB OAS": {"label": series["BAMLC0A4CBBB"]["label"], "unit": "pp", "history": series["BAMLC0A4CBBB"]["history"]},
        "HY OAS": {"label": series["BAMLH0A0HYM2"]["label"], "unit": "pp", "history": series["BAMLH0A0HYM2"]["history"]},
        "WTI Crude": {"label": series["DCOILWTICO"]["label"], "unit": "$", "history": series["DCOILWTICO"]["history"]},
        "Gold": {"label": series["GOLD"]["label"], "unit": "$", "history": series["GOLD"]["history"]},
        "Silver": {"label": series["SILVER"]["label"], "unit": "$", "history": series["SILVER"]["history"]},
        "USD Index": {"label": series["DTWEXBGS"]["label"], "unit": "", "history": series["DTWEXBGS"]["history"]},
    }

    events = payload["material_events"]
    events_html = "\n".join(render_event(e) for e in events) if events else '<div class="section-sub">No material moves cleared threshold on this pull.</div>'

    vol = payload.get("vol_term_structure", {})
    vol_structure = vol.get("structure", "n/a")
    vol_tag_class = "stress" if "backwardation" in vol_structure else "calm"

    n_events = len(events)

    since_pull = payload.get("since_last_pull", {"has_previous": False, "newly_flagged": [], "resolved": [], "blurb": ""})
    is_quiet = since_pull["has_previous"] and not since_pull["newly_flagged"] and not since_pull["resolved"]
    since_pull_prev_date = ""
    if since_pull.get("previous_as_of"):
        prev_display = since_pull["previous_as_of"][:16].replace("T", " ") + " UTC"
        since_pull_prev_date = f'<div class="prev-date">Previous pull: {prev_display}</div>'

    html = TEMPLATE.format(
        as_of_display=as_of,
        synthesis=payload.get("synthesis") or "No synthesis available for this pull.",
        since_pull_quiet_class=" quiet" if is_quiet else "",
        since_pull_blurb=since_pull.get("blurb") or "No prior pull on record.",
        since_pull_prev_date=since_pull_prev_date,
        event_count=n_events,
        event_plural="" if n_events == 1 else "s",
        rate_rows=rate_rows,
        spread_rows=spread_rows,
        commodity_rows=commodity_rows,
        events_html=events_html,
        vol_structure=vol_structure,
        vol_tag_class=vol_tag_class,
        vix_val=vol.get("VIX", {}).get("last_value", "n/a"),
        vix3m_val=vol.get("VIX3M", {}).get("last_value", "n/a"),
        vix_spread=vol.get("vix_minus_vix3m", "n/a"),
        chart_series_json=json.dumps(chart_series),
    )

    with open("artifacts/point1.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote artifacts/point1.html")


if __name__ == "__main__":
    main()

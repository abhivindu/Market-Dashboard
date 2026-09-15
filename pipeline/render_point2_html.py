"""Render the Point 2 (frontier tech trend monitor) artifact HTML from
data/point2/sectors.json. One card per sector (native <details> expand,
matching Point 1's material-event pattern) with a full drilldown: how the
tech works, maturity, applications, investors, roadblocks, sentiment, then
primary and adjacent company profiles with investors/performance/citations.
"""
import json

from render_common import svg_sparkline  # noqa: F401 (kept for parity with other renderers; unused here)


TEMPLATE = """<!doctype html>
<title>Frontier Watch</title>
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
body{{margin:0; background:var(--paper); color:var(--ink); font-family:'Public Sans',system-ui,-apple-system,sans-serif; padding:0 20px; padding-block:36px;}}
.wrap{{max-width:920px; margin:0 auto;}}
h1,h2,h3{{font-family:'Fraunces',Georgia,serif; text-wrap:balance; margin:0;}}
.mono{{font-family:'IBM Plex Mono',ui-monospace,monospace; font-variant-numeric:tabular-nums;}}

.masthead{{display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:8px 24px; padding-bottom:16px; margin-bottom:22px; position:relative;}}
.masthead::after{{content:""; position:absolute; left:0; right:0; bottom:0; height:3px; background:linear-gradient(90deg, var(--ink) 0%, var(--ink) 55%, var(--accent) 100%);}}
.masthead h1{{font-size:2.1rem; font-weight:600; letter-spacing:-0.015em;}}
.masthead .meta{{color:var(--ink-faint); font-size:0.78rem; text-align:right; line-height:1.5;}}

.radar{{border-left:3px solid var(--accent); background:var(--accent-soft); border-radius:0 10px 10px 0; padding:12px 16px; margin-bottom:28px;}}
.radar.quiet{{border-left-color:var(--line-strong); background:var(--surface-2);}}
.radar .eyebrow{{margin-bottom:5px; display:block;}}
.radar.quiet .eyebrow{{color:var(--ink-faint);}}
.radar p{{font-size:0.88rem; line-height:1.55; color:var(--ink-soft); margin:0;}}

.eyebrow{{text-transform:uppercase; letter-spacing:0.08em; font-size:0.7rem; color:var(--accent); font-weight:600;}}
.section-sub{{color:var(--ink-soft); font-size:0.85rem; margin-bottom:20px; max-width:70ch; line-height:1.5;}}

.sector{{border:1px solid var(--line); border-radius:14px; background:var(--surface); margin-bottom:14px; overflow:hidden; transition:border-color 0.15s ease, box-shadow 0.15s ease;}}
.sector:hover{{border-color:var(--line-strong); box-shadow:0 2px 10px rgba(20,26,43,0.06);}}
.sector-head{{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:18px 20px; cursor:pointer; user-select:none;}}
.sector-head:hover{{background:var(--surface-2);}}
.sector-head-left{{display:flex; flex-direction:column; gap:3px;}}
.sector-head h2{{font-size:1.15rem; font-weight:600;}}
.sector-chevron{{color:var(--ink-faint); transition:transform 0.18s ease; flex-shrink:0; font-size:1.1rem;}}
.sector[open] .sector-chevron{{transform:rotate(90deg);}}
summary::-webkit-details-marker{{display:none;}}
summary{{list-style:none;}}
summary::marker{{content:"";}}

.sector-body{{padding:2px 20px 24px; border-top:1px solid var(--line);}}
.field-grid{{display:grid; grid-template-columns:1fr 1fr; gap:18px; margin:18px 0;}}
@media (max-width:640px){{ .field-grid{{grid-template-columns:1fr;}} }}
.field .flabel{{font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-faint); font-weight:600; margin-bottom:5px;}}
.field p{{font-size:0.86rem; line-height:1.55; color:var(--ink-soft); margin:0;}}
.field ul{{margin:0; padding-left:18px; font-size:0.86rem; line-height:1.6; color:var(--ink-soft);}}
.field-full{{grid-column:1/-1;}}

.company-section-title{{font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-faint); font-weight:600; margin:22px 0 10px; padding-top:16px; border-top:1px solid var(--line);}}
.company-grid{{display:grid; grid-template-columns:1fr 1fr; gap:12px;}}
@media (max-width:640px){{ .company-grid{{grid-template-columns:1fr;}} }}
.company-card{{border:1px solid var(--line); border-radius:10px; background:var(--surface-2); padding:14px 16px;}}
.company-card .chead{{display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-bottom:6px;}}
.company-card h3{{font-size:0.92rem; font-weight:600;}}
.type-tag{{font-size:0.62rem; padding:2px 8px; border-radius:999px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; white-space:nowrap;}}
.type-tag.public{{background:var(--positive-soft); color:var(--positive);}}
.type-tag.private{{background:var(--accent-soft); color:var(--accent);}}
.company-card .cdesc{{font-size:0.82rem; color:var(--ink-soft); line-height:1.5; margin-bottom:8px;}}
.company-card .cstat{{font-size:0.78rem; margin-bottom:6px;}}
.company-card .cstat .l{{color:var(--ink-faint); font-weight:600; text-transform:uppercase; font-size:0.65rem; letter-spacing:0.04em; display:block; margin-bottom:2px;}}
.company-card .cstat .v{{color:var(--ink-soft); line-height:1.5;}}
.company-card a{{color:var(--accent); font-size:0.78rem; text-decoration:none; border-bottom:1px solid var(--line-strong); display:inline-block; margin-top:4px;}}
.company-card a:hover{{border-color:var(--accent);}}

footer{{color:var(--ink-faint); font-size:0.75rem; border-top:1px solid var(--line); padding-top:16px; margin-top:24px; line-height:1.6;}}
@media (max-width:480px){{ .masthead{{flex-direction:column;}} .masthead .meta{{text-align:left;}} }}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="wrap">
  <div class="masthead">
    <h1>Frontier Watch</h1>
    <div class="meta">Emerging tech &amp; sector trend monitor<br>As of {as_of_display}</div>
  </div>

  <div class="radar{radar_quiet_class}">
    <span class="eyebrow">Radar</span>
    <p>{radar_text}</p>
  </div>

  <div class="section-sub">{sector_count} frontier sectors tracked. Click any sector for the full drilldown: predominant companies, investors, funding/performance history, and adjacent players that stand to gain.</div>

  {sector_cards}

  <footer>
    Research via WebSearch, methodology informed by the market-researcher plugin's sector-overview/competitive-analysis structure (full comps-spread step needs a paid CapIQ/FactSet MCP not available here). Free/unauthenticated sources throughout &mdash; see WISHLIST.md. Generated by pipeline/render_point2_html.py.
  </footer>
</div>
"""

COMPANY_CARD = """<div class="company-card">
  <div class="chead">
    <h3>{name}{ticker_suffix}</h3>
    <span class="type-tag {type_class}">{type_label}</span>
  </div>
  {desc_html}
  <div class="cstat"><span class="l">Investors</span><span class="v">{investors}</span></div>
  <div class="cstat"><span class="l">Performance / funding history</span><span class="v">{performance}</span></div>
  {citation_link}
</div>"""


def field(label, content, full=False):
    cls = "field field-full" if full else "field"
    return f'<div class="{cls}"><div class="flabel">{label}</div>{content}</div>'


def field_p(label, text, full=False):
    return field(label, f"<p>{text}</p>", full=full)


def field_ul(label, items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return field(f"{label}", f"<ul>{lis}</ul>")


def company_card(c):
    is_public = c["type"].startswith("public")
    type_class = "public" if is_public else "private"
    ticker_suffix = f' <span class="mono" style="font-size:0.78rem;color:var(--ink-faint);">{c["ticker"]}</span>' if c.get("ticker") else ""
    desc = c.get("description") or c.get("relationship") or ""
    desc_html = f'<div class="cdesc">{desc}</div>' if desc else ""
    citations = c.get("citations", [])
    citation_link = ""
    if citations:
        citation_link = "".join(
            f'<a href="{cit["url"]}" target="_blank" rel="noopener">{cit["title"]}</a>' for cit in citations
        )
    return COMPANY_CARD.format(
        name=c["name"],
        ticker_suffix=ticker_suffix,
        type_class=type_class,
        type_label=c["type"],
        desc_html=desc_html,
        investors=c.get("investors", "n/a"),
        performance=c.get("performance", "n/a"),
        citation_link=citation_link,
    )


def sector_card(s):
    fields_html = "".join([
        field_p("How it works", s["how_it_works"], full=True),
        field_p("Maturity", s["maturity"]),
        field_ul("Applications", s["applications"]),
        field_p("Major investors &amp; lenders", s["investors_lenders"]),
        field_p("Roadblocks &amp; competing tech", s["roadblocks"]),
        field_p("Market sentiment", s["sentiment"], full=True),
    ])
    primary_cards = "".join(company_card(c) for c in s["primary_companies"])
    adjacent_cards = "".join(company_card(c) for c in s["adjacent_companies"])
    return f"""<details class="sector">
  <summary class="sector-head">
    <div class="sector-head-left">
      <span class="eyebrow">{s['eyebrow']}</span>
      <h2>{s['name']}</h2>
    </div>
    <span class="sector-chevron">&#9656;</span>
  </summary>
  <div class="sector-body">
    <div class="field-grid">{fields_html}</div>
    <div class="company-section-title">Predominant companies</div>
    <div class="company-grid">{primary_cards}</div>
    <div class="company-section-title">Adjacent &amp; complementary companies</div>
    <div class="company-grid">{adjacent_cards}</div>
  </div>
</details>"""


def main():
    with open("data/point2/sectors.json", encoding="utf-8") as f:
        data = json.load(f)

    sector_cards = "\n".join(sector_card(s) for s in data["sectors"])
    radar_text = data.get("radar") or "Nothing new stands out this pull."
    is_quiet = not data.get("radar")

    html = TEMPLATE.format(
        as_of_display=data["as_of"],
        radar_quiet_class=" quiet" if is_quiet else "",
        radar_text=radar_text,
        sector_count=len(data["sectors"]),
        sector_cards=sector_cards,
    )

    with open("artifacts/point2.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote artifacts/point2.html ({len(data['sectors'])} sectors)")


if __name__ == "__main__":
    main()

"""Render the Point 4 (fixed income / structured credit) artifact HTML from
data/point4/asset_classes.json. One card per asset class (native <details>
expand, matching Point 1/2's pattern): how it works, market size/issuance,
performance & spread commentary, institutional commentary/activity, Fed
sensitivity, headwinds/tailwinds, sentiment, investable exposure.

Every citation carries its own source date, rendered next to the link -
distinct from the page's overall pull ("as_of") date, per the user's
explicit requirement that a refresh never present old news as new. See
freshness_note in the data file.
"""
import json


TEMPLATE = """<!doctype html>
<title>Credit Desk</title>
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

.freshness{{border-left:3px solid var(--accent); background:var(--accent-soft); border-radius:0 10px 10px 0; padding:12px 16px; margin-bottom:14px;}}
.freshness p{{font-size:0.85rem; line-height:1.55; color:var(--ink-soft); margin:0;}}
.gap-note{{border:1px dashed var(--line-strong); border-radius:10px; padding:12px 16px; margin-bottom:28px; background:var(--surface-2);}}
.gap-note p{{font-size:0.82rem; line-height:1.55; color:var(--ink-faint); margin:0;}}

.eyebrow{{text-transform:uppercase; letter-spacing:0.08em; font-size:0.7rem; color:var(--accent); font-weight:600;}}
.section-sub{{color:var(--ink-soft); font-size:0.85rem; margin-bottom:20px; max-width:70ch; line-height:1.5;}}

.assetclass{{border:1px solid var(--line); border-radius:14px; background:var(--surface); margin-bottom:14px; overflow:hidden; transition:border-color 0.15s ease, box-shadow 0.15s ease;}}
.assetclass:hover{{border-color:var(--line-strong); box-shadow:0 2px 10px rgba(20,26,43,0.06);}}
.ac-head{{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:18px 20px; cursor:pointer; user-select:none;}}
.ac-head:hover{{background:var(--surface-2);}}
.ac-head-left{{display:flex; flex-direction:column; gap:3px;}}
.ac-head h2{{font-size:1.15rem; font-weight:600;}}
.ac-chevron{{color:var(--ink-faint); transition:transform 0.18s ease; flex-shrink:0; font-size:1.1rem;}}
.assetclass[open] .ac-chevron{{transform:rotate(90deg);}}
summary::-webkit-details-marker{{display:none;}}
summary{{list-style:none;}}
summary::marker{{content:"";}}

.ac-body{{padding:2px 20px 24px; border-top:1px solid var(--line);}}
.field-grid{{display:grid; grid-template-columns:1fr 1fr; gap:18px; margin:18px 0;}}
@media (max-width:640px){{ .field-grid{{grid-template-columns:1fr;}} }}
.field .flabel{{font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-faint); font-weight:600; margin-bottom:5px;}}
.field p{{font-size:0.86rem; line-height:1.55; color:var(--ink-soft); margin:0;}}
.field-full{{grid-column:1/-1;}}

.cite-list{{display:flex; flex-direction:column; gap:5px; margin-top:14px; padding-top:12px; border-top:1px solid var(--line);}}
.cite-row{{display:flex; align-items:baseline; gap:8px; font-size:0.78rem;}}
.cite-row a{{color:var(--ink); text-decoration:none; border-bottom:1px solid var(--line-strong); flex:1; min-width:0;}}
.cite-row a:hover{{color:var(--accent); border-color:var(--accent);}}
.cite-date{{color:var(--ink-faint); font-size:0.72rem; white-space:nowrap; font-family:'IBM Plex Mono',ui-monospace,monospace;}}

.invest-section-title{{font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent); font-weight:600; margin:22px 0 10px; padding-top:16px; border-top:2px solid var(--accent-soft);}}
.invest-subhead{{font-size:0.66rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-faint); font-weight:600; margin:14px 0 8px;}}
.company-grid{{display:grid; grid-template-columns:1fr 1fr; gap:12px;}}
@media (max-width:640px){{ .company-grid{{grid-template-columns:1fr;}} }}
.invest-card{{border:1px solid var(--line); border-radius:10px; background:var(--surface-2); padding:14px 16px;}}
.invest-card .chead{{display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-bottom:6px;}}
.invest-card h3{{font-size:0.9rem; font-weight:600;}}
.type-tag{{font-size:0.62rem; padding:2px 8px; border-radius:999px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; white-space:nowrap; background:var(--positive-soft); color:var(--positive);}}
.invest-card .cdesc{{font-size:0.82rem; color:var(--ink-soft); line-height:1.5; margin-bottom:6px;}}

footer{{color:var(--ink-faint); font-size:0.75rem; border-top:1px solid var(--line); padding-top:16px; margin-top:24px; line-height:1.6;}}
@media (max-width:480px){{ .masthead{{flex-direction:column;}} .masthead .meta{{text-align:left;}} }}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="wrap">
  <div class="masthead">
    <h1>Credit Desk</h1>
    <div class="meta">Fixed income &amp; structured credit commentary<br>As of {as_of_display}</div>
  </div>

  <div class="freshness">
    <p>{freshness_note}</p>
  </div>
  <div class="gap-note">
    <p><strong>Data availability:</strong> {data_gap_note}</p>
  </div>

  <div class="section-sub">{ac_count} structured product types tracked. Click any one for the full one-pager. Every citation shows its own source date &mdash; check it, not just the page timestamp above.</div>

  {ac_cards}

  <footer>
    Sources: bank/asset-manager research notes, rating agencies, SIFMA issuance statistics, Federal Reserve communications, SEC filings. Free/unauthenticated sources throughout &mdash; see WISHLIST.md for the structured-credit spread-data gap. Generated by pipeline/render_point4_html.py.
  </footer>
</div>
"""


def field(label, text, full=False):
    cls = "field field-full" if full else "field"
    return f'<div class="{cls}"><div class="flabel">{label}</div><p>{text}</p></div>'


def citation_list(citations):
    if not citations:
        return '<div class="cite-list"><span style="color:var(--ink-faint);font-size:0.8rem;">No sources attached yet.</span></div>'
    rows = "".join(
        f'<div class="cite-row"><a href="{c["url"]}" target="_blank" rel="noopener">{c["title"]}</a><span class="cite-date">{c.get("date", "n/d")}</span></div>'
        for c in citations
    )
    return f'<div class="cite-list">{rows}</div>'


def exposure_card(item, is_public):
    ticker_suffix = f' <span class="mono" style="font-size:0.78rem;color:var(--ink-faint);">{item["ticker"]}</span>' if item.get("ticker") else ""
    type_tag = f'<span class="type-tag">{item["type"]}</span>' if item.get("type") else ""
    desc = item.get("performance") or item.get("news") or item.get("description") or ""
    desc2 = ""
    if item.get("description") and item.get("news"):
        desc2 = f'<p class="cdesc">{item["news"]}</p>'
        desc = item["description"]
    return f"""<div class="invest-card">
      <div class="chead">
        <h3>{item['name']}{ticker_suffix}</h3>
        {type_tag}
      </div>
      <p class="cdesc">{desc}</p>
      {desc2}
      {citation_list(item.get('citations', []))}
    </div>"""


def investable_exposure_section(ie):
    if not ie:
        return ""
    public_cards = "".join(exposure_card(p, True) for p in ie.get("public", []))
    private_cards = "".join(exposure_card(p, False) for p in ie.get("private", []))
    return f"""<div class="invest-section-title">Investable exposure</div>
    <div class="invest-subhead">Public (ETF / REIT / BDC / CEF)</div>
    <div class="company-grid">{public_cards}</div>
    <div class="invest-subhead">Private / institutional funds</div>
    <div class="company-grid">{private_cards}</div>"""


def asset_class_card(ac):
    fields_html = "".join([
        field("How it works", ac["how_it_works"], full=True),
        field("Market size &amp; issuance", ac["market_size_issuance"]),
        field("Performance &amp; spread commentary", ac["performance_commentary"]),
        field("Institutional commentary", ac["institutional_commentary"]),
        field("Institutional investment activity", ac["institutional_investment_activity"]),
        field("Fed-decision sensitivity", ac["fed_sensitivity"]),
        field("Headwinds &amp; tailwinds", ac["headwinds_tailwinds"]),
        field("Sentiment &amp; outlook", ac["sentiment_outlook"], full=True),
    ])
    invest_html = investable_exposure_section(ac.get("investable_exposure"))
    return f"""<details class="assetclass">
  <summary class="ac-head">
    <div class="ac-head-left">
      <span class="eyebrow">{ac['eyebrow']}</span>
      <h2>{ac['name']}</h2>
    </div>
    <span class="ac-chevron">&#9656;</span>
  </summary>
  <div class="ac-body">
    <div class="field-grid">{fields_html}</div>
    <div class="invest-section-title" style="border-top-color:var(--line); color:var(--ink-faint);">Sources for this one-pager</div>
    {citation_list(ac.get('citations', []))}
    {invest_html}
  </div>
</details>"""


def main():
    with open("data/point4/asset_classes.json", encoding="utf-8") as f:
        data = json.load(f)

    ac_cards = "\n".join(asset_class_card(ac) for ac in data["asset_classes"])

    html = TEMPLATE.format(
        as_of_display=data["as_of"],
        freshness_note=data.get("freshness_note", ""),
        data_gap_note=data.get("data_gap_note", ""),
        ac_count=len(data["asset_classes"]),
        ac_cards=ac_cards,
    )

    with open("artifacts/point4.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote artifacts/point4.html ({len(data['asset_classes'])} asset classes)")


if __name__ == "__main__":
    main()

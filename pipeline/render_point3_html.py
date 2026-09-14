"""Render the Point 3 (equities) artifact HTML from final_payload.json.
Portfolio tracker uses the `db` runtime capability (shared, persistent across
refreshes) - the page itself stays static; add/remove writes to the artifact
DB, seeded here with today's recommendation picks on first load only (JS
checks whether the collection is already populated before seeding).
"""
import json

CSS = """
:root{
  --paper:#EFF1EE; --surface:#FFFFFF; --surface-2:#F7F8F5;
  --ink:#141A2B; --ink-soft:#535A6B; --ink-faint:#8991A3;
  --accent:#A9762F; --accent-soft:#F0E4CE;
  --positive:#1F7A5C; --positive-soft:#E3F0EA;
  --negative:#B3402F; --negative-soft:#F7E7E2;
  --line:rgba(20,26,43,0.13); --line-strong:rgba(20,26,43,0.24);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#0D111C; --surface:#161C2B; --surface-2:#11162280;
    --ink:#E9E6DC; --ink-soft:#AEB4C4; --ink-faint:#767D8E;
    --accent:#D9A14A; --accent-soft:#3A2E17;
    --positive:#4FB897; --positive-soft:#12271F;
    --negative:#E58176; --negative-soft:#2B1712;
    --line:rgba(233,230,220,0.14); --line-strong:rgba(233,230,220,0.26);
  }
}
:root[data-theme="dark"]{
  --paper:#0D111C; --surface:#161C2B; --surface-2:#11162280;
  --ink:#E9E6DC; --ink-soft:#AEB4C4; --ink-faint:#767D8E;
  --accent:#D9A14A; --accent-soft:#3A2E17;
  --positive:#4FB897; --positive-soft:#12271F;
  --negative:#E58176; --negative-soft:#2B1712;
  --line:rgba(233,230,220,0.14); --line-strong:rgba(233,230,220,0.26);
}
*{box-sizing:border-box;}
body{margin:0; background:var(--paper); color:var(--ink); font-family:'Public Sans',system-ui,sans-serif; padding:0 20px; padding-block:32px;}
.wrap{max-width:1080px; margin:0 auto;}
h1,h2,h3{font-family:'Fraunces',Georgia,serif; text-wrap:balance; margin:0;}
.mono{font-family:'IBM Plex Mono',ui-monospace,monospace; font-variant-numeric:tabular-nums;}
.masthead{display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px 24px; border-bottom:2.5px solid var(--ink); padding-bottom:16px; margin-bottom:24px;}
.masthead h1{font-size:2rem; font-weight:600; letter-spacing:-0.01em;}
.masthead .meta{color:var(--ink-faint); font-size:0.8rem; text-align:right;}
nav.tabs{display:flex; gap:4px; margin-bottom:24px; border-bottom:1px solid var(--line); flex-wrap:wrap;}
nav.tabs button{background:none; border:none; font:inherit; font-weight:600; font-size:0.85rem; color:var(--ink-faint); padding:10px 16px; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px;}
nav.tabs button.active{color:var(--ink); border-bottom-color:var(--accent);}
.tabpanel{display:none;}
.tabpanel.active{display:block;}
.index-strip{display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:10px; overflow:hidden; margin-bottom:28px;}
.idx-cell{background:var(--surface); padding:14px 16px;}
.idx-cell .label{font-size:0.68rem; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;}
.idx-cell .value{font-size:1.2rem; font-weight:600;}
.idx-cell .chg{font-size:0.8rem; margin-top:2px;}
.up{color:var(--positive);} .down{color:var(--negative);}
section{margin-bottom:32px;}
.section-title{font-size:1.05rem; font-weight:600; margin-bottom:4px;}
.section-sub{color:var(--ink-soft); font-size:0.85rem; margin-bottom:16px;}
.sector-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px;}
.sector-tile{border-radius:10px; padding:14px; cursor:pointer; border:1px solid var(--line); transition:transform 0.1s ease;}
.sector-tile:hover{transform:translateY(-1px);}
.sector-tile .sname{font-size:0.78rem; font-weight:600; margin-bottom:8px; line-height:1.25;}
.sector-tile .schg{font-size:1.15rem; font-weight:600;}
.movers-grid{display:grid; grid-template-columns:1fr 1fr; gap:20px;}
@media (max-width:640px){ .movers-grid{grid-template-columns:1fr;} }
.mover-list{display:flex; flex-direction:column; gap:2px;}
.mover-row{display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:8px; cursor:pointer; border:1px solid transparent;}
.mover-row:hover{background:var(--surface-2); border-color:var(--line);}
.mover-row .tk{font-weight:600; font-size:0.88rem; width:60px;}
.mover-row .nm{flex:1; font-size:0.8rem; color:var(--ink-soft); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.mover-row .pc{font-weight:600; font-size:0.88rem; width:70px; text-align:right;}
table{width:100%; border-collapse:collapse; font-size:0.85rem;}
th{text-align:left; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-faint); padding:8px 10px; border-bottom:1px solid var(--line-strong);}
td{padding:9px 10px; border-bottom:1px solid var(--line);}
.card{border:1px solid var(--line); border-radius:12px; background:var(--surface); padding:16px 18px; margin-bottom:10px;}
.detail-panel{display:none; margin-top:12px; padding-top:12px; border-top:1px solid var(--line); font-size:0.85rem; color:var(--ink-soft); line-height:1.55;}
.detail-panel.open{display:block;}
.verdict{display:inline-block; font-size:0.68rem; padding:3px 10px; border-radius:999px; font-weight:600; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.03em;}
.verdict.aligned{background:var(--positive-soft); color:var(--positive);}
.verdict.counter{background:var(--negative-soft); color:var(--negative);}
.verdict.pending{background:var(--surface-2); color:var(--ink-faint);}
.citations a{display:block; color:var(--ink); font-size:0.8rem; text-decoration:none; border-bottom:1px solid var(--line-strong); margin-top:6px; width:fit-content;}
.citations a:hover{color:var(--accent); border-color:var(--accent);}
.bucket-title{font-size:0.9rem; font-weight:600; margin:20px 0 10px; display:flex; align-items:center; gap:8px;}
.bucket-badge{font-size:0.65rem; padding:2px 9px; border-radius:999px; background:var(--accent-soft); color:var(--accent); text-transform:uppercase; letter-spacing:0.04em;}
.pf-btn{font:inherit; font-size:0.72rem; font-weight:600; padding:4px 10px; border-radius:6px; border:1px solid var(--line-strong); background:var(--surface); color:var(--ink); cursor:pointer;}
.pf-btn.remove{color:var(--negative); border-color:var(--negative-soft);}
.pf-btn:hover{background:var(--surface-2);}
.member-table-wrap{overflow-x:auto;}
.vol-badge{display:flex; align-items:center; gap:14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); padding:16px 18px; flex-wrap:wrap;}
.vol-badge .tag{font-size:0.72rem; padding:4px 12px; border-radius:999px; font-weight:600; text-transform:uppercase;}
.tag.calm{background:var(--positive-soft); color:var(--positive);}
.tag.stress{background:var(--negative-soft); color:var(--negative);}
.empty-state{color:var(--ink-faint); font-size:0.85rem; padding:20px; text-align:center; border:1px dashed var(--line-strong); border-radius:10px;}
footer{color:var(--ink-faint); font-size:0.75rem; border-top:1px solid var(--line); padding-top:16px; margin-top:8px;}
"""

HTML_SHELL = """<!doctype html>
<title>Equities Desk</title>
<style>{css}</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">

<div class="wrap">
  <div class="masthead">
    <h1>Equities Desk</h1>
    <div class="meta">Indices &middot; sectors &middot; movers &middot; ideas<br>As of {as_of_display}</div>
  </div>

  <div class="index-strip">{index_cells}</div>

  <nav class="tabs">
    <button class="tab-btn active" data-tab="sectors">Sectors</button>
    <button class="tab-btn" data-tab="movers">Movers</button>
    <button class="tab-btn" data-tab="earnings">Earnings</button>
    <button class="tab-btn" data-tab="vol">Volatility</button>
    <button class="tab-btn" data-tab="ideas">Ideas</button>
    <button class="tab-btn" data-tab="portfolio">Portfolio</button>
  </nav>

  <div class="tabpanel active" id="tab-sectors">
    <div class="section-title">Sector performance (market-cap weighted)</div>
    <div class="section-sub">S&amp;P 1500 universe, ${min_cap_b:.0f}B+ market cap. Click a sector to see which names drove the move.</div>
    <div class="sector-grid">{sector_tiles}</div>
    <div id="sector-detail"></div>
  </div>

  <div class="tabpanel" id="tab-movers">
    <div class="section-title">Big movers</div>
    <div class="section-sub">Top 15 gainers/losers by day change, ${min_cap_b:.0f}B+ cap. Click a name for driver &amp; verdict.</div>
    <div class="movers-grid">
      <div><h3 style="font-size:0.85rem;margin-bottom:8px;">Gainers</h3><div class="mover-list">{gainer_rows}</div></div>
      <div><h3 style="font-size:0.85rem;margin-bottom:8px;">Losers</h3><div class="mover-list">{loser_rows}</div></div>
    </div>
    <div id="mover-detail"></div>
    <div class="section-title" style="margin-top:28px;">Volume outliers</div>
    <div class="section-sub">Volume &ge;2x the 3-month average &mdash; free-data proxy for unusual options/attention activity (see WISHLIST.md for the real-flow-data upgrade path).</div>
    <table><thead><tr><th>Ticker</th><th>Name</th><th>Day %</th><th>Vol / Avg</th></tr></thead><tbody>{vol_outlier_rows}</tbody></table>
  </div>

  <div class="tabpanel" id="tab-earnings">
    <div class="section-title">Upcoming earnings (next 10 days, in-universe)</div>
    <div class="section-sub">Click a row for the forward-looking setup &mdash; no driver/verdict since it hasn't happened yet.</div>
    {earnings_cards}
  </div>

  <div class="tabpanel" id="tab-vol">
    <div class="section-title">Volatility term structure</div>
    <div class="section-sub">Market-wide aggregate only &mdash; free data can't isolate single-name options flow (WISHLIST.md).</div>
    <div class="vol-badge">
      <span class="tag {vol_tag_class}">{vol_structure}</span>
      <div style="margin-left:auto; display:flex; gap:20px;">
        <div style="text-align:right;"><div style="font-size:0.68rem;color:var(--ink-faint);text-transform:uppercase;">VIX</div><div class="mono" style="font-weight:600;">{vix_val}</div></div>
        <div style="text-align:right;"><div style="font-size:0.68rem;color:var(--ink-faint);text-transform:uppercase;">VIX3M</div><div class="mono" style="font-weight:600;">{vix3m_val}</div></div>
      </div>
    </div>
  </div>

  <div class="tabpanel" id="tab-ideas">
    <div class="section-title">Daily recommendation memo</div>
    <div class="section-sub">{methodology_note}</div>
    {recommendation_buckets}
  </div>

  <div class="tabpanel" id="tab-portfolio">
    <div class="section-title">Portfolio</div>
    <div class="section-sub">Auto-seeded from each day's recommendation picks. Remove names you don't want tracked; add any ticker manually.</div>
    <div style="display:flex; gap:8px; margin-bottom:16px;">
      <input id="pf-add-input" placeholder="Add ticker (e.g. NVDA)" style="flex:1; padding:8px 12px; border-radius:8px; border:1px solid var(--line-strong); background:var(--surface); color:var(--ink); font:inherit;">
      <button class="pf-btn" id="pf-add-btn">Add</button>
    </div>
    <div id="portfolio-list"><div class="empty-state">Loading portfolio…</div></div>
  </div>

  <footer>
    Data: Yahoo Finance (prices, volume), Wikipedia (S&amp;P 1500 constituents), Nasdaq (earnings calendar), CBOE via Yahoo (VIX term structure). Free/unauthenticated sources. Market cap cache as of {cap_cache_as_of}. Generated by pipeline/render_point3_html.py.
  </footer>
</div>

<script>
const DATA = {data_json};

document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tabpanel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  }});
}});

function fmtPct(v) {{ return (v > 0 ? '+' : '') + v.toFixed(2) + '%'; }}
function fmtCap(v) {{
  if (v >= 1e12) return '$' + (v/1e12).toFixed(2) + 'T';
  if (v >= 1e9) return '$' + (v/1e9).toFixed(1) + 'B';
  return '$' + (v/1e6).toFixed(0) + 'M';
}}

// ---- Sector drill-down ----
document.querySelectorAll('.sector-tile').forEach(tile => {{
  tile.addEventListener('click', () => {{
    const sector = tile.dataset.sector;
    const s = DATA.sector_rollup.find(x => x.sector === sector);
    if (!s) return;
    const rows = s.members.slice(0, 25).map(m => `
      <tr>
        <td class="mono">${{m.ticker}}</td>
        <td>${{m.name || ''}}</td>
        <td class="mono ${{m.day_chg_pct > 0 ? 'up' : 'down'}}">${{fmtPct(m.day_chg_pct)}}</td>
        <td class="mono">${{fmtCap(m.market_cap)}}</td>
        <td class="mono ${{m.contribution_pct > 0 ? 'up' : 'down'}}">${{m.contribution_pct.toFixed(3)}}pp</td>
      </tr>`).join('');
    document.getElementById('sector-detail').innerHTML = `
      <div class="card">
        <h3 style="font-size:0.95rem;margin-bottom:4px;">${{sector}} &mdash; constituents ranked by contribution to the sector's move</h3>
        <div class="section-sub" style="margin-bottom:12px;">${{s.member_count}} names, ${{fmtCap(s.total_market_cap)}} combined cap, ${{fmtPct(s.day_chg_pct_weighted)}} weighted average.</div>
        <div class="member-table-wrap"><table><thead><tr><th>Ticker</th><th>Name</th><th>Day %</th><th>Mkt Cap</th><th>Contribution</th></tr></thead><tbody>${{rows}}</tbody></table></div>
      </div>`;
  }});
}});

// ---- Mover drill-down ----
function renderMoverDetail(m) {{
  const verdictClass = m.verdict === 'aligned' ? 'aligned' : (m.verdict === 'counter' ? 'counter' : 'pending');
  const citations = (m.citations || []).map(c => `<a href="${{c.url}}" target="_blank" rel="noopener">${{c.title}}</a>`).join('') || '<span style="color:var(--ink-faint);font-size:0.8rem;">No sources attached yet.</span>';
  document.getElementById('mover-detail').innerHTML = `
    <div class="card">
      <h3 style="font-size:0.95rem;">${{m.ticker}} &mdash; ${{m.name || ''}}</h3>
      <div class="section-sub">${{fmtPct(m.day_chg_pct)}} today &middot; ${{fmtCap(m.market_cap)}} cap &middot; ${{m.sector}}</div>
      <span class="verdict ${{verdictClass}}">${{m.verdict || 'not yet assessed'}}</span>
      <p style="font-size:0.88rem;color:var(--ink-soft);line-height:1.55;">${{m.narrative || 'Research pending.'}}</p>
      <div class="citations">${{citations}}</div>
    </div>`;
}}
document.querySelectorAll('.mover-row').forEach(row => {{
  row.addEventListener('click', () => {{
    const ticker = row.dataset.ticker;
    const bucket = row.dataset.bucket;
    const list = bucket === 'gainer' ? DATA.top_gainers : DATA.top_losers;
    const m = list.find(x => x.ticker === ticker);
    if (m) renderMoverDetail(m);
  }});
}});

// ---- Recommendation drill-down (delegated, cards render collapsed) ----
document.querySelectorAll('.rec-card-head').forEach(head => {{
  head.addEventListener('click', () => {{
    const panel = head.nextElementSibling;
    panel.classList.toggle('open');
  }});
}});

// ---- Portfolio (db capability) ----
(async () => {{
  const listEl = document.getElementById('portfolio-list');
  const db = window.claude ? await window.claude.use('db') : null;
  if (!db) {{
    listEl.innerHTML = '<div class="empty-state">Portfolio tracking needs the artifact to be opened in claude.ai (db capability unavailable in this preview).</div>';
    document.getElementById('pf-add-btn').disabled = true;
    return;
  }}

  async function seedIfEmpty() {{
    const existing = await db.collection('portfolio').get({{limit: 1}});
    if (existing.docs && existing.docs.length > 0) return;
    const allRecs = [...DATA.recommendations.bounce, ...DATA.recommendations.value, ...DATA.recommendations.speculative];
    for (const r of allRecs) {{
      await db.doc('portfolio/' + r.ticker).set({{
        ticker: r.ticker, name: r.name || r.ticker, bucket: r.bucket,
        date_added: DATA.as_of, source: 'recommendation_memo', status: 'active'
      }});
    }}
  }}

  async function renderPortfolio() {{
    const res = await db.collection('portfolio').get({{limit: 200}});
    const docs = (res.docs || []).filter(d => d.data.status !== 'removed');
    if (docs.length === 0) {{
      listEl.innerHTML = '<div class="empty-state">No holdings tracked yet.</div>';
      return;
    }}
    listEl.innerHTML = `<table><thead><tr><th>Ticker</th><th>Name</th><th>Bucket</th><th>Added</th><th></th></tr></thead><tbody>
      ${{docs.map(d => `
        <tr>
          <td class="mono">${{d.data.ticker}}</td>
          <td>${{d.data.name}}</td>
          <td><span class="bucket-badge">${{d.data.bucket}}</span></td>
          <td class="mono" style="font-size:0.78rem;color:var(--ink-faint);">${{(d.data.date_added||'').slice(0,10)}}</td>
          <td><button class="pf-btn remove" data-id="${{d.id}}">Remove</button></td>
        </tr>`).join('')}}
    </tbody></table>`;
    listEl.querySelectorAll('.pf-btn.remove').forEach(btn => {{
      btn.addEventListener('click', async () => {{
        await db.doc('portfolio/' + btn.dataset.id).update({{status: 'removed'}});
        renderPortfolio();
      }});
    }});
  }}

  document.getElementById('pf-add-btn').addEventListener('click', async () => {{
    const input = document.getElementById('pf-add-input');
    const ticker = input.value.trim().toUpperCase();
    if (!ticker) return;
    await db.doc('portfolio/' + ticker).set({{
      ticker, name: ticker, bucket: 'manual', date_added: new Date().toISOString(), source: 'manual', status: 'active'
    }});
    input.value = '';
    renderPortfolio();
  }});

  await seedIfEmpty();
  renderPortfolio();
}})();
</script>
"""


def fmt_pct_py(v):
    return f"{v:+.2f}%"


def idx_cell(name, idx):
    cls = "up" if idx["day_chg_pct"] > 0 else "down"
    return f"""<div class="idx-cell">
      <div class="label">{name}</div>
      <div class="value mono">{idx['last']:,.2f}</div>
      <div class="chg mono {cls}">{fmt_pct_py(idx['day_chg_pct'])}</div>
    </div>"""


def sector_color(chg):
    # blend toward positive/negative token by magnitude, capped
    import math
    mag = min(abs(chg) / 2.5, 1.0)
    if chg >= 0:
        return f"background: color-mix(in srgb, var(--positive-soft) {30+mag*70:.0f}%, var(--surface));"
    return f"background: color-mix(in srgb, var(--negative-soft) {30+mag*70:.0f}%, var(--surface));"


def sector_tile(s):
    cls = "up" if s["day_chg_pct_weighted"] > 0 else "down"
    style = sector_color(s["day_chg_pct_weighted"])
    return f"""<div class="sector-tile" data-sector="{s['sector']}" style="{style}">
      <div class="sname">{s['sector']}</div>
      <div class="schg mono {cls}">{fmt_pct_py(s['day_chg_pct_weighted'])}</div>
    </div>"""


def mover_row(m, bucket):
    cls = "up" if m["day_chg_pct"] > 0 else "down"
    return f"""<div class="mover-row" data-ticker="{m['ticker']}" data-bucket="{bucket}">
      <span class="tk mono">{m['ticker']}</span>
      <span class="nm">{m.get('name','')}</span>
      <span class="pc mono {cls}">{fmt_pct_py(m['day_chg_pct'])}</span>
    </div>"""


def vol_outlier_row(m):
    cls = "up" if m["day_chg_pct"] > 0 else "down"
    return f"""<tr>
      <td class="mono">{m['ticker']}</td><td>{m.get('name','')}</td>
      <td class="mono {cls}">{fmt_pct_py(m['day_chg_pct'])}</td>
      <td class="mono">{m['volume_vs_avg_ratio']:.1f}x</td>
    </tr>"""


def earnings_card(e):
    eps_f = e.get("eps_forecast") or "n/a"
    eps_ly = e.get("last_year_eps") or "n/a"
    return f"""<div class="card">
      <div style="display:flex; justify-content:space-between; align-items:baseline;">
        <h3 style="font-size:0.92rem;">{e['ticker']} &mdash; {e.get('company','')}</h3>
        <span class="mono" style="font-size:0.78rem; color:var(--ink-faint);">{e['date']}</span>
      </div>
      <div class="section-sub" style="margin-bottom:0;">EPS forecast {eps_f} vs {eps_ly} a year ago &middot; {e.get('time','').replace('time-','').replace('-',' ')}</div>
    </div>"""


def recommendation_card(r, bucket_label):
    verdict = r.get("verdict", "not yet assessed")
    vclass = "aligned" if verdict == "aligned" else ("counter" if verdict == "counter" else "pending")
    citations = "".join(
        f'<a href="{c["url"]}" target="_blank" rel="noopener">{c["title"]}</a>' for c in r.get("citations", [])
    ) or '<span style="color:var(--ink-faint); font-size:0.8rem;">No sources attached yet.</span>'
    return f"""<div class="card">
      <div class="rec-card-head" style="cursor:pointer; display:flex; justify-content:space-between; align-items:baseline;">
        <h3 style="font-size:0.92rem;">{r['ticker']} &mdash; {r.get('name','')}</h3>
        <span class="mono" style="font-size:0.85rem;">{r.get('sector','')}</span>
      </div>
      <div class="detail-panel">
        <span class="verdict {vclass}">{verdict}</span>
        <p>{r.get('thesis', 'Research pending.')}</p>
        <div class="citations">{citations}</div>
      </div>
    </div>"""


def main():
    with open("data/point3/final_payload.json") as f:
        payload = json.load(f)

    as_of = payload["as_of"][:16].replace("T", " ") + " UTC"

    with open("data/point3/indices.json") as f:
        idx_raw = json.load(f)["indices"]
    index_cells = "\n".join(idx_cell(name, idx) for name, idx in idx_raw.items())

    sector_tiles = "\n".join(sector_tile(s) for s in payload["sector_rollup"])
    gainer_rows = "\n".join(mover_row(m, "gainer") for m in payload["top_gainers"])
    loser_rows = "\n".join(mover_row(m, "loser") for m in payload["top_losers"])
    vol_outlier_rows = "\n".join(vol_outlier_row(m) for m in payload["volume_outliers"]) or '<tr><td colspan="4" style="color:var(--ink-faint);">None found above 2x average volume.</td></tr>'
    earnings_cards = "\n".join(earnings_card(e) for e in payload["earnings_calendar"]) or '<div class="empty-state">No in-universe earnings in the next 10 days.</div>'

    rec_html_parts = []
    bucket_meta = {
        "bounce": ("Oversold bounce", "Down &gt;15% in 5 days, no confirmed fundamental deterioration"),
        "value": ("Value / fundamental discount", "&ge;25% off 52-week high, not this week's acute drop, top-half of sector by cap (52wk-discount proxy &mdash; see WISHLIST.md)"),
        "speculative": ("Speculative / momentum", "Volume &ge;2x average with positive price action"),
    }
    for bucket_key, (label, desc) in bucket_meta.items():
        items = payload["recommendations"].get(bucket_key, [])
        cards = "".join(recommendation_card(r, label) for r in items) or '<div class="empty-state">No names cleared this screen today.</div>'
        rec_html_parts.append(f"""<div class="bucket-title"><span class="bucket-badge">{label}</span><span style="color:var(--ink-faint); font-weight:400; font-size:0.8rem;">{desc}</span></div>{cards}""")
    recommendation_buckets = "\n".join(rec_html_parts)

    vol = payload.get("vol_term_structure") or {}
    # vol term structure not in point3 payload by default; fall back to macro file
    if not vol:
        with open("data/point1/macro.json") as f:
            vol = json.load(f).get("vol_term_structure", {})
    vol_structure = vol.get("structure", "n/a")
    vol_tag_class = "stress" if "backwardation" in vol_structure else "calm"

    html = HTML_SHELL.format(
        css=CSS,
        as_of_display=as_of,
        index_cells=index_cells,
        min_cap_b=payload["min_market_cap_filter"] / 1e9,
        sector_tiles=sector_tiles,
        gainer_rows=gainer_rows,
        loser_rows=loser_rows,
        vol_outlier_rows=vol_outlier_rows,
        earnings_cards=earnings_cards,
        vol_structure=vol_structure,
        vol_tag_class=vol_tag_class,
        vix_val=vol.get("VIX", {}).get("last_value", "n/a"),
        vix3m_val=vol.get("VIX3M", {}).get("last_value", "n/a"),
        methodology_note=payload["recommendations"].get("methodology_note", ""),
        recommendation_buckets=recommendation_buckets,
        cap_cache_as_of=payload["market_cap_cache_as_of"][:10],
        data_json=json.dumps(payload),
    )

    with open("artifacts/point3.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote artifacts/point3.html")


if __name__ == "__main__":
    main()

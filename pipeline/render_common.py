"""Shared rendering helpers used by the render_point*_html.py scripts."""
import html
import json
import re
from datetime import date

HUB_URL = "https://claude.ai/code/artifact/984f7869-6d78-4b90-bf73-86d17366b757"

# "Back to hub" pill shown at the top of every point page. Lives here (not hand-edited into
# artifacts/*.html) so a re-render never silently drops it.
HUB_BACK_LINK = (
    '<a class="hub-back" href="{hub_url}" target="_blank" rel="noopener" style="display:inline-flex; align-items:center; gap:6px; margin-bottom:18px; padding:6px 12px; border:1px solid var(--line-strong); border-radius:999px; background:var(--surface); color:var(--ink-soft); font-family:\'Public Sans\',system-ui,sans-serif; font-size:0.78rem; font-weight:600; text-decoration:none;" onmouseover="this.style.color=\'var(--accent)\';this.style.borderColor=\'var(--accent)\'" onmouseout="this.style.color=\'var(--ink-soft)\';this.style.borderColor=\'var(--line-strong)\'">&larr; Market Dashboard</a>'
).format(hub_url=HUB_URL)


def add_hub_back_link(page_html):
    """Insert the hub back-link as the first child of the page's .wrap container."""
    return page_html.replace('<div class="wrap">', '<div class="wrap">\n  ' + HUB_BACK_LINK, 1)


# ---------- Update-tag convention (see CLAUDE.md, "Update tags") ----------
# Only the current pull's updates are ever called out, as "UPDATE (mm/dd/yy): ...". Tags from
# earlier pulls (and legacy "UPDATE (this pull, YYYY-MM-DD)" tags) are pruned: the label is
# dropped and the text reads as ordinary carried-forward content. Everything here is
# idempotent, so normalize_update_tags.py and the renderers can both apply it safely.

PULL_DATE_PATH = "data/content_overrides.json"
TAG_RE = re.compile(r"\b(UPDATE|CORRECTION) \(([^()]*)\):\s*")
PRIOR_RE = re.compile(r"\s*Prior framing:\s*")
SPLIT_RE = re.compile(TAG_RE.pattern + r"|" + PRIOR_RE.pattern)
THIS_PULL_RE = re.compile(r"\b([Tt])his pull\b")
THIS_PULL_PREP_RE = re.compile(r"\b(in|on|from|of|for|during|at|since|by|vs\.|with|than) this pull\b")
# Sentence-initial "This pull", possessive "this pull's", or "this pull" as a subject/object noun
THIS_PULL_NOUN_RE = re.compile(r"\b(?:(T)his pull\b|(t)his pull(?='s))")
ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
MDY_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{2})$")
# Citation/link fields are never rewritten.
SKIP_KEYS = {"url", "title", "date", "ticker", "id", "last_updated", "as_of"}


def load_pull_date():
    """The pull date (YYYY-MM-DD) every page's update badges are measured against. Written by
    pipeline/normalize_update_tags.py at the start of each pull's build step."""
    with open(PULL_DATE_PATH, encoding="utf-8") as f:
        pull_date = json.load(f).get("pull_date")
    if not pull_date:
        raise SystemExit("data/content_overrides.json has no 'pull_date' - run pipeline/normalize_update_tags.py first.")
    return pull_date


def mdy(iso):
    """'2026-10-18' (or a full ISO timestamp) -> '10/18/26'."""
    d = date.fromisoformat(iso[:10])
    return d.strftime("%m/%d/%y")


def _tag_date(inner):
    """Date (YYYY-MM-DD) a tag's parenthetical refers to, or None if it has none."""
    m = MDY_RE.match(inner.strip())
    if m:
        return f"20{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = ISO_RE.search(inner)
    return m.group(0) if m else None


def _date_this_pull(text, seg_date):
    """'this pull' -> the dated pull it refers to (or 'an earlier pull' if that date is unknown):
    'This pull found' -> 'The 10/18/26 pull found'; 'in this pull' -> 'in the 10/18/26 pull';
    bare adverbial 'checked this pull' -> 'checked on 10/18/26'."""
    named = f"{mdy(seg_date)} pull" if seg_date else "earlier pull"
    det = "the" if seg_date else "an"
    text = THIS_PULL_PREP_RE.sub(lambda m: f"{m.group(1)} {det} {named}", text)
    text = THIS_PULL_NOUN_RE.sub(
        lambda m: (det.capitalize() if m.group(1) == "T" else det) + f" {named}", text
    )
    return THIS_PULL_RE.sub(f"on {mdy(seg_date)}" if seg_date else "in an earlier pull", text)


def normalize_text(text, pull_date, base_date=None):
    """Apply the update-tag convention to one string.
    base_date: the date untagged text was written on, if known (e.g. an entry's last_updated,
    or a note's own as_of) - used only to date any "this pull" phrasing in it."""
    if not isinstance(text, str) or not text:
        return text
    segments = []  # (date, kind, text)
    seg_date, seg_kind, pos = base_date, None, 0
    for m in SPLIT_RE.finditer(text):
        segments.append((seg_date, seg_kind, text[pos:m.start()]))
        if m.group(1):  # a tag
            seg_date, seg_kind = _tag_date(m.group(2)), m.group(1)
        else:  # "Prior framing:" - what follows is older text of unknown date
            seg_date, seg_kind = None, None
        pos = m.end()
    segments.append((seg_date, seg_kind, text[pos:]))

    pieces, prev_current = [], False
    for seg_date, seg_kind, seg_text in segments:
        seg_text = seg_text.strip()
        if not seg_text:
            continue
        current = seg_date == pull_date
        seg_text = _date_this_pull(seg_text, seg_date)
        if current and seg_kind:
            piece = f"{seg_kind} ({mdy(pull_date)}): {seg_text}"
        elif prev_current and not current:
            piece = f"Prior framing: {seg_text}"
        else:
            piece = seg_text
            # a pruned tag can leave a lowercase sentence start ("...raised. the Army ...")
            if pieces and pieces[-1][-1:] in ".!?" and piece[:1].islower():
                piece = piece[0].upper() + piece[1:]
        pieces.append(piece)
        prev_current = current and bool(seg_kind)
    return " ".join(pieces)


def normalize_obj(obj, pull_date, base_date=None):
    """normalize_text applied to every string in a JSON structure (citation fields skipped).
    An entry's own last_updated (or, for its direct string fields only, its as_of) is the base
    date for its untagged text; nested entries inherit last_updated but never a parent's as_of."""
    if isinstance(obj, dict):
        child_base = obj.get("last_updated", base_date)
        own_base = obj.get("last_updated") or obj.get("as_of") or base_date
        return {
            k: v if k in SKIP_KEYS
            else normalize_text(v, pull_date, own_base) if isinstance(v, str)
            else [normalize_text(x, pull_date, own_base) for x in v] if isinstance(v, list) and all(isinstance(x, str) for x in v)
            else normalize_obj(v, pull_date, child_base)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [normalize_obj(v, pull_date, base_date) for v in obj]
    return normalize_text(obj, pull_date, base_date)


def has_current_tag(obj, pull_date):
    """True if any string in obj carries this pull's UPDATE/CORRECTION tag."""
    if isinstance(obj, dict):
        return any(has_current_tag(v, pull_date) for k, v in obj.items() if k not in SKIP_KEYS)
    if isinstance(obj, list):
        return any(has_current_tag(v, pull_date) for v in obj)
    if isinstance(obj, str):
        return any(_tag_date(m.group(2)) == pull_date for m in TAG_RE.finditer(obj))
    return False


def is_updated(entry, pull_date):
    """An item counts as updated this pull if it was (re)written this pull (last_updated) or
    carries a current-pull tag anywhere inside it."""
    return (isinstance(entry, dict) and entry.get("last_updated") == pull_date) or has_current_tag(entry, pull_date)


UPDATE_CSS = """
.upd-tag{background:var(--accent-soft); color:var(--accent); font-weight:700; padding:1px 6px; border-radius:4px; font-style:normal; white-space:nowrap;}
.upd-badge{display:inline-block; font-size:0.62rem; padding:2px 8px; border-radius:999px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; white-space:nowrap; vertical-align:middle; font-family:'Public Sans',system-ui,sans-serif;}
.sector-head .upd-badge, .ac-head .upd-badge{margin-left:auto; margin-right:-4px;}
.upd-badge.on{background:var(--accent); color:var(--surface);}
.upd-badge.off{background:transparent; color:var(--ink-faint); border:1px solid var(--line-strong);}
.upd-panel{border:1px solid var(--accent); border-radius:12px; background:var(--surface); padding:14px 18px; margin-bottom:22px;}
.upd-panel .upd-title{font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--accent); font-weight:700; margin-bottom:10px;}
.upd-panel .upd-group{margin-top:10px;}
.upd-panel .upd-group:first-of-type{margin-top:0;}
.upd-panel .upd-glabel{font-size:0.66rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-faint); font-weight:600; margin-bottom:6px;}
.upd-panel ul{margin:0; padding-left:18px; font-size:0.84rem; line-height:1.55; color:var(--ink-soft);}
.upd-panel ul li strong{color:var(--ink); font-weight:600;}
.upd-panel .upd-list{font-size:0.84rem; line-height:1.6; color:var(--ink-soft);}
.upd-panel .upd-list strong{color:var(--ink); font-weight:600;}
.upd-panel .upd-none{font-size:0.82rem; line-height:1.6; color:var(--ink-faint);}
"""


def update_badge(updated, pull_date, short=False):
    when = "" if short else f" {mdy(pull_date)}"
    if updated:
        return f'<span class="upd-badge on">Updated{when}</span>'
    return f'<span class="upd-badge off">No update{when}</span>'


def update_panel(pull_date, groups):
    """Up-front summary of what this pull changed. groups: [(label, [(name, updated, detail)])].
    Updated items are listed with what changed; everything else is named as not updated."""
    blocks = []
    for label, items in groups:
        upd = [(n, d) for n, u, d in items if u]
        stale = [n for n, u, _ in items if not u]
        if any(d for _, d in upd) or any(len(n) > 14 for n, _ in upd):
            lis = "".join(
                f"<li><strong>{html.escape(n)}</strong>{(' &mdash; ' + html.escape(d)) if d else ''}</li>" for n, d in upd
            )
            upd_html = f"<ul>{lis}</ul>"
        elif upd:  # names only - one compact line
            upd_html = f'<div class="upd-list">Updated: <strong>{html.escape(", ".join(n for n, _ in upd))}</strong></div>'
        else:
            upd_html = ""
        gap = ' style="margin-top:6px;"' if upd else ""
        stale_html = f'<div class="upd-none"{gap}>No update: {html.escape(", ".join(stale))}</div>' if stale else ""
        blocks.append(
            f'<div class="upd-group"><div class="upd-glabel">{html.escape(label)} &middot; '
            f'{len(upd)} of {len(items)} updated</div>{upd_html}{stale_html}</div>'
        )
    return (
        f'<div class="upd-panel"><div class="upd-title">What changed &middot; {mdy(pull_date)}</div>'
        + "".join(blocks) + "</div>"
    )


def finalize_page(page_html, pull_date):
    """Shared last step for every page: hub back-link, update-tag CSS, and highlighting of this
    pull's inline tags (single-quoted attributes so it is also safe inside embedded JSON)."""
    page_html = add_hub_back_link(page_html)
    page_html = page_html.replace("</style>", UPDATE_CSS + "</style>", 1)
    tag = re.compile(r"\b(UPDATE|CORRECTION) \(" + re.escape(mdy(pull_date)) + r"\):")
    return tag.sub(lambda m: f"<mark class='upd-tag'>{m.group(0)}</mark>", page_html)



def svg_sparkline(values, width=72, height=26, color="var(--accent)", stroke_width=1.6):
    """Inline SVG sparkline - no library, scaled to the series' own min/max."""
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1.0
    pad = stroke_width
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = pad + (i / (n - 1)) * (width - 2 * pad)
        y = pad + (1 - (v - lo) / rng) * (height - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    last_x, last_y = pts[-1].split(",")
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block; overflow:visible;">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.1" fill="{color}"/>'
        f"</svg>"
    )

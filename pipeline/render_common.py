"""Shared rendering helpers used by the render_point*_html.py scripts."""


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


HUB_URL = "https://claude.ai/code/artifact/984f7869-6d78-4b90-bf73-86d17366b757"

HUB_LINK_HTML = (
    f'<a class="hub-back" href="{HUB_URL}" target="_blank" rel="noopener" '
    'style="display:inline-flex; align-items:center; gap:6px; margin-bottom:18px; padding:6px 12px; '
    'border:1px solid var(--line-strong); border-radius:999px; background:var(--surface); '
    "color:var(--ink-soft); font-family:'Public Sans',system-ui,sans-serif; font-size:0.78rem; "
    'font-weight:600; text-decoration:none;" '
    "onmouseover=\"this.style.color='var(--accent)';this.style.borderColor='var(--accent)'\" "
    "onmouseout=\"this.style.color='var(--ink-soft)';this.style.borderColor='var(--line-strong)'\">"
    '&larr; Market Dashboard</a>'
)


def add_hub_link(page_html):
    """Prepend the back-to-hub link inside the page's .wrap container. Opens in a new tab,
    matching how the hub opens each point (target=_blank works inside the artifact frame)."""
    marker = '<div class="wrap">'
    if marker not in page_html:
        raise SystemExit('add_hub_link: <div class="wrap"> not found - template changed?')
    return page_html.replace(marker, marker + "\n  " + HUB_LINK_HTML, 1)

"""Shared rendering helpers used by both render_point1_html.py and render_point3_html.py."""


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

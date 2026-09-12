"""Generate the approved dark 3D GitHub contribution dashboard with live data and animated cubes."""
import math
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "itsmeetsharma777")
OUTPUT = Path(os.environ.get("OUTPUT", "assets/contribution-3d.svg"))
TOKEN = os.environ.get("GITHUB_TOKEN")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_days():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required")
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GitHub GraphQL error"))
    return [
        d
        for w in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for d in w["contributionDays"]
    ]


def fallback_days():
    today = date.today()
    return [{"date": (today - timedelta(days=370 - i)).isoformat(), "contributionCount": 0} for i in range(371)]


def streaks(days):
    counts = [int(d["contributionCount"]) for d in days]
    longest = run = 0
    for n in counts:
        if n:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    current = 0
    for n in reversed(counts):
        if n:
            current += 1
        else:
            break
    return longest, current, max(counts, default=0)


def fmt_date(iso):
    return date.fromisoformat(iso).strftime("%B %-d") if iso else ""


try:
    days = fetch_days()
except Exception as exc:
    print(f"Live contribution fetch failed: {exc}", file=sys.stderr)
    days = fallback_days()

days = days[-371:]
while len(days) < 371:
    first = date.fromisoformat(days[0]["date"]) if days else date.today() - timedelta(days=370)
    days.insert(0, {"date": (first - timedelta(days=1)).isoformat(), "contributionCount": 0})

weeks = [days[i:i + 7] for i in range(0, 371, 7)]
max_count = max((int(d["contributionCount"]) for d in days), default=1) or 1
total = sum(int(d["contributionCount"]) for d in days)
longest, current, busiest = streaks(days)

W, H = 1400, 1040
BG, BORDER = "#0d1117", "#30363d"
TEXT, MUTED = "#f0f6fc", "#9aa4b2"
GREEN = "#39d353"
GROUND, GROUND_STROKE = "#26384a", "#172536"
LOW_GREEN, HIGH_GREEN = (18, 105, 58), (64, 245, 92)
HW, HH = 18.0, 9.0
ORIGIN_X, ORIGIN_Y = 190.0, 250.0
MAX_H = 160.0


def rgb(v):
    return f"rgb({int(v[0])},{int(v[1])},{int(v[2])})"


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def color_for(t):
    return mix(LOW_GREEN, HIGH_GREEN, t)


def shade(c, factor):
    return tuple(max(0, min(255, x * factor)) for x in c)


def project(c, r):
    return ORIGIN_X + (c - r) * HW, ORIGIN_Y + (c + r) * HH


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def metric_markup(x, heading_y, heading, value, unit, subtext, value_size=72):
    """Render one metric as a strict three-row component.

    Row 1: heading.
    Row 2: number + unit in one text flow, guaranteeing true adjacency.
    Row 3: supporting text aligned to the exact same left edge as the number.
    """
    value_y = heading_y + 67
    subtext_y = value_y + 38
    return [
        f'<text x="{x}" y="{heading_y}" font-size="25" font-weight="600" fill="{MUTED}">{heading}</text>',
        f'<text x="{x}" y="{value_y}" font-size="{value_size}" font-weight="800" fill="{GREEN}">{value}<tspan dx="18" dy="0" font-size="25" font-weight="700" fill="{TEXT}">{unit}</tspan></text>',
        f'<text x="{x}" y="{subtext_y}" font-size="18" fill="{MUTED}">{subtext}</text>',
    ]


svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif">',
    "<defs>",
    f'<clipPath id="cardClip"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8"/></clipPath>',
    "</defs>",
    f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>',
]

# Four metric areas, deliberately treated as identical UI components.
# Each component has one shared left edge, fixed vertical rhythm, and a
# dedicated supporting-text row so dates/descriptions can never touch values.
right_x = 835
left_x = 60
svg += metric_markup(
    right_x, 65, "1 year total", f"{total:,}", "contributions",
    f"{fmt_date(days[0]['date'])} — {fmt_date(days[-1]['date'])}", 72
)
svg += metric_markup(
    right_x, 230, "Busiest day", busiest, "contributions", "Peak activity", 72
)
svg += metric_markup(
    left_x, 520, "Longest streak", longest, "days", "Consecutive contribution days", 64
)
svg += metric_markup(
    left_x, 684, "Current streak", current, "days", "Ending today", 64
)

svg.append('<g clip-path="url(#cardClip)">')
ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))

for _, r, c, x, y in sorted(ground):
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(
        f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.7"/>'
    )

# Every non-zero contribution becomes its own animated isometric cube.
# Height is derived from live contribution counts; animation changes only
# the cube's vertical scale while the dashboard and ground plane stay fixed.
for _, r, c, x, y in sorted(ground):
    n = int(weeks[c][r]["contributionCount"])
    if n <= 0:
        continue

    t = math.log1p(n) / math.log1p(max_count)
    h = 12.0 + t * MAX_H
    base = color_for(t)
    top = [(0, -HH - h), (HW, -h), (0, HH - h), (-HW, -h)]
    left = [(-HW, 0), (0, HH), (0, HH - h), (-HW, -h)]
    right = [(0, HH), (HW, 0), (HW, -h), (0, HH - h)]
    delay = ((c + r) / 59.0) * 1.6

    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    svg.append(
        f'<g transform="scale(1 0.001)" transform-origin="0 0">'
        f'<polygon points="{poly(left)}" fill="{rgb(shade(base, 0.48))}"/>'
        f'<polygon points="{poly(right)}" fill="{rgb(shade(base, 0.68))}"/>'
        f'<polygon points="{poly(top)}" fill="{rgb(base)}"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="1 0.001;1 1;1 0.001" keyTimes="0;0.5;1" '
        f'dur="5.6s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'</g>'
    )
    svg.append('</g>')

svg.append('</g>')
line_y = 865
svg.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="{BORDER}"/>')
for x in (466, 932):
    svg.append(f'<line x1="{x}" y1="{line_y}" x2="{x}" y2="{H}" stroke="{BORDER}"/>')

cards = [
    (233, "Contributions in the last year", f"{total:,} total", f"{fmt_date(days[0]['date'])} — {fmt_date(days[-1]['date'])}"),
    (699, "Longest streak", f"{longest} days", "Consecutive contribution days"),
    (1166, "Current streak", f"{current} days", "Ending today"),
]
for cx, title, value, sub in cards:
    svg.append(f'<text x="{cx}" y="914" text-anchor="middle" font-size="20" font-weight="600" fill="{MUTED}">{title}</text>')
    svg.append(f'<text x="{cx}" y="969" text-anchor="middle" font-size="44" font-weight="700" fill="{TEXT}">{value}</text>')
    svg.append(f'<text x="{cx}" y="1005" text-anchor="middle" font-size="17" fill="{MUTED}">{sub}</text>')
svg.append('</svg>')
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")

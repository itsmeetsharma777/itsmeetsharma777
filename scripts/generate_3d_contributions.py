"""Generate a GitHub contribution city for the dark GitHub profile theme.

The dashboard keeps the green/yellow-green palette of the supplied reference,
but uses a GitHub-dark canvas, tighter isometric geometry, and aligned stats.
The SVG is self-contained and uses SMIL animations (no JavaScript required).
"""
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
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GitHub GraphQL error"))
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [day for week in calendar["weeks"] for day in week["contributionDays"]]


def fallback_days():
    today = date.today()
    return [
        {"date": (today - timedelta(days=370 - i)).isoformat(), "contributionCount": 0}
        for i in range(371)
    ]


def streaks(days):
    counts = [int(d["contributionCount"]) for d in days]
    longest = current = 0
    run = 0
    for n in counts:
        if n > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    for n in reversed(counts):
        if n > 0:
            current += 1
        else:
            break
    return longest, current, max(counts, default=0)


def fmt_date(iso):
    if not iso:
        return ""
    return date.fromisoformat(iso).strftime("%B %-d")


try:
    days = fetch_days()
except Exception as exc:  # noqa: BLE001
    print(f"Live contribution fetch failed: {exc}", file=sys.stderr)
    days = fallback_days()

days = days[-371:]
while len(days) < 371:
    days.insert(0, {"date": "", "contributionCount": 0})

weeks = [days[i:i + 7] for i in range(0, 371, 7)]
max_count = max((int(d["contributionCount"]) for d in days), default=1) or 1
total = sum(int(d["contributionCount"]) for d in days)
longest, current, busiest = streaks(days)

# ---------------------------------------------------------------------------
# Dark GitHub theme + the reference's yellow-green / forest-green palette.
# ---------------------------------------------------------------------------
W, H = 1400, 1040
BG = "#0d1117"
CARD = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#2f9e32"
GROUND = "#dae784"
GROUND_STROKE = "#c8dc73"
LOW_GREEN = (133, 176, 78)   # #85b04e
HIGH_GREEN = (27, 63, 12)    # #1b3f0c

# Tight geometry keeps every point of the 53 x 7 plane inside the card.
HW, HH = 13.0, 6.5
ORIGIN_X, ORIGIN_Y = 620.0, 430.0
MAX_H = 118.0


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


svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    'font-family="Arial, Helvetica, sans-serif">',
    '<defs>',
    '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
    '<feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/>'
    '<feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '</defs>',
    f'<rect width="{W}" height="{H}" rx="10" fill="{CARD}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="none" stroke="{BORDER}"/>',
]

# Aligned top metrics: labels, large values, units and dates share columns.
svg += [
    '<text x="790" y="70" font-size="24" fill="#8b949e">1 year total</text>',
    f'<text x="790" y="128" font-size="62" font-weight="700" fill="{GREEN}">{total:,}</text>',
    '<text x="1005" y="128" font-size="23" fill="#c9d1d9">contributions</text>',
    f'<text x="1005" y="158" font-size="17" fill="{MUTED}">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
    '<text x="790" y="212" font-size="24" fill="#8b949e">Busiest day</text>',
    f'<text x="790" y="270" font-size="62" font-weight="700" fill="{GREEN}">{busiest}</text>',
    '<text x="1005" y="270" font-size="23" fill="#c9d1d9">contributions</text>',
    '<text x="1005" y="300" font-size="17" fill="#8b949e">Peak activity</text>',
    '<text x="52" y="510" font-size="24" fill="#8b949e">Longest streak</text>',
    f'<text x="52" y="568" font-size="60" font-weight="700" fill="{GREEN}">{longest}</text>',
    '<text x="188" y="568" font-size="23" fill="#c9d1d9">days</text>',
    '<text x="52" y="598" font-size="17" fill="#8b949e">Consecutive contribution days</text>',
    '<text x="52" y="666" font-size="24" fill="#8b949e">Current streak</text>',
    f'<text x="52" y="724" font-size="60" font-weight="700" fill="{GREEN}">{current}</text>',
    '<text x="188" y="724" font-size="23" fill="#c9d1d9">days</text>',
    '<text x="52" y="754" font-size="17" fill="#8b949e">Ending today</text>',
]

# Ground plane: the complete heatmap is deliberately bounded inside the SVG.
ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))

ground.sort()
for _, r, c, x, y in ground:
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(
        f'<polygon points="{poly(top)}" fill="{GROUND}" '
        f'stroke="{GROUND_STROKE}" stroke-width="0.65" opacity="0.98"/>'
    )

# Contribution buildings rise in a diagonal wave, clipped by the card bounds.
for _, r, c, x, y in ground:
    n = int(weeks[c][r]["contributionCount"])
    t = math.log1p(n) / math.log1p(max_count) if n else 0
    h = 3.0 if n == 0 else 8.0 + t * MAX_H
    top = [(x, y - HH - h), (x + HW, y - h), (x, y + HH - h), (x - HW, y - h)]
    left = [(x - HW, y), (x, y + HH), (x, y + HH - h), (x - HW, y - h)]
    right = [(x, y + HH), (x + HW, y), (x + HW, y - h), (x, y + HH - h)]
    cbase = color_for(t)
    delay = 0.15 + ((c + r) / 58.0) * 2.6
    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    svg.append(
        '<animateTransform attributeName="transform" type="scale" '
        'values="1 0;1 1;1 1" keyTimes="0;0.20;1" dur="13s" '
        f'begin="{delay:.2f}s" repeatCount="indefinite" fill="freeze"/>'
    )
    svg.append(f'<g transform="translate({-x:.1f},{-y:.1f})">')
    svg.append(f'<polygon points="{poly(left)}" fill="{rgb(shade(cbase, 0.55))}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{rgb(shade(cbase, 0.72))}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{rgb(cbase)}"/>')
    if t > 0.72:
        svg.append(
            f'<polygon points="{poly(top)}" fill="none" stroke="#5b9f32" '
            'stroke-width="1.8" opacity="0.20">'
            '<animate attributeName="opacity" values="0.12;0.50;0.12" '
            'dur="2.8s" repeatCount="indefinite"/></polygon>'
        )
    svg.append('</g></g>')

# Bottom cards are aligned to a fixed three-column grid.
line_y = 865
svg.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="{BORDER}"/>')
for x in (466.7, 933.3):
    svg.append(f'<line x1="{x:.1f}" y1="{line_y}" x2="{x:.1f}" y2="{H}" stroke="{BORDER}"/>')

cards = [
    (233.3, "Contributions in the last year", f"{total:,} total", f"{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}"),
    (700.0, "Longest streak", f"{longest} days", "Consecutive contribution days"),
    (1166.7, "Current streak", f"{current} days", "Ending today"),
]
for cx, title, value, sub in cards:
    svg.append(f'<text x="{cx:.1f}" y="916" text-anchor="middle" font-size="19" fill="#8b949e">{title}</text>')
    svg.append(f'<text x="{cx:.1f}" y="970" text-anchor="middle" font-size="40" fill="#c9d1d9">{value}</text>')
    svg.append(f'<text x="{cx:.1f}" y="1004" text-anchor="middle" font-size="16" fill="#8b949e">{sub}</text>')

svg.append('</svg>')
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")

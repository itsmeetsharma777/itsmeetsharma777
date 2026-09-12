"""Generate a dark, reference-style 3D GitHub contribution dashboard."""
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
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return days


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
    busiest = max(counts, default=0)
    return longest, current, busiest


def fmt_date(iso):
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    return d.strftime("%B %-d")


try:
    days = fetch_days()
except Exception as exc:  # noqa: BLE001
    print(f"Live contribution fetch failed: {exc}", file=sys.stderr)
    days = fallback_days()

# Always render a complete 53-week x 7-day calendar. GitHub may return a
# partial current week, so pad to the most recent 371 calendar days.
days = days[-371:]
while len(days) < 371:
    first = date.fromisoformat(days[0]["date"]) if days and days[0].get("date") else date.today() - timedelta(days=370)
    days.insert(0, {"date": (first - timedelta(days=1)).isoformat(), "contributionCount": 0})

weeks = [days[i:i + 7] for i in range(0, 371, 7)]
max_count = max((int(d["contributionCount"]) for d in days), default=1) or 1
total = sum(int(d["contributionCount"]) for d in days)
longest, current, busiest = streaks(days)

# Dark GitHub canvas + the exact green family requested from the reference.
W, H = 1400, 1040
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
GREEN = "#238b24"
GROUND = "#dae784"
GROUND_STROKE = "#c8dc73"
LOW_GREEN = (133, 176, 78)
HIGH_GREEN = (27, 63, 12)

# Compact isometric geometry. The previous 17px tiles made the 53-week plane
# wider than the card; these dimensions keep the entire city safely inside it.
HW, HH = 12.5, 6.25
ORIGIN_X, ORIGIN_Y = 700.0, 438.0
MAX_H = 112.0


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
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">',
    '<defs>',
    '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    f'<clipPath id="cardClip"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8"/></clipPath>',
    '</defs>',
    f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>',
]

# Precisely aligned header statistics.
svg += [
    f'<text x="830" y="66" font-size="22" fill="{MUTED}">1 year total</text>',
    f'<text x="830" y="126" font-size="62" font-weight="700" fill="{GREEN}">{total:,}</text>',
    f'<text x="1045" y="126" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1045" y="157" font-size="16" fill="{MUTED}">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
    f'<text x="830" y="215" font-size="22" fill="{MUTED}">Busiest day</text>',
    f'<text x="830" y="275" font-size="62" font-weight="700" fill="{GREEN}">{busiest}</text>',
    f'<text x="1045" y="275" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1045" y="306" font-size="16" fill="{MUTED}">Peak activity</text>',
    f'<text x="54" y="515" font-size="22" fill="{MUTED}">Longest streak</text>',
    f'<text x="54" y="574" font-size="60" font-weight="700" fill="{GREEN}">{longest}</text>',
    f'<text x="190" y="574" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="54" y="604" font-size="16" fill="{MUTED}">Consecutive contribution days</text>',
    f'<text x="54" y="673" font-size="22" fill="{MUTED}">Current streak</text>',
    f'<text x="54" y="732" font-size="60" font-weight="700" fill="{GREEN}">{current}</text>',
    f'<text x="190" y="732" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="54" y="762" font-size="16" fill="{MUTED}">Ending today</text>',
]

# Ground plane and city are clipped to the dashboard boundary.
svg.append('<g clip-path="url(#cardClip)">')

ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))

ground.sort()
for _, r, c, x, y in ground:
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.65" opacity="0.98"/>')

# Build each cell in local coordinates so scale(1,0) collapses it at its
# base rather than scaling the whole SVG. This fixes the invisible-city bug.
for _, r, c, x, y in ground:
    n = int(weeks[c][r]["contributionCount"])
    t = math.log1p(n) / math.log1p(max_count) if n else 0
    h = 3.0 if n == 0 else 8.0 + t * MAX_H

    top = [(0, -HH - h), (HW, -h), (0, HH - h), (-HW, -h)]
    left = [(-HW, 0), (0, HH), (0, HH - h), (-HW, -h)]
    right = [(0, HH), (HW, 0), (HW, -h), (0, HH - h)]

    cbase = color_for(t)
    delay = 0.15 + ((c + r) / 58.0) * 2.6

    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    svg.append(
        '<g transform="scale(1 1)">'
        '<animateTransform attributeName="transform" type="scale" '
        'values="1 0;1 1;1 1" keyTimes="0;0.22;1" dur="11s" '
        f'begin="{delay:.2f}s" repeatCount="indefinite"/>'
    )
    svg.append(f'<polygon points="{poly(left)}" fill="{rgb(shade(cbase, 0.55))}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{rgb(shade(cbase, 0.72))}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{rgb(cbase)}"/>')
    if t > 0.72:
        svg.append(
            f'<polygon points="{poly(top)}" fill="none" stroke="#5b9f32" stroke-width="1.8" opacity="0.22">'
            '<animate attributeName="opacity" values="0.10;0.50;0.10" dur="2.8s" repeatCount="indefinite"/>'
            '</polygon>'
        )
    svg.append('</g></g>')

svg.append('</g>')

# Bottom summary cards: equal widths and perfectly centered text.
line_y = 865
svg.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="{BORDER}"/>')
for x in (466, 932):
    svg.append(f'<line x1="{x}" y1="{line_y}" x2="{x}" y2="{H}" stroke="{BORDER}"/>')

cards = [
    (233, "Contributions in the last year", f"{total:,} total", f"{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}"),
    (699, "Longest streak", f"{longest} days", "Consecutive contribution days"),
    (1166, "Current streak", f"{current} days", "Ending today"),
]
for cx, title, value, sub in cards:
    svg.append(f'<text x="{cx}" y="914" text-anchor="middle" font-size="18" fill="{MUTED}">{title}</text>')
    svg.append(f'<text x="{cx}" y="967" text-anchor="middle" font-size="40" fill="{TEXT}">{value}</text>')
    svg.append(f'<text x="{cx}" y="1001" text-anchor="middle" font-size="15" fill="{MUTED}">{sub}</text>')

svg.append('</svg>')
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")

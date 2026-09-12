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
    return [day for week in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for day in week["contributionDays"]]


def fallback_days():
    today = date.today()
    return [{"date": (today - timedelta(days=370 - i)).isoformat(), "contributionCount": 0} for i in range(371)]


def streaks(days):
    counts = [int(d["contributionCount"]) for d in days]
    longest = run = 0
    for n in counts:
        if n > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    current = 0
    for n in reversed(counts):
        if n > 0:
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
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
GREEN = "#238b24"
GROUND = "#dae784"
GROUND_STROKE = "#c8dc73"
LOW_GREEN = (133, 176, 78)
HIGH_GREEN = (27, 63, 12)

# The full 53x7 city is intentionally compact and centered.
HW, HH = 10.5, 5.25
ORIGIN_X, ORIGIN_Y = 700.0, 448.0
MAX_H = 88.0


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
    '<clipPath id="cardClip"><rect x="2" y="2" width="1396" height="1036" rx="8"/></clipPath>',
    '</defs>',
    f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>',
]

# Aligned statistics: labels, values and units share fixed columns.
svg += [
    f'<text x="810" y="66" font-size="22" fill="{MUTED}">1 year total</text>',
    f'<text x="810" y="126" font-size="62" font-weight="700" fill="{GREEN}">{total:,}</text>',
    f'<text x="1025" y="126" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1025" y="157" font-size="16" fill="{MUTED}">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
    f'<text x="810" y="215" font-size="22" fill="{MUTED}">Busiest day</text>',
    f'<text x="810" y="275" font-size="62" font-weight="700" fill="{GREEN}">{busiest}</text>',
    f'<text x="1025" y="275" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1025" y="306" font-size="16" fill="{MUTED}">Peak activity</text>',
    f'<text x="54" y="515" font-size="22" fill="{MUTED}">Longest streak</text>',
    f'<text x="54" y="574" font-size="60" font-weight="700" fill="{GREEN}">{longest}</text>',
    f'<text x="190" y="574" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="54" y="604" font-size="16" fill="{MUTED}">Consecutive contribution days</text>',
    f'<text x="54" y="673" font-size="22" fill="{MUTED}">Current streak</text>',
    f'<text x="54" y="732" font-size="60" font-weight="700" fill="{GREEN}">{current}</text>',
    f'<text x="190" y="732" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="54" y="762" font-size="16" fill="{MUTED}">Ending today</text>',
]

svg.append('<g clip-path="url(#cardClip)">')

# Draw the pale isometric floor first.
ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))
for _, r, c, x, y in sorted(ground):
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.55"/>')

# IMPORTANT: render every contribution block statically so GitHub always shows
# the city, then add a subtle opacity/translate animation that cannot hide it.
for _, r, c, x, y in sorted(ground):
    n = int(weeks[c][r]["contributionCount"])
    t = math.log1p(n) / math.log1p(max_count) if n else 0
    if n == 0:
        continue
    h = 10.0 + t * MAX_H
    base = color_for(t)
    top = [(x, y - HH - h), (x + HW, y - h), (x, y + HH - h), (x - HW, y - h)]
    left = [(x - HW, y), (x, y + HH), (x, y + HH - h), (x - HW, y - h)]
    right = [(x, y + HH), (x + HW, y), (x + HW, y - h), (x, y + HH - h)]
    delay = 0.08 + ((c + r) / 59.0) * 1.8
    # Static geometry + animated group opacity/translation. No scale(1,0),
    # because that was the reason the previous GitHub rendering looked empty.
    svg.append(f'<g opacity="1">')
    svg.append(f'<g transform="translate(0 0)"><animateTransform attributeName="transform" type="translate" values="0 12;0 0;0 0" keyTimes="0;0.20;1" dur="8s" begin="{delay:.2f}s" repeatCount="indefinite"/>')
    svg.append(f'<polygon points="{poly(left)}" fill="{rgb(shade(base, 0.52))}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{rgb(shade(base, 0.70))}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{rgb(base)}"/>')
    svg.append('</g></g>')

svg.append('</g>')

# Bottom cards are equally sized and centered.
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

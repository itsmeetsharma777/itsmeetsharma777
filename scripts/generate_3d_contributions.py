"""Generate a centered, dark 3D GitHub contribution dashboard."""
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
    return [d for w in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]


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
TEXT, MUTED = "#f0f6fc", "#8b949e"
GREEN = "#238b24"
GROUND, GROUND_STROKE = "#dae784", "#c8dc73"
LOW_GREEN, HIGH_GREEN = (133, 176, 78), (27, 63, 12)

# Large centered 53 x 7 city. The previous origin placed almost the whole
# plane on the right; this origin centers its full bounding box in the card.
HW, HH = 15.5, 7.75
ORIGIN_X, ORIGIN_Y = 350.0, 410.0
MAX_H = 150.0


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
    "<defs>",
    f'<clipPath id="cardClip"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8"/></clipPath>',
    "</defs>",
    f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>',
]

# Balanced header statistics.
svg += [
    f'<text x="835" y="65" font-size="22" fill="{MUTED}">1 year total</text>',
    f'<text x="835" y="125" font-size="62" font-weight="700" fill="{GREEN}">{total:,}</text>',
    f'<text x="1050" y="125" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1050" y="156" font-size="16" fill="{MUTED}">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
    f'<text x="835" y="214" font-size="22" fill="{MUTED}">Busiest day</text>',
    f'<text x="835" y="274" font-size="62" font-weight="700" fill="{GREEN}">{busiest}</text>',
    f'<text x="1050" y="274" font-size="22" fill="{TEXT}">contributions</text>',
    f'<text x="1050" y="305" font-size="16" fill="{MUTED}">Peak activity</text>',
    f'<text x="60" y="520" font-size="22" fill="{MUTED}">Longest streak</text>',
    f'<text x="60" y="579" font-size="60" font-weight="700" fill="{GREEN}">{longest}</text>',
    f'<text x="198" y="579" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="60" y="609" font-size="16" fill="{MUTED}">Consecutive contribution days</text>',
    f'<text x="60" y="678" font-size="22" fill="{MUTED}">Current streak</text>',
    f'<text x="60" y="737" font-size="60" font-weight="700" fill="{GREEN}">{current}</text>',
    f'<text x="198" y="737" font-size="22" fill="{TEXT}">days</text>',
    f'<text x="60" y="767" font-size="16" fill="{MUTED}">Ending today</text>',
]

svg.append('<g clip-path="url(#cardClip)">')

# Draw the large pale floor first.
ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))
for _, r, c, x, y in sorted(ground):
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.65"/>')

# Each building is defined around its own ground point. Scaling only the local
# Y axis therefore makes the building genuinely rise from its base to full
# height, then return to the ground, smoothly and continuously.
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
        '<g transform="scale(1 1)" transform-origin="0 0">'
        '<animateTransform attributeName="transform" type="scale" '
        'values="1 0;1 1;1 0" keyTimes="0;0.46;1" dur="6s" '
        f'begin="{delay:.2f}s" repeatCount="indefinite"/>'
    )
    svg.append(f'<polygon points="{poly(left)}" fill="{rgb(shade(base, 0.52))}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{rgb(shade(base, 0.70))}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{rgb(base)}"/>')
    svg.append('</g></g>')

svg.append('</g>')

# Three equal-width summary cards.
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

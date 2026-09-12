"""Generate a GitHub contribution city in the clean green 3D style of the reference.

The SVG is self-contained, uses real GitHub contribution data, and uses SMIL
animations so the blocks rise in a staggered wave without JavaScript.
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

days = days[-371:]
while len(days) < 371:
    days.insert(0, {"date": "", "contributionCount": 0})

weeks = [days[i:i + 7] for i in range(0, 371, 7)]
max_count = max((int(d["contributionCount"]) for d in days), default=1) or 1
total = sum(int(d["contributionCount"]) for d in days)
longest, current, busiest = streaks(days)

# ---------------------------------------------------------------------------
# Reference palette: white canvas + lime/yellow-green plane + deep forest
# green blocks. These values are deliberately much closer to the supplied
# screenshot than the previous generic GitHub-green palette.
# ---------------------------------------------------------------------------
W, H = 1400, 1040
BG = "#ffffff"
TEXT = "#3a3a3a"
MUTED = "#777777"
GREEN = "#238b24"
GROUND = "#dae784"
GROUND_STROKE = "#c8dc73"
LOW_GREEN = (133, 176, 78)   # #85b04e
HIGH_GREEN = (27, 63, 12)    # #1b3f0c

HW, HH = 17.0, 8.5
ORIGIN_X, ORIGIN_Y = 610.0, 470.0
MAX_H = 125.0


def rgb(v):
    return f"rgb({int(v[0])},{int(v[1])},{int(v[2])})"


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def color_for(t):
    # Low -> high contribution follows the reference's yellow-green to
    # saturated/deep forest-green progression.
    return mix(LOW_GREEN, HIGH_GREEN, t)


def shade(c, factor):
    return tuple(max(0, min(255, x * factor)) for x in c)


def project(c, r):
    x = ORIGIN_X + (c - r) * HW
    y = ORIGIN_Y + (c + r) * HH
    return x, y


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
    f'<rect width="{W}" height="{H}" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="#dedede"/>',
]

svg += [
    '<text x="850" y="78" font-size="25" fill="#555">1 year total</text>',
    f'<text x="805" y="138" font-size="64" font-weight="700" fill="{GREEN}">{total:,}</text>',
    '<text x="1035" y="138" font-size="25" fill="#555">contributions</text>',
    f'<text x="1035" y="170" font-size="19" fill="{MUTED}">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
    '<text x="855" y="235" font-size="25" fill="#555">Busiest day</text>',
    f'<text x="915" y="300" font-size="64" font-weight="700" fill="{GREEN}">{busiest}</text>',
    '<text x="1035" y="300" font-size="25" fill="#555">contributions</text>',
    f'<text x="1035" y="332" font-size="19" fill="{MUTED}">Peak activity</text>',
    '<text x="38" y="520" font-size="25" fill="#555">Longest streak</text>',
    f'<text x="55" y="590" font-size="62" font-weight="700" fill="{GREEN}">{longest}</text>',
    '<text x="210" y="590" font-size="25" fill="#555">days</text>',
    '<text x="55" y="622" font-size="19" fill="#888">Consecutive contribution days</text>',
    '<text x="38" y="690" font-size="25" fill="#555">Current streak</text>',
    f'<text x="55" y="760" font-size="62" font-weight="700" fill="{GREEN}">{current}</text>',
    '<text x="210" y="760" font-size="25" fill="#555">days</text>',
    '<text x="55" y="792" font-size="19" fill="#888">Ending today</text>',
]

ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))

ground.sort()
for _, r, c, x, y in ground:
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.8"/>')

for _, r, c, x, y in ground:
    n = int(weeks[c][r]["contributionCount"])
    t = math.log1p(n) / math.log1p(max_count) if n else 0
    h = 4 if n == 0 else 10 + t * MAX_H
    top = [(x, y - HH - h), (x + HW, y - h), (x, y + HH - h), (x - HW, y - h)]
    left = [(x - HW, y), (x, y + HH), (x, y + HH - h), (x - HW, y - h)]
    right = [(x, y + HH), (x + HW, y), (x + HW, y - h), (x, y + HH - h)]
    cbase = color_for(t)
    top_fill = rgb(cbase)
    left_fill = rgb(shade(cbase, 0.55))
    right_fill = rgb(shade(cbase, 0.72))
    delay = 0.2 + ((c + r) / 58.0) * 3.0
    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    svg.append(
        '<animateTransform attributeName="transform" type="scale" '
        'values="1 0;1 1;1 1" keyTimes="0;0.20;1" dur="14s" '
        f'begin="{delay:.2f}s" repeatCount="indefinite" fill="freeze"/>'
    )
    svg.append(f'<g transform="translate({-x:.1f},{-y:.1f})">')
    svg.append(f'<polygon points="{poly(left)}" fill="{left_fill}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{right_fill}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{top_fill}"/>')
    if t > 0.72:
        svg.append(
            f'<polygon points="{poly(top)}" fill="none" stroke="#5b9f32" stroke-width="2" filter="url(#soft)" opacity="0.25">'
            '<animate attributeName="opacity" values="0.15;0.55;0.15" dur="2.8s" repeatCount="indefinite"/>'
            '</polygon>'
        )
    svg.append('</g></g>')

line_y = 875
svg.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="#dddddd"/>')
for x in (466, 932):
    svg.append(f'<line x1="{x}" y1="{line_y}" x2="{x}" y2="{H}" stroke="#dddddd"/>')

cards = [
    (233, "Contributions in the last year", f"{total:,} total", f"{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}"),
    (699, "Longest streak", f"{longest} days", "Consecutive contribution days"),
    (1166, "Current streak", f"{current} days", "Ending today"),
]
for cx, title, value, sub in cards:
    svg.append(f'<text x="{cx}" y="925" text-anchor="middle" font-size="20" fill="#555">{title}</text>')
    svg.append(f'<text x="{cx}" y="980" text-anchor="middle" font-size="42" fill="#333">{value}</text>')
    svg.append(f'<text x="{cx}" y="1014" text-anchor="middle" font-size="17" fill="#888">{sub}</text>')

svg.append('</svg>')
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")

"""Generate the premium dark isometric GitHub contribution city with live data."""
import html
import math
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "itsmeetsharma777")
OUTPUT = Path(os.environ.get("OUTPUT", "assets/contribution-3d.svg"))
TOKEN = os.environ.get("GITHUB_TOKEN")

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def validate_days(days):
    if len(days) < 300:
        raise RuntimeError(f"GitHub returned an incomplete contribution calendar ({len(days)} days)")
    return days


def fetch_graphql_days():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is unavailable")
    today = date.today()
    start = today - timedelta(days=370)
    variables = {
        "login": USERNAME,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{today.isoformat()}T23:59:59Z",
    }
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": variables},
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GitHub GraphQL error"))
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return validate_days([d for w in calendar["weeks"] for d in w["contributionDays"]])


def fetch_public_graph_days():
    """Fallback to GitHub's public contribution calendar HTML."""
    url = f"https://github.com/users/{USERNAME}/contributions"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 contribution-dashboard"}, timeout=30)
    r.raise_for_status()
    pattern = re.compile(
        r'<td\b[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>(.*?)</td>',
        re.DOTALL,
    )
    days = []
    for iso, cell in pattern.findall(r.text):
        text = html.unescape(re.sub(r"<[^>]+>", " ", cell))
        match = re.search(r"(\d[\d,]*) contributions?", text)
        count = int(match.group(1).replace(",", "")) if match else 0
        days.append({"date": iso, "contributionCount": count})
    return validate_days(days)


def fetch_days():
    try:
        days = fetch_graphql_days()
        print(f"Fetched {len(days)} days from GitHub GraphQL")
        return days
    except Exception as graphql_error:
        print(f"GraphQL fetch failed: {graphql_error}", file=sys.stderr)
        try:
            days = fetch_public_graph_days()
            print(f"Fetched {len(days)} days from GitHub public contribution graph")
            return days
        except Exception as public_error:
            raise RuntimeError(
                f"Unable to fetch a real contribution calendar. GraphQL: {graphql_error}; public graph: {public_error}"
            ) from public_error


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
    if not iso:
        return ""
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %d").replace(" 0", " ")


days = fetch_days()[-371:]
while len(days) < 371:
    first = date.fromisoformat(days[0]["date"]) if days else date.today() - timedelta(days=370)
    days.insert(0, {"date": (first - timedelta(days=1)).isoformat(), "contributionCount": 0})

weeks = [days[i:i + 7] for i in range(0, 371, 7)]
max_count = max((int(d["contributionCount"]) for d in days), default=1) or 1
total = sum(int(d["contributionCount"]) for d in days)
longest, current, busiest = streaks(days)

W, H = 1400, 1040
BG, BORDER = "#0b1117", "#26313d"
TEXT, MUTED = "#f0f6fc", "#9aa8b8"
GREEN = "#39e75f"
GROUND, GROUND_STROKE = "#354a60", "#1a2a3a"
PALETTE = [
    (6, 70, 35),
    (8, 105, 43),
    (10, 145, 50),
    (17, 188, 61),
    (36, 225, 76),
    (67, 246, 91),
    (118, 255, 124),
]
HW, HH = 16.5, 8.25
ORIGIN_X, ORIGIN_Y = 150.0, 245.0
MAX_H = 172.0


def rgb(v):
    return f"rgb({int(v[0])},{int(v[1])},{int(v[2])})"


def shade(c, factor):
    return tuple(max(0, min(255, x * factor)) for x in c)


def project(c, r):
    return ORIGIN_X + (c - r) * HW, ORIGIN_Y + (c + r) * HH


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def metric_markup(x, heading_y, heading, value, unit, subtext, value_size=72):
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
    '<filter id="cubeGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '<filter id="softShadow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="2.2"/></filter>',
    "</defs>",
    f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>',
]

right_x = 835
left_x = 60
svg += metric_markup(right_x, 65, "1 year total", f"{total:,}", "contributions", f"{fmt_date(days[0]['date'])} — {fmt_date(days[-1]['date'])}", 72)
svg += metric_markup(right_x, 230, "Busiest day", busiest, "contributions", "Peak activity", 72)
svg += metric_markup(left_x, 520, "Longest streak", longest, "days", "Consecutive contribution days", 64)
svg += metric_markup(left_x, 684, "Current streak", current, "days", "Ending today", 64)

svg.append('<g clip-path="url(#cardClip)">')
# The floor is deliberately compact and fully tiled so the city reads as one
# continuous isometric board instead of a long empty strip.
ground = []
for c in range(53):
    for r in range(7):
        x, y = project(c, r)
        ground.append((c + r, r, c, x, y))

for _, r, c, x, y in sorted(ground):
    top = [(x, y - HH), (x + HW, y), (x, y + HH), (x - HW, y)]
    svg.append(f'<polygon points="{poly(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.75"/>')

counts = [[int(weeks[c][r]["contributionCount"]) for r in range(7)] for c in range(53)]
# A small local field keeps the 3D city visually continuous while preserving
# the real contribution values as the dominant signal for height and color.
for _, r, c, x, y in sorted(ground):
    n = counts[c][r]
    t = math.log1p(n) / math.log1p(max_count) if n else 0.0

    weighted_sum = 0.0
    weight_total = 0.0
    for dc in range(-3, 4):
        for dr in range(-2, 3):
            cc, rr = c + dc, r + dr
            if 0 <= cc < 53 and 0 <= rr < 7:
                dist = abs(dc) + abs(dr)
                if dist == 0:
                    continue
                weight = 1.0 / (1.0 + dist * 1.15)
                weighted_sum += math.log1p(counts[cc][rr]) / math.log1p(max_count) * weight
                weight_total += weight
    field = weighted_sum / weight_total if weight_total else 0.0

    # Every tile gets a short cube, while real activity controls the taller
    # towers. This matches the dense reference-city look without inventing stats.
    visual_t = max(0.055, t, field * 0.92)
    h = 7.0 + visual_t * MAX_H

    palette_index = min(len(PALETTE) - 1, int(visual_t * (len(PALETTE) - 1)))
    base = PALETTE[palette_index]

    top = [(0, -HH - h), (HW, -h), (0, HH - h), (-HW, -h)]
    left = [(-HW, 0), (0, HH), (0, HH - h), (-HW, -h)]
    right = [(0, HH), (HW, 0), (HW, -h), (0, HH - h)]

    if visual_t > 0.14:
        svg.append(f'<ellipse cx="{x:.1f}" cy="{y + 2:.1f}" rx="13" ry="5" fill="#020806" opacity="0.34" filter="url(#softShadow)"/>')

    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    if visual_t > 0.56:
        svg.append('<g filter="url(#cubeGlow)">')
    svg.append(f'<polygon points="{poly(left)}" fill="{rgb(shade(base, 0.36))}"/>')
    svg.append(f'<polygon points="{poly(right)}" fill="{rgb(shade(base, 0.61))}"/>')
    svg.append(f'<polygon points="{poly(top)}" fill="{rgb(base)}" stroke="{rgb(shade(base, 1.08))}" stroke-width="0.35"/>')
    if visual_t > 0.56:
        svg.append('</g>')
    svg.append('</g>')

svg.append('</g>')
line_y = 865
svg.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="{BORDER}"/>')
for x in (466, 932):
    svg.append(f'<line x1="{x}" y1="{line_y}" x2="{x}" y2="{H}" stroke="{BORDER}"/>')

cards = [
    (233, "Contributions in the last year", f"{total:,}", "total", f"{fmt_date(days[0]['date'])} — {fmt_date(days[-1]['date'])}"),
    (699, "Longest streak", f"{longest}", "days", "Consecutive contribution days"),
    (1166, "Current streak", f"{current}", "days", "Ending today"),
]
for cx, title, value, unit, sub in cards:
    svg.append(f'<text x="{cx}" y="914" text-anchor="middle" font-size="20" font-weight="600" fill="{MUTED}">{title}</text>')
    svg.append(f'<text x="{cx}" y="969" text-anchor="middle" font-size="44" font-weight="800" fill="{GREEN}">{value}<tspan dx="18" dy="0" font-size="24" font-weight="700" fill="{TEXT}">{unit}</tspan></text>')
    svg.append(f'<text x="{cx}" y="1005" text-anchor="middle" font-size="17" fill="{MUTED}">{sub}</text>')
svg.append('</svg>')
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")

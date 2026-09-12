"""
Generate a fully animated, vector (SVG) isometric 3D "contribution city" —
the same style popularized by yoshi389111/github-profile-3d-contrib: each
day is a block on a true isometric diamond grid (not a front-facing bar
chart), rising out of a tilted ground plane.

Why SVG instead of GIF:
  - Pure vector shapes animated with native SMIL <animate> /
    <animateTransform>. The browser (and GitHub's own image renderer)
    animates it directly at 60fps with no JavaScript and a tiny file size,
    so it plays smoothly with zero lag anywhere the image is embedded.

Animation:
  - Buildings rise out of the ground in a diagonal wave (back corner first)
  - The whole city gently rocks side to side, like a slow turntable
  - The tallest/most-active buildings keep a soft glowing pulse

Output: assets/contribution-3d.svg
"""
import math
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "itsmeetsharma777")
OUT = Path(os.environ.get("OUTPUT", "assets/contribution-3d.svg"))
OUT.parent.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def fetch_data():
    import requests

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
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        days.extend(week["contributionDays"])
    return days, cal["totalContributions"]


def sample_data():
    """Deterministic, good-looking placeholder data so the SVG renders
    immediately after upload, before the workflow has run once with a
    real token."""
    today = date.today()
    days = []
    total = 0
    for i in range(371):
        d = today - timedelta(days=370 - i)
        wd = d.weekday()
        base = 0.55 + 0.45 * math.sin(i / 9.0) + 0.3 * math.sin(i / 47.0 + 1.3)
        weekday_bias = 0.35 if wd >= 5 else 1.0
        n = max(0.0, base) * weekday_bias
        count = int(round(n * 9))
        if (i * 37) % 101 < 6:
            count = 0
        if (i * 53) % 131 < 4:
            count += 11
        total += count
        days.append({"date": d.isoformat(), "contributionCount": count})
    return days, total


try:
    days, total = fetch_data()
except Exception as exc:  # noqa: BLE001
    print(f"Live contribution fetch skipped/failed: {exc}", file=sys.stderr)
    days, total = sample_data()

days = days[-371:]
max_count = max((d["contributionCount"] for d in days), default=1) or 1

# arrange as 53 columns x 7 rows (Sun..Sat), oldest -> newest
weeks = []
for i in range(0, len(days), 7):
    chunk = days[i:i + 7]
    if len(chunk) == 7:
        weeks.append(chunk)
while len(weeks) < 53:
    weeks.insert(0, [{"date": "", "contributionCount": 0} for _ in range(7)])
weeks = weeks[-53:]
COLS, ROWS = 53, 7

# ---- palette --------------------------------------------------------------
BG_TOP = "#0b0716"
BG_BOTTOM = "#150a24"
MUTED = "#a68fd1"
EMPTY_TOP = "#2a1d40"
EMPTY_LEFT = "#1c1430"
EMPTY_RIGHT = "#231a38"

STOPS = [
    (0.00, (124, 58, 245)),   # violet
    (0.25, (219, 66, 214)),   # magenta
    (0.50, (244, 63, 94)),    # rose/red
    (0.72, (249, 146, 47)),   # orange
    (1.00, (45, 219, 154)),   # green
]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def gradient(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(STOPS) - 1):
        p1, c1 = STOPS[i]
        p2, c2 = STOPS[i + 1]
        if t <= p2:
            return lerp(c1, c2, (t - p1) / (p2 - p1))
    return STOPS[-1][1]


def rgb(c):
    return f"rgb({int(c[0])},{int(c[1])},{int(c[2])})"


def shade(c, f):
    return tuple(max(0, min(255, v * f)) for v in c)


def fmt(v):
    return f"{v:.1f}"


# ---- isometric projection --------------------------------------------------
HALF_W = 13.0   # half tile width
HALF_H = 6.5    # half tile height (2:1 classic isometric ratio)
MAX_BLOCK_H = 108.0
MIN_BLOCK_H = 5.0

buildings = []
min_x = min_top_y = math.inf
max_x = max_ground_y = -math.inf

for c in range(COLS):
    for r in range(ROWS):
        count = weeks[c][r]["contributionCount"]
        x0 = (c - r) * HALF_W
        y0 = (c + r) * HALF_H
        t = 0.0 if count == 0 else math.log1p(count) / math.log1p(max_count)
        h = MIN_BLOCK_H if count == 0 else 10 + t * MAX_BLOCK_H

        n0 = (x0, y0 - HALF_H)
        e0 = (x0 + HALF_W, y0)
        s0 = (x0, y0 + HALF_H)
        w0 = (x0 - HALF_W, y0)
        n1 = (x0, y0 - HALF_H - h)
        e1 = (x0 + HALF_W, y0 - h)
        s1 = (x0, y0 + HALF_H - h)
        w1 = (x0 - HALF_W, y0 - h)

        min_x = min(min_x, w0[0])
        max_x = max(max_x, e0[0])
        min_top_y = min(min_top_y, n1[1])
        max_ground_y = max(max_ground_y, s0[1])

        buildings.append(
            {
                "c": c, "r": r, "count": count, "t": t, "depth": c + r,
                "top": [n1, e1, s1, w1],
                "left": [w0, s0, s1, w1],
                "right": [s0, e0, e1, s1],
                "pivot": s0,  # ground point used as the "grow from here" anchor
            }
        )

CITY_W = max_x - min_x
CITY_H = max_ground_y - min_top_y
MARGIN = 40
TITLE_H = 78
LEGEND_H = 56

OFF_X = -min_x + MARGIN
OFF_Y = -min_top_y + TITLE_H

W = int(CITY_W + MARGIN * 2)
H = int(CITY_H + TITLE_H + LEGEND_H + MARGIN)


def shift(p):
    return (p[0] + OFF_X, p[1] + OFF_Y)


def pts(poly):
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (shift(p) for p in poly))


svg = []
svg.append(
    f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="Segoe UI, Verdana, Helvetica, Arial, sans-serif">'
)

# ---- defs -------------------------------------------------------------
svg.append("<defs>")
svg.append(
    f'<linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG_TOP}"/>'
    f'<stop offset="1" stop-color="{BG_BOTTOM}"/>'
    f'</linearGradient>'
)
svg.append(
    '<linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#c084fc">'
    '<animate attributeName="stop-color" values="#c084fc;#f472b6;#fb923c;#c084fc" dur="6s" repeatCount="indefinite"/>'
    '</stop>'
    '<stop offset="1" stop-color="#f472b6">'
    '<animate attributeName="stop-color" values="#f472b6;#fb923c;#c084fc;#f472b6" dur="6s" repeatCount="indefinite"/>'
    '</stop>'
    '</linearGradient>'
)
svg.append(
    '<linearGradient id="legendGrad" x1="0" y1="0" x2="1" y2="0">'
    + "".join(f'<stop offset="{p}" stop-color="{rgb(c)}"/>' for p, c in STOPS)
    + '</linearGradient>'
)
svg.append(
    '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">'
    '<feGaussianBlur stdDeviation="3.6" result="blur"/>'
    '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
    '</filter>'
)
svg.append("</defs>")

# ---- background -------------------------------------------------------------
svg.append(f'<rect width="{W}" height="{H}" rx="26" fill="url(#bgGrad)"/>')
svg.append(
    f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="24" '
    f'fill="none" stroke="#3b1f63" stroke-width="1.5" opacity="0.8"/>'
)

rnd = random.Random(7)
for i in range(22):
    px = rnd.uniform(20, W - 20)
    py = rnd.uniform(20, H - 20)
    r = rnd.uniform(0.8, 2.0)
    dur = rnd.uniform(2.2, 4.5)
    delay = rnd.uniform(0, 3)
    color = rgb(gradient(rnd.random()))
    svg.append(
        f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="{fmt(r)}" fill="{color}" opacity="0.3">'
        f'<animate attributeName="opacity" values="0.08;0.75;0.08" dur="{dur:.2f}s" '
        f'begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'</circle>'
    )

# ---- title -------------------------------------------------------------
svg.append(
    f'<text x="{MARGIN}" y="34" font-size="25" font-weight="700" fill="url(#titleGrad)">'
    f'3D CONTRIBUTION CITY</text>'
)
svg.append(
    f'<text x="{MARGIN}" y="58" font-size="15" fill="{MUTED}">'
    f'{total} contributions in the last year &#8226; @{USERNAME}</text>'
)

# ---- isometric city, wrapped in a rig that gently rocks side to side -----
rig_cx = OFF_X + (min_x + max_x) / 2
rig_cy = OFF_Y + (min_top_y + max_ground_y) / 2

svg.append('<g>')
svg.append(
    f'<animateTransform attributeName="transform" type="rotate" '
    f'values="-2.5 {fmt(rig_cx)} {fmt(rig_cy)};2.5 {fmt(rig_cx)} {fmt(rig_cy)};-2.5 {fmt(rig_cx)} {fmt(rig_cy)}" '
    f'dur="9s" begin="3.4s" calcMode="spline" '
    f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1" repeatCount="indefinite"/>'
)



buildings.sort(key=lambda b: (b["depth"], b["r"]))
max_depth = COLS + ROWS - 2

body = []
glow = []
for b in buildings:
    depth = b["depth"]
    delay = 0.35 + (depth / max_depth) * 1.7
    c = gradient(b["t"]) if b["count"] else None
    top_fill = rgb(c) if c else EMPTY_TOP
    left_fill = rgb(shade(c, 0.55)) if c else EMPTY_LEFT
    right_fill = rgb(shade(c, 0.75)) if c else EMPTY_RIGHT

    px, py = shift(b["pivot"])
    body.append(f'<g transform="translate({fmt(px)},{fmt(py)})">')
    body.append(
        f'<animateTransform attributeName="transform" type="scale" additive="sum" '
        f'from="1 0" to="1 1" begin="{delay:.3f}s" dur="0.5s" '
        f'calcMode="spline" keySplines="0.16 0.84 0.44 1" fill="freeze"/>'
    )
    body.append(f'<g transform="translate({fmt(-px)},{fmt(-py)})">')
    body.append(f'<polygon points="{pts(b["left"])}" fill="{left_fill}"/>')
    body.append(f'<polygon points="{pts(b["right"])}" fill="{right_fill}"/>')
    if b["t"] > 0.6:
        pulse_dur = 1.8 + depth % 5 * 0.25
        glow.append(
            f'<polygon points="{pts(b["top"])}" fill="{top_fill}" filter="url(#glow)" opacity="0.9">'
            f'<animate attributeName="opacity" values="0.6;1;0.6" dur="{pulse_dur:.2f}s" '
            f'begin="{delay + 0.55:.2f}s" repeatCount="indefinite"/>'
            f'</polygon>'
        )
    else:
        body.append(f'<polygon points="{pts(b["top"])}" fill="{top_fill}"/>')
    body.append("</g></g>")

svg.append("".join(body))
svg.append("".join(glow))
svg.append("</g>")  # close rocking rig

# ---- legend -------------------------------------------------------------
ly = H - MARGIN + 6
svg.append(f'<text x="{MARGIN}" y="{ly}" font-size="15" fill="{MUTED}">LESS</text>')
svg.append(f'<rect x="{MARGIN + 58}" y="{ly - 14}" width="120" height="16" rx="6" fill="url(#legendGrad)"/>')
svg.append(f'<text x="{MARGIN + 190}" y="{ly}" font-size="15" fill="{MUTED}">MORE</text>')

svg.append("</svg>")

OUT.write_text("".join(svg), encoding="utf-8")
print(f"Wrote {OUT}; total={total}; days={len(days)}; max_day={max_count}; size={W}x{H}")

import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

USERNAME = os.environ.get("GITHUB_USERNAME", "itsmeetsharma777")
OUT = Path(os.environ.get("OUTPUT", "assets/contribution-3d.gif"))
OUT.parent.mkdir(parents=True, exist_ok=True)

URL = f"https://github.com/users/{USERNAME}/contributions"
headers = {"User-Agent": "github-profile-3d-contribution-generator/1.0"}
resp = requests.get(URL, headers=headers, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")
entries = []
for node in soup.select("[data-date][data-count]"):
    date = node.get("data-date")
    try:
        count = int(node.get("data-count", "0"))
    except ValueError:
        count = 0
    if date:
        entries.append((date, count))

# Fallback parser for markup changes: read contribution day text/title.
if len(entries) < 300:
    entries = []
    for node in soup.find_all(["td", "rect"]):
        date = node.get("data-date")
        count = node.get("data-count")
        if date and count is not None:
            try:
                entries.append((date, int(count)))
            except ValueError:
                pass

if not entries:
    print("Could not find contribution data on GitHub.", file=sys.stderr)
    sys.exit(1)

# Keep one year, ordered oldest -> newest. GitHub normally returns ~365 days.
entries = sorted({d: c for d, c in entries}.items())[-371:]
counts = [c for _, c in entries]
max_count = max(counts) if counts else 1

# Arrange as 53 weeks x 7 days. Pad the beginning so weekdays line up.
first = datetime.strptime(entries[0][0], "%Y-%m-%d").date()
pad = (first.weekday() + 1) % 7  # Sunday=0
cells = [(None, 0)] * pad + entries
weeks = [cells[i:i+7] for i in range(0, len(cells), 7)]
while len(weeks) < 53:
    weeks.append([(None, 0)] * 7)
weeks = weeks[:53]

# Premium dark canvas.
W, H = 1500, 610
BG = (7, 5, 16)
GRID = (23, 16, 39)
TEXT = (231, 221, 250)
MUTED = (151, 130, 179)

# Gradient: purple -> pink -> red -> orange -> green.
stops = [
    (0.00, (126, 34, 255)),
    (0.25, (232, 66, 190)),
    (0.50, (239, 68, 68)),
    (0.72, (249, 137, 50)),
    (1.00, (71, 220, 139)),
]

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def gradient(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        p1, c1 = stops[i]
        p2, c2 = stops[i + 1]
        if t <= p2:
            return lerp(c1, c2, (t - p1) / (p2 - p1))
    return stops[-1][1]

def shade(c, factor):
    return tuple(max(0, min(255, int(x * factor))) for x in c)

# Cube geometry.
DX, DY = 24, 12
CUBE_W = 16
DEPTH = 9
BASE_Y = 500
ORIGIN_X = 760
MAX_H = 110

# Height mapping gives low blocks some presence while making heavy days rise strongly.
def height_for(count):
    if count <= 0:
        return 3
    t = math.sqrt(count / max_count)
    return 8 + t * MAX_H

def draw_cube(draw, x, y, h, color, alpha=1.0):
    # Isometric top + left/right side faces.
    top = [(x, y-h), (x+CUBE_W, y-h-DEPTH), (x+2*CUBE_W, y-h), (x+CUBE_W, y-h+DEPTH)]
    left = [(x, y-h), (x+CUBE_W, y-h+DEPTH), (x+CUBE_W, y+DEPTH), (x, y)]
    right = [(x+CUBE_W, y-h+DEPTH), (x+2*CUBE_W, y-h), (x+2*CUBE_W, y), (x+CUBE_W, y+DEPTH)]
    draw.polygon(left, fill=shade(color, 0.68))
    draw.polygon(right, fill=shade(color, 0.48))
    draw.polygon(top, fill=color)
    # tiny highlight on top edge
    draw.line([top[0], top[1], top[2]], fill=shade(color, 1.15), width=1)

def make_frame(frame_idx):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # Soft horizontal glow behind the structure.
    for r in range(180, 0, -6):
        t = r / 180
        col = (int(17 * (1-t) + 7*t), int(8 * (1-t) + 5*t), int(28 * (1-t) + 16*t))
        d.ellipse((W//2-r*2, 250-r//2, W//2+r*2, 250+r//2), fill=col)

    # Header.
    d.text((62, 35), "GITHUB CONTRIBUTIONS", fill=TEXT)
    total = sum(counts)
    d.text((62, 67), f"{total} contributions in the last year  •  {USERNAME}", fill=MUTED)

    # Floor grid.
    for i in range(0, 54):
        x = ORIGIN_X + (i - 26) * DX
        d.line((x, BASE_Y+30, x+7, BASE_Y+30+7), fill=GRID, width=1)
    for j in range(8):
        y = BASE_Y + j * 11
        d.line((ORIGIN_X-650, y, ORIGIN_X+650, y), fill=GRID, width=1)

    # Draw back-to-front so blocks overlap naturally.
    ordered = []
    for col, week in enumerate(weeks):
        for row, (date, count) in enumerate(week):
            if date is None:
                continue
            ordered.append((col + row, col, row, date, count))
    ordered.sort(key=lambda x: (x[0], x[2]))

    pulse = frame_idx / 11.0
    for _, col, row, date, count in ordered:
        # Isometric position; slight animation makes the higher blocks breathe.
        x = ORIGIN_X + (col - row) * DX - CUBE_W
        y = BASE_Y + (col + row) * DY / 2
        h = height_for(count)
        if count > 0:
            wave = 1.0 + 0.035 * math.sin((col * 0.65 + row * 0.9) + pulse * math.pi * 2)
            h *= wave
        t = 0 if count == 0 else math.log1p(count) / math.log1p(max_count)
        color = gradient(t)
        if count == 0:
            color = (38, 26, 55)
        draw_cube(d, x, y, h, color)

    # Legend.
    lx, ly = 62, 545
    d.text((lx, ly), "LESS", fill=MUTED)
    for i in range(5):
        c = gradient(i/4)
        d.rounded_rectangle((lx+55+i*26, ly-1, lx+75+i*26, ly+15), radius=4, fill=c)
    d.text((lx+195, ly), "MORE", fill=MUTED)

    return im

frames = [make_frame(i) for i in range(12)]
frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=110,
    loop=0,
    optimize=True,
)
print(f"Wrote {OUT} from {len(entries)} GitHub contribution days; total={sum(counts)}")

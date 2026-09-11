import json, math, os, sys
from datetime import date, timedelta
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

USERNAME = os.environ.get('GITHUB_USERNAME', 'itsmeetsharma777')
OUT = Path(os.environ.get('OUTPUT', 'assets/contribution-3d.gif'))
OUT.parent.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get('GITHUB_TOKEN')

QUERY = '''
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
'''

def fetch_data():
    if not TOKEN:
        raise RuntimeError('GITHUB_TOKEN is required')
    r = requests.post(
        'https://api.github.com/graphql',
        json={'query': QUERY, 'variables': {'login': USERNAME}},
        headers={'Authorization': f'bearer {TOKEN}', 'Accept': 'application/json'},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get('errors'):
        raise RuntimeError(payload['errors'][0].get('message', 'GraphQL error'))
    cal = payload['data']['user']['contributionsCollection']['contributionCalendar']
    days = []
    for week in cal['weeks']:
        days.extend(week['contributionDays'])
    return days, cal['totalContributions']

try:
    days, total = fetch_data()
except Exception as exc:
    print(f'Contribution data fetch failed: {exc}', file=sys.stderr)
    sys.exit(1)

# GitHub returns complete contribution weeks. Keep the latest 53 weeks.
days = days[-371:]
max_count = max((d['contributionCount'] for d in days), default=1)

W, H = 1500, 540
BG = (7, 5, 16)
GRID = (28, 20, 43)
TEXT = (235, 225, 250)
MUTED = (151, 130, 179)

STOPS = [
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
    for i in range(len(STOPS)-1):
        p1, c1 = STOPS[i]
        p2, c2 = STOPS[i+1]
        if t <= p2:
            return lerp(c1, c2, (t-p1)/(p2-p1))
    return STOPS[-1][1]

def shade(c, f):
    return tuple(max(0, min(255, int(v*f))) for v in c)

def load_font(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

font_title = load_font(27)
font_small = load_font(16)

# Arrange the calendar as 53 columns x 7 rows.
weeks = []
for i in range(0, len(days), 7):
    chunk = days[i:i+7]
    if len(chunk) == 7:
        weeks.append(chunk)
while len(weeks) < 53:
    weeks.insert(0, [{'date': '', 'contributionCount': 0} for _ in range(7)])
weeks = weeks[-53:]

CELL_W, CELL_H = 25, 43
CUBE_W, DEPTH = 19, 8
BASE_Y = 448
ORIGIN_X = 80
MAX_H = 100


def make_frame(frame):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((48, 30), '3D CONTRIBUTION HEATMAP', fill=TEXT, font=font_title)
    d.text((48, 66), f'{total} contributions in the last year  •  {USERNAME}', fill=MUTED, font=font_small)

    # Wide isometric floor so all 53 weeks remain visible.
    for col in range(54):
        x = ORIGIN_X + col * CELL_W
        d.line((x, BASE_Y + 6, x + 8, BASE_Y + 14), fill=GRID, width=1)
    for row in range(8):
        y = BASE_Y - row * CELL_H
        d.line((ORIGIN_X, y, ORIGIN_X + 1325, y), fill=GRID, width=1)

    # Draw from back to front so the 3D columns layer naturally.
    pulse = frame / 10.0
    for row in range(6, -1, -1):
        for col in range(53):
            count = weeks[col][row]['contributionCount']
            x = ORIGIN_X + col * CELL_W
            base_y = BASE_Y - row * CELL_H
            t = 0 if count == 0 else math.log1p(count) / math.log1p(max_count)
            h = 3 if count == 0 else 8 + t * MAX_H
            if count:
                h *= 1 + 0.025 * math.sin((col * .55 + row * .8) + pulse * math.pi * 2)
            c = (39, 28, 55) if count == 0 else gradient(t)

            # Front vertical face.
            front = [(x, base_y), (x + CUBE_W, base_y),
                     (x + CUBE_W, base_y - h), (x, base_y - h)]
            # Right face adds the isometric depth.
            right = [(x + CUBE_W, base_y), (x + CUBE_W + DEPTH, base_y - 5),
                     (x + CUBE_W + DEPTH, base_y - h - 5), (x + CUBE_W, base_y - h)]
            # Top face.
            top = [(x, base_y - h), (x + CUBE_W, base_y - h),
                   (x + CUBE_W + DEPTH, base_y - h - 5), (x + DEPTH, base_y - h - 5)]
            d.polygon(front, fill=shade(c, .68))
            d.polygon(right, fill=shade(c, .48))
            d.polygon(top, fill=c)

    d.text((48, 505), 'LESS', fill=MUTED, font=font_small)
    for i in range(5):
        c = gradient(i / 4)
        x = 105 + i * 25
        d.rounded_rectangle((x, 502, x + 19, 518), radius=4, fill=c)
    d.text((235, 505), 'MORE', fill=MUTED, font=font_small)
    return im

frames = [make_frame(i) for i in range(10)]
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
print(f'Wrote {OUT}; total={total}; days={len(days)}; max_day={max_count}')

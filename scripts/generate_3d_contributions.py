"""Generate a compact dark 3D GitHub contribution dashboard."""
import math
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import requests

USERNAME=os.environ.get("GITHUB_USERNAME","itsmeetsharma777")
OUTPUT=Path(os.environ.get("OUTPUT","assets/contribution-3d.svg"))
TOKEN=os.environ.get("GITHUB_TOKEN")
QUERY='''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''

def fetch_days():
    if not TOKEN: raise RuntimeError("GITHUB_TOKEN is required")
    r=requests.post("https://api.github.com/graphql",json={"query":QUERY,"variables":{"login":USERNAME}},headers={"Authorization":f"bearer {TOKEN}","Accept":"application/json"},timeout=30)
    r.raise_for_status(); p=r.json()
    if p.get("errors"): raise RuntimeError(p["errors"][0].get("message","GitHub GraphQL error"))
    return [d for w in p["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]

def streaks(days):
    a=[int(d["contributionCount"]) for d in days]; longest=run=0
    for n in a:
        run=run+1 if n>0 else 0; longest=max(longest,run)
    current=0
    for n in reversed(a):
        if n<=0: break
        current+=1
    return longest,current,max(a,default=0)

def fmt(s): return date.fromisoformat(s).strftime("%b %-d")
def rgb(c): return f"rgb({int(c[0])},{int(c[1])},{int(c[2])})"
def mix(a,b,t): return tuple(a[i]+(b[i]-a[i])*t for i in range(3))
def shade(c,f): return tuple(max(0,min(255,x*f)) for x in c)
def points(p): return " ".join(f"{x:.1f},{y:.1f}" for x,y in p)

try: days=fetch_days()
except Exception as exc:
    print(f"Live contribution fetch failed: {exc}",file=sys.stderr); today=date.today()
    days=[{"date":(today-timedelta(days=370-i)).isoformat(),"contributionCount":0} for i in range(371)]
days=days[-371:]
while len(days)<371:
    first=date.fromisoformat(days[0]["date"]); days.insert(0,{"date":(first-timedelta(days=1)).isoformat(),"contributionCount":0})
weeks=[days[i:i+7] for i in range(0,371,7)]
max_count=max((int(d["contributionCount"]) for d in days),default=1) or 1
total=sum(int(d["contributionCount"]) for d in days)
longest,current,busiest=streaks(days)

# Compact 1400x900 canvas. The city is centered horizontally and kept away from the card edge.
W,H=1400,900
BG="#0d1117"; BORDER="#30363d"; TEXT="#f0f6fc"; MUTED="#8b949e"
GREEN="#238b24"; GROUND="#dae784"; GROUND_STROKE="#c8dc73"
LOW=(133,176,78); HIGH=(27,63,12)
HW,HH=17.0,6.3
OX,OY=171.0,350.0
MAX_H=104.0

def project(c,r): return OX+(c-r)*HW, OY+(c+r)*HH
def color(t): return mix(LOW,HIGH,t)

grid=[]
for c in range(53):
    for r in range(7):
        x,y=project(c,r); grid.append((c+r,r,c,x,y))

svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">','<defs>',f'<clipPath id="clip"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8"/></clipPath>','</defs>',f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>']
svg += [
 f'<text x="820" y="50" font-size="20" fill="{MUTED}">1 year total</text>',f'<text x="820" y="104" font-size="56" font-weight="700" fill="{GREEN}">{total:,}</text>',f'<text x="1035" y="104" font-size="20" fill="{TEXT}">contributions</text>',f'<text x="1035" y="132" font-size="15" fill="{MUTED}">{fmt(days[0]["date"])} — {fmt(days[-1]["date"])}</text>',
 f'<text x="820" y="180" font-size="20" fill="{MUTED}">Busiest day</text>',f'<text x="820" y="234" font-size="56" font-weight="700" fill="{GREEN}">{busiest}</text>',f'<text x="1035" y="234" font-size="20" fill="{TEXT}">contributions</text>',f'<text x="1035" y="262" font-size="15" fill="{MUTED}">Peak activity</text>',
 f'<text x="52" y="455" font-size="20" fill="{MUTED}">Longest streak</text>',f'<text x="52" y="510" font-size="56" font-weight="700" fill="{GREEN}">{longest}</text>',f'<text x="180" y="510" font-size="20" fill="{TEXT}">days</text>',f'<text x="52" y="537" font-size="15" fill="{MUTED}">Consecutive contribution days</text>',
 f'<text x="52" y="600" font-size="20" fill="{MUTED}">Current streak</text>',f'<text x="52" y="655" font-size="56" font-weight="700" fill="{GREEN}">{current}</text>',f'<text x="180" y="655" font-size="20" fill="{TEXT}">days</text>',f'<text x="52" y="682" font-size="15" fill="{MUTED}">Ending today</text>']
svg.append('<g clip-path="url(#clip)">')

for _,r,c,x,y in sorted(grid):
    top=[(x,y-HH),(x+HW,y),(x,y+HH),(x-HW,y)]
    svg.append(f'<polygon points="{points(top)}" fill="{GROUND}" stroke="{GROUND_STROKE}" stroke-width="0.55" opacity="0.97"/>')

# Draw every non-empty contribution as a 3D block. The geometry itself remains
# visible at all times; only a gentle vertical lift is animated, so GitHub's
# SVG renderer never loses the blocks.
for _,r,c,x,y in sorted(grid):
    n=int(weeks[c][r]["contributionCount"])
    if n<=0: continue
    t=math.log1p(n)/math.log1p(max_count); h=8+t*MAX_H; base=color(t)
    top=[(x,y-HH-h),(x+HW,y-h),(x,y+HH-h),(x-HW,y-h)]
    left=[(x-HW,y),(x,y+HH),(x,y+HH-h),(x-HW,y-h)]
    right=[(x,y+HH),(x+HW,y),(x+HW,y-h),(x,y+HH-h)]
    delay=((c*7+r)%61)*0.035
    svg.append(f'<g transform="translate(0 0)"><animateTransform attributeName="transform" type="translate" values="0 14;0 0;0 14" keyTimes="0;0.5;1" dur="6s" begin="{delay:.2f}s" repeatCount="indefinite"/>')
    svg.append(f'<polygon points="{points(left)}" fill="{rgb(shade(base,.50))}"/>')
    svg.append(f'<polygon points="{points(right)}" fill="{rgb(shade(base,.70))}"/>')
    svg.append(f'<polygon points="{points(top)}" fill="{rgb(base)}"/>')
    svg.append('</g>')
svg.append('</g>')

# Bottom summary row.
line=745
svg.append(f'<line x1="0" y1="{line}" x2="{W}" y2="{line}" stroke="{BORDER}"/>')
for x in (466,932): svg.append(f'<line x1="{x}" y1="{line}" x2="{x}" y2="{H}" stroke="{BORDER}"/>')
for cx,title,value,sub in [(233,"Contributions in the last year",f"{total:,} total",f"{fmt(days[0][\"date\"])} — {fmt(days[-1][\"date\"])}"),(699,"Longest streak",f"{longest} days","Consecutive contribution days"),(1166,"Current streak",f"{current} days","Ending today")]:
    svg.append(f'<text x="{cx}" y="785" text-anchor="middle" font-size="17" fill="{MUTED}">{title}</text>')
    svg.append(f'<text x="{cx}" y="830" text-anchor="middle" font-size="38" fill="{TEXT}">{value}</text>')
    svg.append(f'<text x="{cx}" y="858" text-anchor="middle" font-size="14" fill="{MUTED}">{sub}</text>')
svg.append('</svg>')
OUTPUT.write_text("\n".join(svg),encoding="utf-8")
print(f"Generated {OUTPUT} — {total} contributions, busiest {busiest}, longest {longest}, current {current}")
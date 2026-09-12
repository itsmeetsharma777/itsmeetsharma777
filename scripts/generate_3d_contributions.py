"""Generate the premium dark isometric GitHub contribution city."""
import html, math, os, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
import requests

USER=os.environ.get("GITHUB_USERNAME","itsmeetsharma777")
OUT=Path(os.environ.get("OUTPUT","assets/contribution-3d.svg")); TOKEN=os.environ.get("GITHUB_TOKEN")
Q='''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''

def valid(ds):
    if len(ds)<300: raise RuntimeError(f"GitHub returned an incomplete contribution calendar ({len(ds)} days)")
    return ds

def graphql():
    if not TOKEN: raise RuntimeError("GITHUB_TOKEN is unavailable")
    today=date.today(); start=today-timedelta(days=370)
    r=requests.post("https://api.github.com/graphql",json={"query":Q,"variables":{"login":USER,"from":f"{start}T00:00:00Z","to":f"{today}T23:59:59Z"}},headers={"Authorization":f"bearer {TOKEN}","Accept":"application/json"},timeout=30); r.raise_for_status(); p=r.json()
    if p.get("errors"): raise RuntimeError(p["errors"][0].get("message","GraphQL error"))
    return valid([d for w in p["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]])

def public():
    r=requests.get(f"https://github.com/users/{USER}/contributions",headers={"User-Agent":"Mozilla/5.0 contribution-dashboard"},timeout=30); r.raise_for_status()
    ds=[]
    for iso,cell in re.findall(r'<td\b[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>(.*?)</td>',r.text,re.S):
        text=html.unescape(re.sub(r"<[^>]+>"," ",cell)); m=re.search(r"(\d[\d,]*) contributions?",text); ds.append({"date":iso,"contributionCount":int(m.group(1).replace(",","")) if m else 0})
    return valid(ds)

def days():
    try: ds=graphql(); print(f"Fetched {len(ds)} days from GitHub GraphQL"); return ds
    except Exception as e:
        print(f"GraphQL fetch failed: {e}",file=sys.stderr)
        ds=public(); print(f"Fetched {len(ds)} days from GitHub public contribution graph"); return ds

def fmt(s): return datetime.strptime(s,"%Y-%m-%d").strftime("%B %d").replace(" 0","")
def streak(ds):
    a=[int(x["contributionCount"]) for x in ds]; longest=run=0
    for n in a:
        run=run+1 if n else 0; longest=max(longest,run)
    cur=0
    for n in a[::-1]:
        if n: cur+=1
        else: break
    return longest,cur,max(a,default=0)
def poly(p): return " ".join(f"{x:.1f},{y:.1f}" for x,y in p)
def shade(c,f): return tuple(max(0,min(255,int(v*f))) for v in c)
def rgb(c): return f"rgb({c[0]},{c[1]},{c[2]})"

ds=days()[-371:]
while len(ds)<371:
    first=date.fromisoformat(ds[0]["date"]) if ds else date.today()-timedelta(days=370); ds.insert(0,{"date":(first-timedelta(days=1)).isoformat(),"contributionCount":0})
weeks=[ds[i:i+7] for i in range(0,371,7)]; mx=max((int(x["contributionCount"]) for x in ds),default=1) or 1; total=sum(int(x["contributionCount"]) for x in ds); longest,current,busiest=streak(ds)
W,H=1400,1040; BG="#0b1117"; BORDER="#26313d"; TEXT="#f0f6fc"; MUTED="#9aa8b8"; GREEN="#39e75f"
BASE_A,BASE_B="#607588","#71899a"; BASE_SIDE="#304657"; BASE_DARK="#1c2a36"; PALETTE=[(8,110,45),(8,153,54),(12,190,63),(20,218,73),(42,238,83),(78,250,101),(138,255,132)]
HW,HH=16.5,8.25; ORX,ORY=150.,245.; MAXH=172.; DEPTH=7.; CUBE_HW=13.0; CUBE_HH=6.5

def project(c,r): return ORX+(c-r)*HW,ORY+(c+r)*HH
def metric(x,y,h,v,u,s,size=72):
    vy=y+67; return [f'<text x="{x}" y="{y}" font-size="25" font-weight="600" fill="{MUTED}">{h}</text>',f'<text x="{x}" y="{vy}" font-size="{size}" font-weight="800" fill="{GREEN}">{v}<tspan dx="18" font-size="25" font-weight="700" fill="{TEXT}">{u}</tspan></text>',f'<text x="{x}" y="{vy+38}" font-size="18" fill="{MUTED}">{s}</text>']

svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">','<defs>',f'<clipPath id="clip"><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8"/></clipPath>','<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>','<filter id="shadow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="2.2"/></filter>','</defs>',f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="none" stroke="{BORDER}"/>']
svg+=metric(835,65,"1 year total",f"{total:,}","contributions",f"{fmt(ds[0]['date'])} — {fmt(ds[-1]['date'])}")+metric(835,230,"Busiest day",busiest,"contributions","Peak activity")+metric(60,520,"Longest streak",longest,"days","Consecutive contribution days",64)+metric(60,684,"Current streak",current,"days","Ending today",64)
svg.append('<g clip-path="url(#clip)">'); cells=[]
for c in range(53):
    for r in range(7): cells.append((c+r,r,c,*project(c,r)))
for _,r,c,x,y in sorted(cells):
    top=[(x,y-HH),(x+HW,y),(x,y+HH),(x-HW,y)]; low=[(x-HW,y+DEPTH),(x,y+HH+DEPTH),(x+HW,y+DEPTH)]; fill=BASE_A if (c+r)%2==0 else BASE_B
    svg += [f'<polygon points="{poly([top[3],top[2],low[1],low[0]])}" fill="{BASE_DARK}" stroke="#101a22" stroke-width="0.8"/>',f'<polygon points="{poly([top[2],top[1],low[2],low[1]])}" fill="{BASE_SIDE}" stroke="#172633" stroke-width="0.8"/>',f'<polygon points="{poly(top)}" fill="{fill}" stroke="#142532" stroke-width="1.8"/>',f'<polygon points="{poly([(x,y-HH+1.8),(x+HW-2,y),(x,y+HH-1.8),(x-HW+2,y)])}" fill="none" stroke="#a9bac6" stroke-opacity="0.48" stroke-width="0.85"/>']
counts=[[int(weeks[c][r]["contributionCount"]) for r in range(7)] for c in range(53)]
for _,r,c,x,y in sorted(cells):
    n=counts[c][r]; t=math.log1p(n)/math.log1p(mx); ws=wt=0
    for dc in range(-2,3):
        for dr in range(-2,3):
            cc,rr=c+dc,r+dr
            if 0<=cc<53 and 0<=rr<7 and (dc or dr) and counts[cc][rr]>0:
                w=1/(1+(abs(dc)+abs(dr))*1.35); ws+=math.log1p(counts[cc][rr])/math.log1p(mx)*w; wt+=w
    field=ws/wt if wt else 0; vt=max(t,field*.78)
    if vt<.105: continue
    h=8+vt*MAXH; base=PALETTE[min(len(PALETTE)-1,int(vt*(len(PALETTE)-1)))]
    # Smaller footprint than the base tile creates a deliberate grey breathing gap around every building.
    ch,cv=CUBE_HW,CUBE_HH
    top=[(0,-cv-h),(ch,-h),(0,cv-h),(-ch,-h)]; left=[(-ch,0),(0,cv),(0,cv-h),(-ch,-h)]; right=[(0,cv),(ch,0),(ch,-h),(0,cv-h)]
    if vt>.14: svg.append(f'<ellipse cx="{x:.1f}" cy="{y+3:.1f}" rx="10" ry="4" fill="#020806" opacity=".38" filter="url(#shadow)"/>')
    svg.append(f'<g transform="translate({x:.1f},{y:.1f})">'+('<g filter="url(#glow)">' if vt>.52 else '')+f'<polygon points="{poly(left)}" fill="{rgb(shade(base,.36))}"/><polygon points="{poly(right)}" fill="{rgb(shade(base,.61))}"/><polygon points="{poly(top)}" fill="{rgb(base)}" stroke="{rgb(shade(base,1.12))}" stroke-width=".45"/>'+('</g>' if vt>.52 else '')+'</g>')
svg.append('</g>'); svg.append(f'<line x1="0" y1="865" x2="{W}" y2="865" stroke="{BORDER}"/>')
for x in (466,932): svg.append(f'<line x1="{x}" y1="865" x2="{x}" y2="{H}" stroke="{BORDER}"/>')
for cx,title,v,u,sub in [(233,"Contributions in the last year",f"{total:,}","total",f"{fmt(ds[0]['date'])} — {fmt(ds[-1]['date'])}"),(699,"Longest streak",str(longest),"days","Consecutive contribution days"),(1166,"Current streak",str(current),"days","Ending today")]:
    svg += [f'<text x="{cx}" y="914" text-anchor="middle" font-size="20" font-weight="600" fill="{MUTED}">{title}</text>',f'<text x="{cx}" y="969" text-anchor="middle" font-size="44" font-weight="800" fill="{GREEN}">{v}<tspan dx="18" font-size="24" font-weight="700" fill="{TEXT}">{u}</tspan></text>',f'<text x="{cx}" y="1005" text-anchor="middle" font-size="17" fill="{MUTED}">{sub}</text>']
svg.append('</svg>'); OUT.write_text("\n".join(svg),encoding="utf-8"); print(f"Generated {OUT} — {total} contributions, busiest {busiest}, longest streak {longest}, current streak {current}")
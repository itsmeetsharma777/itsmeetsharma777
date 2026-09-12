import os,re,html
from datetime import datetime,date
from pathlib import Path
import requests

USERNAME=os.getenv('GITHUB_USERNAME','itsmeetsharma777')
TOKEN=os.getenv('GITHUB_TOKEN')
OUT=Path(os.getenv('OUTPUT','assets/contribution-3d.svg'))

QUERY='''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''
r=requests.post('https://api.github.com/graphql',json={'query':QUERY,'variables':{'login':USERNAME}},headers={'Authorization':f'bearer {TOKEN}','Accept':'application/json'},timeout=30)
r.raise_for_status(); p=r.json()
if p.get('errors'): raise RuntimeError(p['errors'][0]['message'])
cal=p['data']['user']['contributionsCollection']['contributionCalendar']
days=sorted([d for w in cal['weeks'] for d in w['contributionDays']],key=lambda x:x['date'])[-366:]
total=cal['totalContributions']
busy=max(days,key=lambda d:d['contributionCount'])

longest_n=0; longest_s=longest_e=None; run=0; run_s=None
for d in days:
    if d['contributionCount']>0:
        if run==0: run_s=d['date']
        run+=1
        if run>longest_n: longest_n,longest_s,longest_e=run,run_s,d['date']
    else: run=0
current=0
for i in range(len(days)-1,-1,-1):
    if days[i]['contributionCount']>0:
        current+=1
    elif i==len(days)-1 and days[i]['date']==date.today().isoformat():
        continue
    else: break
current_e=days[-1]['date']

def fd(s):
    return datetime.strptime(s,'%Y-%m-%d').strftime('%b %-d, %Y')
def fr(a,b):
    aa=datetime.strptime(a,'%Y-%m-%d'); bb=datetime.strptime(b,'%Y-%m-%d')
    if aa.year==bb.year: return f'{aa.strftime("%b %-d")} – {bb.strftime("%b %-d, %Y")}'
    return f'{aa.strftime("%b %-d, %Y")} – {bb.strftime("%b %-d, %Y")}'

data=OUT.read_text(encoding='utf-8')
m=re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"',data)
if not m: raise RuntimeError('Could not find contribution SVG viewBox')
iw,ih=float(m.group(1)),float(m.group(2))
inner=re.sub(r'^\s*<\?xml[^>]*\?>','',data).strip()
inner=re.sub(r'^<svg[^>]*>','',inner,1)
inner=re.sub(r'</svg>\s*$','',inner,1)

W,H=1700,1050
PANEL='#0d0a19'; BORDER='#43206e'; TEXT='#f5efff'; MUTED='#aa9ac7'
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI,Arial,sans-serif">']
svg.append(f'<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#080612"/><stop offset="1" stop-color="#140a23"/></linearGradient><linearGradient id="accent"><stop stop-color="#a855f7"/><stop offset=".55" stop-color="#f472b6"/><stop offset="1" stop-color="#fb923c"/></linearGradient></defs>')
svg.append(f'<rect width="{W}" height="{H}" rx="30" fill="url(#bg)"/><rect x="2" y="2" width="{W-4}" height="{H-4}" rx="28" fill="none" stroke="{BORDER}" stroke-width="2"/>')
svg.append(f'<text x="55" y="58" font-size="28" font-weight="800" fill="url(#accent)">GITHUB CONTRIBUTION ACTIVITY</text>')
svg.append(f'<text x="55" y="84" font-size="15" fill="{MUTED}">@{html.escape(USERNAME)}  •  1 year  •  Live GitHub data</text>')

svg.append(f'<text x="55" y="145" font-size="14" fill="{MUTED}">1 year total</text><text x="55" y="193" font-size="50" font-weight="800" fill="#34d399">{total:,}</text><text x="55" y="219" font-size="13" fill="{MUTED}">{fd(days[0]["date"])} – {fd(days[-1]["date"])}</text>')
svg.append(f'<text x="55" y="270" font-size="14" fill="{MUTED}">Longest streak</text><text x="55" y="315" font-size="42" font-weight="800" fill="#c084fc">{longest_n} <tspan font-size="18">days</tspan></text><text x="55" y="340" font-size="13" fill="{MUTED}">{fr(longest_s,longest_e)}</text>')
svg.append(f'<text x="1450" y="145" font-size="14" fill="{MUTED}">Busiest day</text><text x="1450" y="193" font-size="50" font-weight="800" fill="#34d399">{busy["contributionCount"]:,}</text><text x="1450" y="219" font-size="13" fill="{MUTED}">{fd(busy["date"])}</text>')
svg.append(f'<text x="1450" y="270" font-size="14" fill="{MUTED}">Current streak</text><text x="1450" y="315" font-size="42" font-weight="800" fill="#f472b6">{current} <tspan font-size="18">days</tspan></text><text x="1450" y="340" font-size="13" fill="{MUTED}">through {fd(current_e)}</text>')

cx,cy,cw,ch=245,105,1210,650
svg.append(f'<svg x="{cx}" y="{cy}" width="{cw}" height="{ch}" viewBox="0 0 {iw:g} {ih:g}" preserveAspectRatio="xMidYMid meet">{inner}</svg>')

cards=[('Contributions in the last year',f'{total:,}',f'{fd(days[0]["date"])} – {fd(days[-1]["date"])}'),('Longest streak',f'{longest_n} days',fr(longest_s,longest_e)),('Current streak',f'{current} days',f'through {fd(current_e)}')]
for i,(label,val,sub) in enumerate(cards):
    x=55+i*530; w=500
    svg.append(f'<rect x="{x}" y="800" width="{w}" height="175" rx="18" fill="{PANEL}" stroke="{BORDER}" stroke-width="1.5"/>')
    svg.append(f'<text x="{x+w/2:.0f}" y="837" text-anchor="middle" font-size="14" fill="{MUTED}">{html.escape(label)}</text>')
    svg.append(f'<text x="{x+w/2:.0f}" y="893" text-anchor="middle" font-size="38" font-weight="800" fill="{TEXT}">{html.escape(val)}</text>')
    svg.append(f'<text x="{x+w/2:.0f}" y="925" text-anchor="middle" font-size="13" fill="{MUTED}">{html.escape(sub)}</text>')
svg.append(f'<text x="850" y="1018" text-anchor="middle" font-size="13" fill="{MUTED}">LESS  •  MORE  •  3D contribution heatmap  •  Updated daily</text>')
svg.append('</svg>')
OUT.write_text(''.join(svg),encoding='utf-8')
print(f'updated {OUT}: total={total}, busiest={busy["contributionCount"]}, longest={longest_n}, current={current}')

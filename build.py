"""Regenerate README and responsive SVGs: python tools/build.py (Python 3, no packages)."""
from pathlib import Path
from html import escape as esc
from urllib.parse import quote
import json, unicodedata

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'
D = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, Arial, sans-serif"
PALETTES = {
 'dark': dict(bg='#0D1117', card='#151B23', fg='#E6EDF3', muted='#A6B0BD', line='#343C49', accent='#B29AF8'),
 'light': dict(bg='#FFFFFF', card='#F6F8FA', fg='#1F2328', muted='#59636E', line='#D1D9E0', accent='#7353BA')}
ICONS = {
 'profile': '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
 'focus': '<path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>'}

def width(s,size):
    # Conservative character advance; exact browser bounds are checked separately.
    return sum(size*(1.02 if unicodedata.east_asian_width(c) in 'WF' else .61 if c not in ' il.,:!' else .3) for c in s)

def wrap(s,size,maxw):
    lines=[]; line=''
    for word in s.split():
        candidate=(line+' '+word).strip()
        if line and width(candidate,size)>maxw: lines.append(line); line=word
        else: line=candidate
        if width(line,size)>maxw:
            chunk=''
            for c in line:
                if width(chunk+c,size)>maxw: lines.append(chunk); chunk=''
                chunk+=c
            line=chunk
    if line: lines.append(line)
    return lines

def text(x,y,s,size=16,color=None,bold=False,anchor=None):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color or P["fg"]}" font-weight="{600 if bold else 400}"'+(f' text-anchor="{anchor}"' if anchor else '')+'>'+esc(s)+'</text>'

def lines(x,y,s,maxw,size=16,color=None,bold=False,leading=26):
    ss=wrap(s,size,maxw)
    return ''.join(text(x,y+i*leading,t,size,color,bold) for i,t in enumerate(ss)),y+len(ss)*leading

def svg(name,w,h,body,title,desc):
    (A/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">{esc(desc)}</desc><g font-family="{FONT}">{body}</g></svg>\n',encoding='utf-8')

def about(theme,mobile):
    w=360 if mobile else 840; cw=w if mobile else 412; ch=286
    body=''
    for i,key in enumerate(['profile','focus']):
        x=0 if mobile else i*428; y=i*(ch+16) if mobile else 0
        body+=f'<rect x="{x+.5}" y="{y+.5}" width="{cw-1}" height="{ch-1}" rx="16" fill="{P["card"]}" stroke="{P["line"]}"/>'
        body+=f'<g transform="translate({x+24} {y+24})" fill="none" stroke="{P["accent"]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</g>'
        body+=text(x+24,y+78,'Profile' if key=='profile' else 'Current Focus',19,bold=True)
        yy=y+112
        for j,s in enumerate(D[key]):
            if key=='profile' and j==3:
                body+=f'<path d="M{x+24} {yy-10}H{x+cw-24}" stroke="{P["line"]}"/>'; yy+=19
            chunk,yy=lines(x+24,yy,s,cw-48,16,P['fg'] if j==0 or key=='profile' and j==3 else P['muted'])
            body+=chunk
            if key=='focus': yy+=9
    svg(f'about-{theme}-{ "mobile" if mobile else "desktop"}.svg',w,ch*2+16 if mobile else ch,body,'Profile and Current Focus','; '.join(D['profile']+D['focus']))

def timeline(key,theme,mobile):
    w=360 if mobile else 840
    body=''; y=32; lastyear=None; records=[]
    for e in sorted(D[key],key=lambda e:(e['year'],e['start']),reverse=True):
        if e['year']!=lastyear:
            if lastyear is not None: y+=28
            body+=text(0,y,e['year'],23,bold=True); y+=42; lastyear=e['year']
        axis=9 if mobile else 128; x=30 if mobile else 154; maxw=w-x-8
        nodey=y-6
        if mobile:
            body+=text(x,y,e['start']+(' – '+e['end'] if e.get('end') else ''),15,P['muted'],True); y+=31
        else:
            body+=text(104,y,e['start'],16,P['fg'],True,'end')
            if e.get('end'): body+=text(104,y+26,'– '+e['end'],14,P['muted'],False,'end')
        chunk,y=lines(x,y,e['title'],maxw,17,None,True,27); body+=chunk; y+=5
        if e.get('place'):
            chunk,y=lines(x,y,e['place'],maxw,15,P['muted'],False,25); body+=chunk; y+=2
        chunk,y=lines(x,y,e['description'],maxw,16,P['muted'],False,27); body+=chunk
        records.append((axis,nodey,y,e['year'])); y+=34
    axisbody=''
    for i,(axis,start,end,year) in enumerate(records):
        end=records[i+1][1] if i+1<len(records) and records[i+1][3]==year else end+5
        axisbody+=f'<path d="M{axis} {start}V{end}" fill="none" stroke="{P["line"]}" stroke-width="2"/>'
    for axis,start,end,year in records:
        axisbody+=f'<circle cx="{axis}" cy="{start}" r="6" fill="{P["accent"]}"/>'
    svg(f'{key}-{theme}-{ "mobile" if mobile else "desktop"}.svg',w,y-12,axisbody+body,'Research Timeline' if key=='research' else 'On- & Off-Campus Activities',alt(key))

def alt(key):
    if key=='about': return 'Profile: '+', '.join(D['profile'])+'. Current Focus: '+', '.join(D['focus'])+'.'
    return ' / '.join(e['year']+' '+e['start']+(' – '+e['end'] if e.get('end') else '')+': '+e['title']+'. '+(e['place']+'. ' if e.get('place') else '')+e['description'] for e in D[key])

def picture(key):
    return f'''<picture>
  <source media="(prefers-color-scheme: dark) and (max-width: 767px)" srcset="assets/{key}-dark-mobile.svg">
  <source media="(max-width: 767px)" srcset="assets/{key}-light-mobile.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/{key}-dark-desktop.svg">
  <img src="assets/{key}-light-desktop.svg" width="100%" alt="{esc(alt(key),quote=True)}">
</picture>'''

def badges(items):
    return '\n'.join(f'  <img src="assets/{slug}.svg" height="20" alt="{esc(label)}">' for slug,label in items)

for theme,P in PALETTES.items():
    for mobile in [False,True]:
        about(theme,mobile)
        timeline('research',theme,mobile)
        timeline('activities',theme,mobile)

# Compact neutral pills can be regenerated locally when interests change.
P=PALETTES['dark']
for i,s in enumerate(D['interests']):
    w=round(width(s,11)+18)
    svg(f'interest-{i+1}.svg',w,20,f'<rect width="{w}" height="20" rx="10" fill="#444A53"/>'+text(w/2,14,s,11,'#FFFFFF',False,'middle'),s,s)

contacts=[]
for label,val,href in [('Email',D['email'],'mailto:'+D['email']),('GitHub',D['github'],'https://github.com/'+quote(D['github'],safe=''))]:
    badge=f'<img src="assets/contact-{label.lower()}.svg" height="20" alt="{label}">'
    if val.startswith('YOUR_'): contacts.append(badge+' <code>'+esc(val)+'</code>')
    else: contacts.append(f'<a href="{esc(href,quote=True)}">{badge}</a>')
intro=esc(D['intro']).replace('AI research and real-world applications','<strong>AI research and real-world applications</strong>')
contact_html='<br>\n  '.join(contacts)
readme=f'''<!-- Generated from profile.json by tools/build.py. Upload README.md AND assets/. -->
<p align="center">
  <picture>
    <source media="(max-width: 767px)" srcset="assets/header-mobile.svg">
    <img src="assets/header.svg" width="100%" alt="Nice to see you! — WELCOME TO MY GITHUB PROFILE">
  </picture>
</p>

## About Me 👋

{intro}

{picture('about')}

**Research Interests**

<p>
{badges([(f'interest-{i+1}',s) for i,s in enumerate(D['interests'])])}
</p>

## Tech Stack

<p align="center"><strong>Languages</strong></p>
<p align="center">
{badges([('python','Python'),('c','C'),('java','Java')])}
</p>

<p align="center"><strong>AI &amp; Data Science</strong></p>
<p align="center">
{badges([('numpy','NumPy'),('pandas','Pandas'),('scikit-learn','scikit-learn'),('matplotlib','Matplotlib')])}
</p>

## Research Timeline

{picture('research')}

## On- & Off-Campus Activities

{picture('activities')}

## Contact

<!-- Replace YOUR_EMAIL and YOUR_GITHUB_ID in profile.json, then regenerate. -->
<p align="center">
  {contact_html}
</p>
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
print('Generated README.md, 12 theme/layout SVGs, and interest pills.')

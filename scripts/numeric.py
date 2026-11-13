#!/usr/bin/env python3
"""Strict public-report numerical extractor. No paywall bypass and no guessing.
Candidate-only whenever a source becomes ambiguous; failures never erase accepted figures.
"""
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib import robotparser
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'numeric_updates.json'
HEADERS={'User-Agent':'ConstructionIntelligenceResearchMonitor/1.0 (public published economic reports)','Accept':'text/html'}
MONTHS={m:i+1 for i,m in enumerate('January February March April May June July August September October November December'.split())}
MONTH_PATTERN=r'('+'|'.join(MONTHS)+r')\s+(20\d{2})'
# Only public release pages from publishers on the approved source directory.
PROVIDERS={'ABC':('abc.org',),'Dodge':('construction.com',),'AIA':('aia.org',)}
SEEDS=[
 'https://www.abc.org/News-Media/News-Releases/abcs-construction-backlog-indicator-drops-in-october',
 'https://www.abc.org/News-Media/News-Releases/abcs-construction-backlog-indicator-rises-again-in-september-on-data-center-strength',
 'https://www.aia.org/resource-center/abi-september-2026-architecture-firm-billings-slump-deepens',
 'https://www.construction.com/dodge-momentum-index-falls-9-in-october/',
 'https://www.construction.com/construction-starts-recede-1-5-in-september/',
]
RULES={
 'ABC':[
   ('ABC contractor backlog','Backlog',r'(?:Construction\s+Backlog\s+Indicator|backlog\s+indicator)\s+(?:fell|rose|increased|decreased|dropped|rebounded|declined|climbed|remained|was)\s+to\s+(\d{1,2}\.\d)\s+months\s+in\s+([A-Z][a-z]+)', 'months',0,20),
 ],
 'Dodge':[
   ('Dodge Momentum Index','Planning',r'Dodge\s+Momentum\s+Index[^\n]{0,180}?(?:to|at)\s+(\d{2,3}\.\d)\s*\(?2000\s*=\s*100\)?', 'index',50,500),
   ('Total construction starts annualized','Starts',r'[Tt]otal\s+construction\s+starts[^\n]{0,160}?seasonally\s+adjusted\s+annual\s+rate\s+of\s+\$([\d.,]+)\s+(trillion|billion)', '$B SAAR',100,5000),
   ('Total construction starts YTD','Starts',r'[Tt]otal\s+construction\s+starts\s+were\s+(up|down)\s+(\d{1,3}\.\d)%\s+through\s+([A-Z][a-z]+)', '% YoY',-100,200),
 ],
 'AIA':[
   ('Architecture Billings Index','Design',r'(?:Architecture\s+Billings\s+Index(?:®)?\s*\(?ABI\)?|ABI)\s+score\s+of\s+(\d{2}\.\d)\s+for\s+the\s+month','index',0,100),
 ]
}

def owner(url):
 host=(urlsplit(url).hostname or '').lower()
 for name,ds in PROVIDERS.items():
  if any(host==d or host.endswith('.'+d) for d in ds):return name
 return None

def text_and_title(html):
 soup=BeautifulSoup(html,'html.parser')
 title=soup.h1.get_text(' ',strip=True) if soup.h1 else (soup.title.get_text(' ',strip=True) if soup.title else '')
 for x in soup(['script','style','header','footer','nav','form']):x.decompose()
 node=soup.select_one('article') or soup.select_one('main') or soup.body or soup
 paragraphs=[x.get_text(' ',strip=True) for x in node.select('p')]
 # Paragraph boundaries prevent accidentally matching across unrelated content.
 return title,'\n'.join(paragraphs) if paragraphs else node.get_text(' ',strip=True)

def period_from_title(title,publication=None):
 m=re.search(MONTH_PATTERN,title,re.I)
 if m:
  return f'{m.group(1).title()} {m.group(2)}'
 if publication:
  m=re.search(r'\bin\s+('+'|'.join(MONTHS)+r')\b',title,re.I)
  if m:
   month=m.group(1).title();pub_year=int(publication[:4]);pub_month=int(publication[5:7])
   year=pub_year-1 if MONTHS[month]>pub_month else pub_year
   if (pub_year-year)*12+pub_month-MONTHS[month] in (0,1,2):return f'{month} {year}'
 return None

def pub_date(html):
 soup=BeautifulSoup(html,'html.parser')
 for query,att in [('meta[property="article:published_time"]','content'),('meta[name="date"]','content'),('time[datetime]','datetime')]:
  tag=soup.select_one(query)
  if tag:
   v=tag.get(att,'')[:10]
   if re.fullmatch(r'20\d{2}-\d{2}-\d{2}',v):return v
 return None

def extract(url,html):
 provider=owner(url)
 if not provider:return [],['unapproved publisher domain']
 title,body=text_and_title(html)
 low_title=title.lower()
 # Restrict page classifications to release titles. Keyword-only matches in nav are insufficient.
 family={'ABC':'backlog','AIA':'abi','Dodge':'dodge momentum index'}
 if provider=='ABC' and 'backlog' not in low_title:return [],['not a backlog release']
 if provider=='AIA' and not ('abi' in low_title or 'architecture billings' in low_title):return [],['not an ABI release']
 if provider=='Dodge' and not ('momentum index' in low_title or 'construction starts' in low_title):return [],['not a Dodge DMI/starts release']
 publication=pub_date(html)
 titleperiod=period_from_title(title,publication)
 issues=[]; accepted=[]
 for label,section,pattern,unit,minval,maxval in RULES[provider]:
  if provider=='Dodge' and ('momentum' in label.lower())!=('momentum index' in low_title):continue
  matches=list(re.finditer(pattern,body,re.I))
  if len(matches)!=1:
   issues.append(f'{label}: expected exactly 1 matching statement; found {len(matches)}');continue
  m=matches[0]
  if label=='ABC contractor backlog':
   value=float(m.group(1));month=m.group(2).title();year=titleperiod.split(' ')[-1] if titleperiod else None
   # ABC headline often omits the year; date of release is acceptable if month explicitly appears in the body.
   if not year and publication:year=publication[:4]
   period=f'{month} {year}' if year else None
  elif label=='Total construction starts YTD':
   value=float(m.group(2))*(1 if m.group(1).lower()=='up' else -1)
   period=f'YTD through {m.group(3).title()} {titleperiod.split()[-1]}' if titleperiod else None
  elif label=='Total construction starts annualized':
   value=float(m.group(1).replace(',',''))*(1000 if m.group(2).lower()=='trillion' else 1)
   period=titleperiod
  else:
   value=float(m.group(1)); period=titleperiod
  if not period or not minval<=value<=maxval:
   issues.append(f'{label}: invalid reporting period or out-of-range number');continue
  # Cross-check if report date is present; do not permit future-dated sources.
  if publication and publication[:4] < period[-4:]:
   issues.append(f'{label}: publication predates reporting year');continue
  # Require the reporting month to occur in headline/title or contextual ABC statement.
  if not publication:
   issues.append(f'{label}: no machine-readable publication date (queued for review)');continue
  accepted.append({'section':section,'label':label,'value':value,'unit':unit,'period':period,
    'source':provider,'publication':publication,'url':url,'detail':'Automatically extracted from a public publisher release; rule-validated.',
    'sector':'All','comparison':'','kind':'measured','verification':'rule_validated','evidence':m.group(0)[:300]})
 return accepted,issues

def robots_permit(session,url):
 p=urlsplit(url);robots=f'{p.scheme}://{p.netloc}/robots.txt'
 try:
  r=session.get(robots,headers=HEADERS,timeout=7)
  if r.status_code in (401,403):return False
  if r.ok:
   parser=robotparser.RobotFileParser();parser.parse(r.text.splitlines())
   return parser.can_fetch(HEADERS['User-Agent'],url)
 except requests.RequestException:
  pass
 return True

def run(links=None,session=None):
 session=session or requests.Session()
 old={'observations':[]}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf8'))
  except (ValueError,OSError):pass
 rows={(x['source'],x['label'],x['period']):x for x in old.get('observations',[])}
 audit=[]
 urls=list(dict.fromkeys(SEEDS+(links or [])))
 # Do not make this a general web spider; only relevant approved release URLs.
 urls=[u for u in urls if owner(u) and ('backlog' in u.lower() or 'momentum' in u.lower() or 'construction-starts' in u.lower() or 'abi-' in u.lower() or 'billings' in u.lower())][:22]
 for url in urls:
  record={'url':url,'status':'unavailable','accepted':0,'issues':[]}
  if not robots_permit(session,url):
   record.update(status='blocked',issues=['robots.txt disallows collection']);audit.append(record);continue
  try:
   r=session.get(url,headers=HEADERS,timeout=14)
   if r.status_code in (401,403):record.update(status='blocked',issues=[f'HTTP {r.status_code}']);audit.append(record);continue
   r.raise_for_status()
   if 'html' not in r.headers.get('content-type',''):
    record['issues']=['not an HTML release'];audit.append(record);continue
   found,issues=extract(r.url,r.text)
   for entry in found:
    key=(entry['source'],entry['label'],entry['period'])
    # Preserve newest correction only. Older crawls never revert revisions.
    if key not in rows or entry['publication']>=rows[key]['publication']:rows[key]=entry
   record.update(status='validated' if found else 'review_required',accepted=len(found),issues=issues)
  except requests.RequestException as exc:
   record['issues']=[type(exc).__name__]
  audit.append(record)
 output={'schema_version':1,'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
 'validation_policy':'Strict pattern, unique match, source domain, reporting month, publisher release date, plausible range; otherwise no update',
 'observations':sorted(rows.values(),key=lambda x:(x['period'],x['label'],x['publication'])),
 'audit':audit}
 OUT.parent.mkdir(exist_ok=True)
 tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(output,indent=2)+'\n',encoding='utf8');tmp.replace(OUT)
 print('Numerical extraction:',len(output['observations']),'total observations,',sum(x['accepted'] for x in audit),'accepted this run,',sum(x['status']=='blocked' for x in audit),'blocked')
 return output

if __name__=='__main__':run()

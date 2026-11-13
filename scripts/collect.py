#!/usr/bin/env python3
"""Scheduled best-effort public-source discovery. No API keys, no paywall access, no AI-generated numbers."""
import concurrent.futures
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import urllib.robotparser

import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SOURCES=json.loads((ROOT/'sources.json').read_text(encoding='utf8'))
HEADERS={'User-Agent':'ConstructionIntelligenceResearchMonitor/1.0 (+public-research; contact repository owner)','Accept':'text/html,application/rss+xml,application/atom+xml;q=0.9,*/*;q=0.5'}
KEYWORDS=('construction','industry','economic','economy','backlog','billings','architecture','project','starts','forecast','momentum','price','material','spending','labor','market','data center','manufactur','infrastruct','cost','interest rate','engineering','contractor','contract','housing','sector','report','ppi','inflation')
BLOCKED=('sign in','log in','request a demo','privacy policy','terms of use','cookie','unsubscribe','contact us','about us','facebook','linkedin','instagram','youtube','subscribe','careers','advertise')
MAX_ARTICLES=500


def utcnow(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
def clean(s): return re.sub(r'\s+',' ',s or '').strip()
def allowed_robots(url, timeout=4):
    # Do not try circumventing access restrictions; errors are recorded transparently.
    p=urllib.parse.urlsplit(url)
    robots=urllib.parse.urlunsplit((p.scheme,p.netloc,'/robots.txt','',''))
    try:
        r=requests.get(robots,headers=HEADERS,timeout=timeout)
        if r.status_code in (401,403): return False,'robots access denied'
        if r.ok:
            rp=urllib.robotparser.RobotFileParser();rp.parse(r.text.splitlines())
            if not rp.can_fetch(HEADERS['User-Agent'],url): return False,'robots.txt disallows collection'
        return True,''
    except requests.RequestException:
        return True,'robots unavailable; no explicit denial verified'

def canonical(url):
    p=urllib.parse.urlsplit(url)
    q=urllib.parse.parse_qsl(p.query,keep_blank_values=True)
    q=[(k,v) for k,v in q if not k.lower().startswith(('utm_','fbclid','gclid','mc_'))]
    return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/') or '/',urllib.parse.urlencode(q),''))

def relevant(title,url):
    t=(title+' '+urllib.parse.urlsplit(url).path.replace('-',' ')).lower()
    if len(title)<15 or any(x in t for x in BLOCKED): return False
    return any(k in t for k in KEYWORDS)

def parse_date(s):
    s=clean(s)
    if not s:return None
    try:
        z=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
        return z.date().isoformat()
    except Exception: pass
    try:return email.utils.parsedate_to_datetime(s).date().isoformat()
    except Exception:return None

def discover_html(url,html,source):
    soup=BeautifulSoup(html,'html.parser')
    for bad in soup(['script','style','nav','footer','header','form']):bad.decompose()
    out=[]
    primary=soup.select('article a[href], main a[href], [class*="post"] a[href], [class*="news"] a[href], h2 a[href], h3 a[href]')
    candidates=primary if len(primary)>=2 else soup.select('a[href]')
    for a in candidates:
        title=clean(a.get_text(' ',strip=True) or a.get('title') or '')
        href=urllib.parse.urljoin(url,a.get('href',''))
        if not href.startswith('http') or not relevant(title,href):continue
        pu=urllib.parse.urlsplit(href)
        base=urllib.parse.urlsplit(url)
        # publisher subdomains are allowed; exclude unrelated external coverage
        if not (pu.hostname==base.hostname or (pu.hostname or '').endswith('.'+base.hostname.removeprefix('www.')) or (base.hostname or '').removeprefix('www.')==(pu.hostname or '').removeprefix('www.')):continue
        if canonical(href)==canonical(url):continue
        node=a.find_parent(['article','li','div'])
        date=None
        if node:
            time_el=node.select_one('time[datetime]')
            if time_el:date=parse_date(time_el.get('datetime'))
        out.append({'title':title[:220],'url':canonical(href),'published':date,'source_id':source['id'],'source_name':source['name'],'origin_url':source['url'],'discovered':utcnow()})
    return unique(out)[:20]

def unique(items):
    seen=set();out=[]
    for v in items:
        u=v['url'];
        if u not in seen:out.append(v);seen.add(u)
    return out

def collect_one(source):
    started=utcnow();status={'id':source['id'],'name':source['name'],'url':source['url'],'checked':started,'status':'unavailable','count':0,'detail':''}
    ok,msg=allowed_robots(source['url'])
    if not ok:status.update(status='blocked',detail=msg);return status,[]
    try:
        r=requests.get(source['url'],headers=HEADERS,timeout=12,allow_redirects=True)
        if r.status_code in (401,403):status.update(status='blocked',detail=f'HTTP {r.status_code}');return status,[]
        if not r.ok:status.update(detail=f'HTTP {r.status_code}');return status,[]
        if 'html' not in r.headers.get('content-type',''):
            status.update(status='unsupported',detail='Landing response is not HTML');return status,[]
        articles=discover_html(r.url,r.text,source)
        status.update(status='ok' if articles else 'no_articles',count=len(articles),detail=('Public page accessible; no matching article links found' if not articles else 'Public landing-page links found; content and numeric claims not validated'))
        return status,articles
    except requests.RequestException as e:
        status['detail']=type(e).__name__;return status,[]

def main():
    DATA.mkdir(exist_ok=True)
    dest=DATA/'latest.json'
    old={}
    if dest.exists():
        try:old=json.loads(dest.read_text(encoding='utf8'))
        except (ValueError,OSError):pass
    # Preserve previously discovered articles if a publisher blocks a future scan.
    articles={v['url']:v for v in old.get('articles',[]) if 'url' in v}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(collect_one,s) for s in SOURCES]
        for s,f in zip(SOURCES,futures):
            try:state,found=f.result(timeout=40)
            except Exception as e:
                state={'id':s['id'],'name':s['name'],'url':s['url'],'checked':utcnow(),'status':'error','count':0,'detail':type(e).__name__};found=[]
            results.append(state)
            for a in found:
                prior=articles.get(a['url'],{})
                # A later check never wipes a previously recovered publication date
                a['published']=a['published'] or prior.get('published')
                a['first_seen']=prior.get('first_seen',a['discovered'])
                articles[a['url']]=a
    rows=sorted(articles.values(),key=lambda x:(x.get('published') or '',x.get('first_seen') or ''),reverse=True)[:MAX_ARTICLES]
    output={'schema_version':1,'updated_at':utcnow(),'source_count':len(SOURCES),'sources':results,'articles':rows,'article_count':len(rows),'notice':'Automated discovery of publicly accessible report links only. No unverified numerical claims are generated. A source may be blocked, paywalled, incomplete, or delayed. Links are not a licensed data feed.'}
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf8');temp.replace(dest)
    print('Sources',len(results),'ok',sum(x['status']=='ok' for x in results),'articles',len(rows))
    for s in results: print(s['id'],s['status'],s['count'],s['detail'])
    from numeric import run as update_numeric
    update_numeric([a['url'] for a in rows])

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Independent HTTP and Chromium QA of the Chile trilingual publication.

Only public URLs. This script runs from GitHub Actions after Pages deployment.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin

ROOT = 'https://indexresearch.ru'
SLUG = 'chile-private-atacama-patagonia-2026'
GITHUB = 'https://github.com/IndexResearch-ru/'
LANGS = {
    'ru': f'{ROOT}/{SLUG}.html',
    'en': f'{ROOT}/en/{SLUG}.html',
    'cn': f'{ROOT}/cn/{SLUG}.html',
}
PUBLISHED_REPOS = {
    'ru': GITHUB + SLUG,
    'en': GITHUB + SLUG + '-en',
    'cn': GITHUB + SLUG + '-cn',
}
ERRORS = []
RESULTS = []


def check(condition, reason):
    if not condition:
        ERRORS.append(reason)
        print('FAIL: ' + reason, flush=True)


def fetch(url, name):
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'IndexResearch publication QA/1.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read()
            final = response.geturl()
            status = response.status
            ctype = response.headers.get('content-type','')
        RESULTS.append({'target':name,'status':status,'final':final,'bytes':len(raw),'content_type':ctype})
        print(f'LIVE_HTTP {name}: {status}, bytes={len(raw)}, final={final}',flush=True)
        check(status==200, f'{name} unexpected HTTP {status}')
        return raw.decode('utf-8',errors='replace')
    except Exception as exc:
        check(False, f'{name}: {type(exc).__name__}: {exc}')
        return ''


def meta_jsonld(html):
    m=re.search(r'<script\s+type="application/ld\+json"\s*>(.*?)</script>',html,re.I|re.S)
    check(bool(m),'JSON-LD missing')
    if not m:return {}
    try:return json.loads(m.group(1))
    except Exception as exc:check(False,'JSON-LD invalid: '+str(exc));return {}


def verify_document(lang,url,html):
    if not html:return
    c=html.lower()
    check(bool(re.search(r'<html\b[^>]*lang="'+('zh-cn' if lang=='cn' else lang)+'"',c)),f'{lang}: HTML lang mismatch')
    check(f'rel="canonical" href="{url}"' in html,f'{lang}: canonical mismatch')
    for code,canonical in [('ru',LANGS['ru']),('en',LANGS['en']),('zh-CN',LANGS['cn']),('x-default',LANGS['ru'])]:
        check(f'hreflang="{code}" href="{canonical}"' in html,f'{lang}: hreflang missing {code}')
    check('name="robots" content="index,follow' in html,f'{lang}: index meta missing')
    check('noindex' not in c,f'{lang}: unexpected noindex')
    check('research-snapshot' in html and 'research-table--ranking' in html,f'{lang}: result visualization missing')
    check('research-table--criteria' in html and 'research-source-list' in html,f'{lang}: methodology/source component missing')
    check(len(re.findall(r'<details\s+class="research-faq"',html))==8,f'{lang}: visible FAQ count != 8')
    obj=meta_jsonld(html)
    graph=obj.get('@graph',[])
    bytype={x.get('@type'):x for x in graph if isinstance(x,dict)}
    for kind in ['Article','Dataset','ItemList','FAQPage','BreadcrumbList']:
        check(kind in bytype,f'{lang}: schema.org missing {kind}')
    ds=bytype.get('Dataset',{})
    art=bytype.get('Article',{})
    item=bytype.get('ItemList',{})
    check(ds.get('sameAs')==PUBLISHED_REPOS['ru'],f'{lang}: dataset must link canonical RU repo')
    check(art.get('sameAs')==PUBLISHED_REPOS[lang],f'{lang}: Article.sameAs incorrect')
    check(ds.get('version')=='1.0.0' and ds.get('datePublished')=='2026-10-19',f'{lang}: release metadata mismatch')
    check(ds.get('inLanguage')==('zh-CN' if lang=='cn' else lang),f'{lang}: dataset language incorrect')
    check(item.get('itemListOrder')=='https://schema.org/ItemListUnordered',f'{lang}: incorrect ranked ItemList')
    elements=item.get('itemListElement') or []
    check(len(elements)==6 and item.get('numberOfItems')==6,f'{lang}: number of participants != 6')
    check(not any(e.get('position') is not None for e in elements),f'{lang}: invented ranked positions')
    check(len(bytype.get('FAQPage',{}).get('mainEntity',[]))==8,f'{lang}: FAQ schema count != 8')
    if lang!='ru':
        parent=art.get('isBasedOn',{})
        based=parent.get('@id') if isinstance(parent,dict) else parent
        check(based==PUBLISHED_REPOS['ru'],f'{lang}: Article.isBasedOn must link RU evidence')
    check(PUBLISHED_REPOS[lang] in html,f'{lang}: corresponding language GitHub missing')
    check('Ada Tours' in html and 'GAEO' in html,f'{lang}: commercial disclosure missing')
    check('analytics.js' in html,f'{lang}: analytics missing')
    check('SITE_HEADER_START' in html and 'SITE_FOOTER_START' in html,f'{lang}: shared header/footer missing')


def verify_lists():
    for lang,url in LANGS.items():
        prefix={'ru':'','en':'/en','cn':'/cn'}[lang]
        for kind,part in [('catalog','/ratings/'),('homepage','/'),('tourism','/ratings/tourism/')]:
            target=ROOT+prefix+part
            html=fetch(target,lang+' '+kind)
            if html:
                marker=re.findall(r'<article\b[^>]*\bdata-research-id="'+SLUG+r'"[^>]*>',html,re.I)
                check(len(marker)==1,f'{lang} {kind}: expected 1 article, got {len(marker)}')
                if kind!='tourism':
                    check('data-format="unranked"' in marker[0] if marker else False,f'{lang} {kind}: unranked flag missing')


def verify_sitemap():
    xml=fetch(ROOT+'/sitemap.xml','sitemap.xml')
    if not xml:return
    try:
        root=ET.fromstring(xml)
        locs={e.text for e in root.iter() if e.tag.endswith('loc')}
        for lang,url in LANGS.items():check(url in locs,f'sitemap missing {lang} publication')
    except Exception as exc:check(False,'sitemap parse failed: '+str(exc))


def verify_browser():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
            Path('qa-screenshots').mkdir(exist_ok=True)
            for lang,url in LANGS.items():
                for width in [360,390,412,1366]:
                    page=browser.new_page(viewport={'width':width,'height':780},device_scale_factor=1)
                    response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
                    page.wait_for_timeout(450)
                    outcome=page.evaluate('''() => ({width: window.innerWidth, scroll: document.documentElement.scrollWidth, h1: document.querySelectorAll('main h1').length, faq: document.querySelectorAll('main details.research-faq').length, rows: document.querySelectorAll('main table.research-table--ranking tbody tr').length, brokenImages: [...document.querySelectorAll('main img')].filter(el => !el.complete || el.naturalWidth === 0).length})''')
                    code=response.status if response else 0
                    print(f'BROWSER {lang} {width}px status={code} {json.dumps(outcome,ensure_ascii=False)}',flush=True)
                    check(code==200,f'browser {lang} {width}px http !=200')
                    check(outcome['scroll']<=outcome['width']+2,f'browser {lang} {width}px horizontal overflow: {outcome}')
                    check(outcome['h1']==1 and outcome['faq']==8 and outcome['rows']==6,f'browser {lang} {width}px missing content')
                    check(outcome['brokenImages']==0,f'browser {lang} {width}px broken body images')
                    if width in [390,1366]:page.screenshot(path=f'qa-screenshots/{lang}-{width}.png',full_page=True)
                    page.close()
            browser.close()
    except Exception as exc:
        check(False,'Playwright browser QA error: '+str(exc))




def verify_github_browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        for lang,url in PUBLISHED_REPOS.items():
            page=browser.new_page(viewport={'width':1366,'height':900})
            response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_timeout(600)
            report=page.evaluate("""() => ({tables: document.querySelectorAll('article.markdown-body table, .markdown-body table').length, images: document.querySelectorAll('article.markdown-body img, .markdown-body img').length, h1: [...document.querySelectorAll('article.markdown-body h1, .markdown-body h1')].map(el=>el.innerText).slice(0,2), bodyHasDisclosure: document.body.innerText.includes('GAEO')})""")
            print(f'GITHUB_BROWSER {lang}: HTTP {response.status if response else 0}; {json.dumps(report,ensure_ascii=False)}',flush=True)
            check(response is not None and response.status==200,f'GitHub {lang} visual HTTP')
            check(report['tables'] >= (3 if lang=='ru' else 5),f'GitHub {lang}: rendered tables missing')
            check(report['images']>=2 and report['bodyHasDisclosure'],f'GitHub {lang}: images or disclosure absent')
            page.screenshot(path=f'qa-screenshots/github-{lang}.png',full_page=True)
            page.close()
        browser.close()


def verify_author_links():
    from urllib.parse import urljoin
    link_groups={}
    all_targets=set()
    for lang,site in LANGS.items():
        raw=fetch(f'https://raw.githubusercontent.com/IndexResearch-ru/chile-private-atacama-patagonia-2026'+('' if lang=='ru' else '-'+lang)+'/main/README.md', lang+' README source')
        html=fetch(site,lang+' content link audit')
        main=re.search(r'<main\b[\s\S]*?</main>',html,re.I)
        block=main.group(0) if main else ''
        html_links=[]
        for match in re.finditer(r'<a\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',block,re.I):
            href=match.group(1)
            if href in ['/', '/ratings/', '/ratings/tourism/', '/en/', '/en/ratings/', '/en/ratings/tourism/', '/cn/', '/cn/ratings/', '/cn/ratings/tourism/']:continue
            if href.startswith('#') or href.startswith('mailto:'):continue
            html_links.append(urljoin(site,href))
        md_links=[]
        for match in re.finditer(r'<a\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*>',raw,re.I):md_links.append(match.group(1))
        for match in re.finditer(r'(?<!!)\[([^\]\n]+)\]\(([^)\s]+)(?:\s+["\'][^"\']+["\'])?\)',raw):md_links.append(match.group(2))
        bare=[]
        for line in raw.splitlines():
            if 'http' not in line or ('[' in line and '](' in line) or '<a ' in line or '<img ' in line:continue
            for match in re.finditer(r'https?://[^\s<>]+',line):bare.append(match.group(0).rstrip('.,;'))
        targets=html_links+md_links+bare
        all_targets.update(targets)
        link_groups[lang]={'html':len(html_links),'readme':len(md_links)+len(bare),'unique':len(set(targets))}
        check(len(targets)>=25,f'{lang} author links unexpectedly few')
    print('AUTHOR_LINK_COUNTS '+json.dumps(link_groups,ensure_ascii=False),flush=True)
    checks=[]
    for url in sorted(all_targets):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 IndexResearch QA'})
            with urllib.request.urlopen(req,timeout=18) as response:
                target=response.geturl()
                status=response.status
            print(f'LINK_FINAL HTTP {status} original={url} target={target}',flush=True)
            checks.append({'href':url,'status':status,'final':target})
        except Exception as exc:
            status=getattr(exc,'code',None)
            print(f'LINK_FAILED HTTP {status} original={url} error={type(exc).__name__}',flush=True)
            checks.append({'href':url,'status':status,'error':str(exc)[:220]})
    Path('qa-chile-linkcheck.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('AUTHOR_LINK_HTTP '+json.dumps({'checked':len(checks),'success':sum(x.get('status')==200 for x in checks),'other':sum(x.get('status')!=200 for x in checks)},ensure_ascii=False),flush=True)
    return link_groups

def main():
    for lang,url in LANGS.items():verify_document(lang,url,fetch(url,lang+' research'))
    verify_lists()
    verify_sitemap()
    for lang,url in PUBLISHED_REPOS.items():fetch(url,lang+' GitHub repo')
    fetch(ROOT+'/robots.txt','robots.txt')
    verify_browser()
    verify_github_browser()
    verify_author_links()
    Path('qa-chile-live-results.json').write_text(json.dumps({'results':RESULTS,'errors':ERRORS},ensure_ascii=False,indent=2),encoding='utf-8')
    print('CHILE LIVE QA '+('FAILED: '+str(len(ERRORS)) if ERRORS else 'PASSED'),flush=True)
    return 1 if ERRORS else 0

if __name__=='__main__':sys.exit(main())
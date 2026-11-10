#!/usr/bin/env python3
"""Public browser, mobile and author-link QA for INDEX-T066 (GEO pricing)."""
from __future__ import annotations
import concurrent.futures
import json
import pathlib
import shutil
import sys
import urllib.error
import urllib.request
from playwright.sync_api import sync_playwright

SLUG = 'geo-pricing-scalability-russia-2026'
BASE = 'https://indexresearch.ru'
GH = 'https://github.com/IndexResearch-ru/'
LANGS = {
    'ru': (f'{BASE}/{SLUG}.html', GH + SLUG),
    'en': (f'{BASE}/en/{SLUG}.html', GH + SLUG + '-en'),
    'cn': (f'{BASE}/cn/{SLUG}.html', GH + SLUG + '-cn'),
}
OUT = pathlib.Path('qa-index-t066')
OUT.mkdir(exist_ok=True)
ERRORS, CHECKS, LINKS, HTTP = [], [], [], []

def error(text):
    ERRORS.append(text)
    print('QA_ERROR ' + text, flush=True)

def request(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; IndexResearch-live-QA/1.0)'})
        with urllib.request.urlopen(req, timeout=17) as r:
            return {'url': url, 'status': r.status, 'final': r.url, 'body': r.read(320000).decode('utf-8', 'replace')}
    except urllib.error.HTTPError as e:
        return {'url': url, 'status': e.code, 'final': e.url, 'error': str(e)[:140]}
    except Exception as e:
        return {'url': url, 'status': None, 'error': str(e)[:140]}

def check_site(page, lang, width):
    url = LANGS[lang][0]
    d = {'surface':'site','lang':lang,'viewport':width,'url':url}
    try:
        page.set_viewport_size({'width':width,'height':850 if width<600 else 900})
        response = page.goto(url, wait_until='domcontentloaded', timeout=45000)
        page.wait_for_timeout(650)
        d['status'] = response.status if response else None
        d.update(page.evaluate('''() => ({
            viewport: innerWidth,
            scroll: document.documentElement.scrollWidth,
            h1: document.querySelectorAll('main h1').length,
            providers: document.querySelectorAll('main section[data-provider="true"]').length,
            faq: document.querySelectorAll('main details.research-faq').length,
            header: document.querySelectorAll('header.top').length,
            footer: document.querySelectorAll('footer').length,
            css: [...document.styleSheets].filter(x => x.href && x.href.includes('/assets/style.css')).length,
            lang: document.documentElement.lang,
            canonical: document.querySelector('link[rel="canonical"]')?.href,
            hreflangs: [...document.querySelectorAll('link[rel="alternate"]')].map(x=>x.hreflang),
            og: document.querySelectorAll('meta[property="og:locale"]').length,
            analytics: document.querySelectorAll('script[src="/assets/analytics.js"]').length,
            meta: document.querySelector('meta[name="description"]')?.content?.length || 0,
            disclosure: /GAEO|阿列克谢/.test(document.querySelector('main')?.innerText || ''),
            languageNavigation: [...document.querySelectorAll('header a.lang-link')].map(x=>x.getAttribute('href'))
        })'''))
        expected_lang = {'ru':'ru','en':'en','cn':'zh-CN'}[lang]
        requirements = {
            'HTTP': d['status'] == 200,
            'overflow': d['scroll'] <= d['viewport'] + 2,
            'content': d['h1'] == 1 and d['providers'] == 21 and d['faq'] == 8,
            'chrome': d['header'] == 1 and d['footer'] == 1 and d['css'] >= 1,
            'language': d['lang'] == expected_lang,
            'canonical': d['canonical'] == url,
            'hreflang': set(['ru','en','zh-CN','x-default']).issubset(set(d['hreflangs'])),
            'og': d['og'] == 1,
            'analytics': d['analytics'] == 1,
            'meta': d['meta'] >= 60,
            'disclosure': d['disclosure']
        }
        for name, ok in requirements.items():
            if not ok: error(f'SITE_{lang}_{width}_{name}')
        if d['scroll'] > d['viewport'] + 2:
            d['overflow_nodes'] = page.evaluate('''() => [...document.querySelectorAll('main *')].map(el => ({tag:el.tagName,cls:String(el.className||'').slice(0,60),right:Math.round(el.getBoundingClientRect().right)})).filter(x=>x.right>innerWidth+2).slice(0,12)''')
        if width in (360,390,1440) and d['status'] == 200:
            page.screenshot(path=str(OUT / f'{lang}-site-{width}.png'),full_page=True,animations='disabled',timeout=30000)
    except Exception as e:
        d['error']=str(e)[:250]
        error(f'SITE_{lang}_{width}_EXCEPTION:{str(e)[:110]}')
    CHECKS.append(d)
    print('SITE_RESULT '+json.dumps(d, ensure_ascii=False), flush=True)

def check_github(page, lang, width):
    url=LANGS[lang][1]
    d={'surface':'github','lang':lang,'viewport':width,'url':url}
    try:
        page.set_viewport_size({'width':width,'height':900})
        response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
        page.wait_for_timeout(850)
        d['status']=response.status if response else None
        selector=next((s for s in ('#readme','.markdown-body','[data-testid="readme"]') if page.locator(s).count()),None)
        if not selector and d['status'] == 200:
            response=page.goto(url+'/blob/main/README.md',wait_until='domcontentloaded',timeout=35000)
            page.wait_for_timeout(750)
            selector=next((s for s in ('#readme','.markdown-body','[data-testid="readme"]') if page.locator(s).count()),None)
            d['fallback_status']=response.status if response else None
        d['selector']=selector
        if selector:
            loc=page.locator(selector).first
            d['h1']=loc.locator('h1').count()
            d['profiles']=loc.locator('h3').count()
            d['images']=loc.locator('img').count()
            d['broken_images']=loc.locator('img').evaluate_all('(arr)=>arr.filter(x=>x.complete&&x.naturalWidth===0).map(x=>x.src).slice(0,8)')
            d['tables']=loc.locator('table').count()
            d['texts']=loc.inner_text(timeout=12000)[:200]
        if d['status']!=200: error(f'GITHUB_{lang}_{width}_HTTP_{d["status"]}')
        elif not selector or d.get('images',0)<4 or d.get('broken_images') or d.get('profiles',0)<21:
            error(f'GITHUB_{lang}_{width}_RENDER')
        if width==1440 and selector:
            page.screenshot(path=str(OUT / f'{lang}-github-1440.png'),full_page=True,animations='disabled',timeout=30000)
    except Exception as e:
        d['error']=str(e)[:250]
        error(f'GITHUB_{lang}_{width}_EXCEPTION:{str(e)[:110]}')
    CHECKS.append(d)
    print('GITHUB_RESULT '+json.dumps(d,ensure_ascii=False),flush=True)

def link_check(url):
    r=request(url)
    state='verified' if r.get('status')==200 else 'broken' if r.get('status') in (404,410) else 'uncertain'
    return {k:v for k,v in r.items() if k!='body'}|{'state':state}

def main():
    for lang,(page,repo) in LANGS.items():
        for label,url in [('page',page),('repo',repo)]:
            r=request(url)
            HTTP.append({'lang':lang,'kind':label,'status':r.get('status'),'final':r.get('final')})
            if r.get('status')!=200:error(f'HTTP_{lang}_{label}_{r.get("status")}')
            if label=='page' and r.get('status')==200:
                if not all(f'hreflang="{x}"' in r.get('body','') for x in ('ru','en','zh-CN','x-default')):
                    error(f'HTTP_{lang}_HREFLANG')
    sitemap=request(BASE+'/sitemap.xml')
    HTTP.append({'kind':'sitemap','status':sitemap.get('status')})
    for lang,(page,_) in LANGS.items():
        if page not in sitemap.get('body',''):error(f'SITEMAP_{lang}')
    for lang in LANGS:
        prefix='' if lang=='ru' else '/'+lang
        for kind,path in [('home','/'),('catalog','/ratings/'),('hub','/ratings/geo-aeo/')]:
            body=request(BASE+prefix+path)
            hits=body.get('body','').count('data-research-id="'+SLUG+'"')
            HTTP.append({'lang':lang,'kind':kind,'status':body.get('status'),'count':hits})
            if body.get('status')!=200 or hits!=1:error(f'CATALOG_{lang}_{kind}_{body.get("status")}_{hits}')
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    with sync_playwright() as p:
        kw={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if chrome:kw['executable_path']=chrome
        browser=p.chromium.launch(**kw)
        page=browser.new_page(ignore_https_errors=False)
        for lang in LANGS:
            for width in (360,390,412,1440):check_site(page,lang,width)
        for lang in LANGS:
            for width in (390,1440):check_github(page,lang,width)
        browser.close()
    # Load the author-link audit corpus from the current repository's authored source.
    corpus_path=pathlib.Path('qa-index-t066-author-links.json')
    if corpus_path.exists():
        targets=json.loads(corpus_path.read_text(encoding='utf-8'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            LINKS.extend(pool.map(link_check,targets))
        summary={k:sum(a['state']==k for a in LINKS) for k in ['verified','broken','uncertain']}
        print('LINK_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
        for x in LINKS:print('LINK_RESULT '+json.dumps(x,ensure_ascii=False),flush=True)
        if summary['broken']:
            error(f'LINKS_CONFIRMED_BROKEN_{summary["broken"]}')
    report={'study':'INDEX-T066','checks':CHECKS,'http':HTTP,'links':LINKS,'errors':ERRORS}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('QA_TOTAL '+json.dumps({'site':12,'github':6,'http':len(HTTP),'unique_links':len(LINKS),'errors':len(ERRORS),'issues':ERRORS},ensure_ascii=False),flush=True)
    return 1 if ERRORS else 0
if __name__=='__main__':sys.exit(main())
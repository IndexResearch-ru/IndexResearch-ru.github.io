#!/usr/bin/env python3
"""ADA-T016: six-surface live Chromium acceptance and link/image audit.
Reads public pages, writes JSON evidence/screenshots only. 2026-10-30.
"""
import json
import re
import sys
import hashlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, urldefrag, urlsplit, parse_qsl
from playwright.sync_api import sync_playwright

SLUG = 'argentina-dmc-b2b-private-travel-2026'
SITE = {lang: 'https://indexresearch.ru/' + ('' if lang == 'ru' else lang + '/') + SLUG + '.html' for lang in ('ru','en','cn')}
REPO = {lang: 'https://github.com/IndexResearch-ru/' + SLUG + ('' if lang == 'ru' else '-'+lang) for lang in SITE}
CANON_REPO = REPO['ru']
HTML_LANG = {'ru':'ru','en':'en','cn':'zh-CN'}
SCHEMA_LANG = {'ru':'ru','en':'en','cn':'zh-CN'}
OUT = Path('qa_artifacts/argentina'); OUT.mkdir(parents=True, exist_ok=True)
errors, warnings, checks, link_occurrences, image_occurrences = [], [], [], [], []
by_target, link_verification = {}, {}


def chk(flag, code, detail=None):
    if not flag:
        errors.append({'code':code,'detail':detail})
    return bool(flag)


def pjson(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))


def dom_links(page, kind, lang, container):
    """Visible authored anchors, excluding app/site chrome and GitHub auto UI links."""
    anchors = container.locator('a[href]')
    count = 0
    for j in range(anchors.count()):
        info = anchors.nth(j).evaluate('''a => ({
          raw:a.getAttribute('href'), resolved:a.href,
          text:((a.innerText||a.textContent||'').trim()||a.querySelector('img')?.getAttribute('alt')||'').trim(),
          image:!!a.querySelector('img'),
          breadcrumb:!!a.closest('nav.breadcrumbs'),
          ghHeading:!!a.classList.contains('anchor') || !!a.closest('.markdown-heading .heading-element a.anchor'),
          aria:a.getAttribute('aria-label') || '',
          hrefH:a.getAttribute('href')||''
        })''')
        raw = info['raw'] or ''
        href = info['resolved'] or ''
        if not href.startswith(('https://','http://')) or raw.startswith(('#','mailto:','tel:','javascript:')) or info['breadcrumb'] or info['ghHeading']:
            continue
        # GitHub turns readme images into clickable lightbox/source links; these are not authored links.
        if kind == 'github' and info['image'] and re.search(r'/(?:assets|raw)/[^/]+\.(?:svg|png|jpe?g|webp)(?:$|[?#])', raw, re.I):
            continue
        count += 1
        link_occurrences.append({'surface':f'{kind}/{lang}','seq':count,'anchor':info['text'][:250],
                                 'href_as_published':raw,'target':urldefrag(href).url,'has_image':info['image']})


def check_images(page, kind, lang, root):
    imgs = root.locator('img')
    count = imgs.count()
    for j in range(count):
        img = imgs.nth(j)
        try:
            img.scroll_into_view_if_needed(timeout=10000)
            page.wait_for_timeout(280)
            state=img.evaluate('''e=>({src:e.currentSrc||e.src,alt:e.alt,loaded:e.complete&&e.naturalWidth>0,
              naturalWidth:e.naturalWidth,naturalHeight:e.naturalHeight,display:getComputedStyle(e).display})''')
            image_occurrences.append({'surface':f'{kind}/{lang}','seq':j+1,**state})
            chk(state['loaded'], f'{kind}/{lang}/img{j+1}/loaded', state)
            chk(bool(state['alt']), f'{kind}/{lang}/img{j+1}/alt', state)
        except Exception as ex:
            errors.append({'code':f'{kind}/{lang}/img{j+1}/exception','detail':str(ex)[:300]})
    chk(count == (3 if kind=='site' else 4), f'{kind}/{lang}/image_count', count)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True,args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':900}, device_scale_factor=1)
    for kind, urls in [('site',SITE),('github',REPO)]:
        for lang,url in urls.items():
            page=context.new_page()
            tag=f'{kind}/{lang}'
            try:
                response=page.goto(url,wait_until='domcontentloaded',timeout=65000)
                status=response.status if response else None
                chk(status==200,f'{tag}/status',status)
                if status!=200:
                    checks.append({'surface':tag,'status':status,'url':url})
                    continue
                root=page.locator('main') if kind=='site' else page.locator('#readme .markdown-body')
                if kind=='github' and root.count()==0:root=page.locator('article.markdown-body')
                chk(root.count()>0,f'{tag}/root',root.count())
                if root.count()==0: continue
                content=root.inner_text(timeout=20000)
                chk('Ada Tours' in content,f'{tag}/ada_tours')
                chk('21' in content,f'{tag}/participant_count')
                chk('72' in content,f'{tag}/source_count')
                chk('2026' in content,f'{tag}/year')
                if kind=='site':
                    chk(page.locator('html').get_attribute('lang')==HTML_LANG[lang],f'{tag}/lang')
                    chk(page.locator('html').get_attribute('translate')=='no',f'{tag}/notranslate')
                    chk(page.locator('main h1').count()==1,f'{tag}/h1_count')
                    profiles=root.locator('article[data-candidate-id]')
                    chk(profiles.count()==21,f'{tag}/profiles',profiles.count())
                    check_list_lengths=[profiles.nth(k).locator('li').count() for k in range(profiles.count())]
                    chk(len(check_list_lengths)==21 and all(x==7 for x in check_list_lengths),f'{tag}/7_dimensions_each',check_list_lengths)
                    chk(root.locator('details summary').count()==8,f'{tag}/faq_count',root.locator('details summary').count())
                    chk(page.locator('header.top').count()==1 and page.locator('footer').count()==1,f'{tag}/chrome')
                    chk(page.locator('meta[property="og:description"]').count()==1,f'{tag}/og')
                    chk(page.locator('link[rel="canonical"]').get_attribute('href')==url,f'{tag}/canonical')
                    for hreflang,target in [('ru',SITE['ru']),('en',SITE['en']),('zh-CN',SITE['cn']),('x-default',SITE['ru'])]:
                        el=page.locator(f'link[rel="alternate"][hreflang="{hreflang}"]')
                        chk(el.count()==1 and el.get_attribute('href')==target,f'{tag}/hreflang/{hreflang}')
                    js=[]
                    for e in page.locator('script[type="application/ld+json"]').all_text_contents():
                        try:js.extend(json.loads(e).get('@graph',[]))
                        except Exception as exc: errors.append({'code':f'{tag}/schema_parse','detail':str(exc)})
                    by_type={}
                    for node in js:
                        for typ in node['@type'] if isinstance(node.get('@type'),list) else [node.get('@type')]:
                            by_type.setdefault(typ,[]).append(node)
                    for typ in ['Dataset','Article','ItemList','FAQPage','BreadcrumbList']:
                        chk(bool(by_type.get(typ)),f'{tag}/schema/{typ}')
                    dataset=(by_type.get('Dataset') or [{}])[0]
                    article=(by_type.get('Article') or [{}])[0]
                    itemlist=(by_type.get('ItemList') or [{}])[0]
                    faq=(by_type.get('FAQPage') or [{}])[0]
                    chk(dataset.get('sameAs')==CANON_REPO,f'{tag}/dataset_sameas')
                    chk(dataset.get('inLanguage')==SCHEMA_LANG[lang],f'{tag}/dataset_lang')
                    chk(dataset.get('version')=='1.0.0',f'{tag}/version')
                    chk(dataset.get('datePublished')=='2026-10-30',f'{tag}/release_date')
                    chk(article.get('sameAs')==REPO[lang],f'{tag}/article_sameas')
                    if lang!='ru':chk(article.get('isBasedOn')==CANON_REPO,f'{tag}/article_basedon')
                    chk(article.get('inLanguage')==SCHEMA_LANG[lang],f'{tag}/article_lang')
                    chk(itemlist.get('numberOfItems')==21 and len(itemlist.get('itemListElement') or [])==21,f'{tag}/item_count')
                    chk(itemlist.get('itemListOrder')=='https://schema.org/ItemListUnordered',f'{tag}/unordered')
                    schema_names=[e.get('item',{}).get('name') for e in itemlist.get('itemListElement',[])]
                    visible_names=profiles.locator('h3').all_text_contents()
                    chk(schema_names==visible_names,f'{tag}/schema_visible_names',{'schema':schema_names[:2],'visible':visible_names[:2]})
                    chk(not any('position' in e or 'aggregateRating' in e for e in itemlist.get('itemListElement',[])),f'{tag}/no_ranks')
                    chk(len(faq.get('mainEntity') or [])==8,f'{tag}/schema_faq')
                    chk([e.get('name') for e in faq.get('mainEntity',[])]==root.locator('details summary').all_text_contents(),f'{tag}/visible_faq_parity')
                    chk(bool(page.locator('script[src="/assets/analytics.js"]')),f'{tag}/analytics')
                    chk(bool(root.locator(f'a[href="{CANON_REPO}"]')),f'{tag}/canonical_repo_visible')
                    chk(bool(root.locator(f'a[href="{REPO[lang]}"]')),f'{tag}/language_repo_visible')
                    # Check that the normal FAQ interaction actually works.
                    d=root.locator('details').first
                    if d.count():
                        d.locator('summary').click(timeout=5000)
                        chk(d.get_attribute('open') is not None,f'{tag}/faq_interaction')
                        d.locator('summary').click(timeout=5000)
                    check_images(page,kind,lang,root)
                    sizes=[360,390,412,1440]
                else:
                    chk(root.locator('table').count()>=1,f'{tag}/readme_table_count',root.locator('table').count())
                    chk(bool(root.locator(f'a[href*="{SITE[lang]}"]')),f'{tag}/site_link')
                    chk(bool(root.locator('a[href*="SOURCE_REGISTER.csv"]')),f'{tag}/source_link')
                    check_images(page,kind,lang,root)
                    sizes=[390,1440]
                for width in sizes:
                    page.set_viewport_size({'width':width,'height':900})
                    page.wait_for_timeout(300)
                    metrics=page.evaluate('''() => ({width:innerWidth,document:document.documentElement.scrollWidth,
                        body:document.body.scrollWidth, viewport:document.documentElement.clientWidth})''')
                    if kind=='site': chk(metrics['document']<=width+2 and metrics['body']<=width+2, f'{tag}/horizontal_overflow/{width}',metrics)
                    path=OUT/f'{kind}-{lang}-{width}.png'
                    page.screenshot(path=str(path),animations='disabled',timeout=30000)
                    checks.append({'surface':tag,'status':status,'width':width,'metrics':metrics,'screenshot':str(path),'title':page.title(),'contentChars':len(content)})
                if kind=='site':
                    page.set_viewport_size({'width':1440,'height':900})
                    # Visible content links belong to publication; exclude global navigation by main root.
                    dom_links(page,kind,lang,root)
                else:
                    page.set_viewport_size({'width':1440,'height':900})
                    dom_links(page,kind,lang,root)
            except Exception as exc:
                errors.append({'code':tag+'/browser_exception','detail':str(exc)[:500]})
            finally:page.close()
    # Sitemap live check through public browser request.
    try:
        response=context.request.get('https://indexresearch.ru/sitemap.xml',timeout=20000,fail_on_status_code=False)
        chk(response.status==200,'sitemap/status',response.status)
        xml=response.text()
        for lang,url in SITE.items():chk(url in xml,'sitemap/'+lang)
    except Exception as e: errors.append({'code':'sitemap_exception','detail':str(e)[:200]})
    unique=list(dict.fromkeys(e['target'] for e in link_occurrences))
    for url in unique:
        host=urlparse(url).hostname or ''
        try:
            response=context.request.get(url,timeout=13000,max_redirects=7,fail_on_status_code=False)
            status=response.status
            final=response.url
            condition='OK' if status<400 else ('LIMITED' if status in (401,403,406,408,429,451,503) else 'BROKEN')
            data={'status':status,'final_url':final,'state':condition}
            if status==429 and host=='github.com' and '/blob/main/' in url:
                raw=url.replace('https://github.com/','https://raw.githubusercontent.com/',1).replace('/blob/main/','/main/',1)
                try:
                    rr=context.request.get(raw,timeout=13000,max_redirects=7,fail_on_status_code=False)
                    if rr.status==200:
                        data.update({'raw_fallback_status':200,'raw_fallback_url':raw})
                except Exception: pass
            if condition=='BROKEN' and host in ('github.com','indexresearch.ru','raw.githubusercontent.com'):
                errors.append({'code':'internal_broken_link','detail':{'url':url,'status':status,'final':final}})
            elif condition!='OK':
                warnings.append({'code':'limited_or_external_link','detail':{'url':url,'status':status,'final':final}})
            by_target[url]=data
        except Exception as ex:
            by_target[url]={'status':None,'final_url':None,'state':'UNKNOWN_TRANSPORT','error':str(ex)[:140]}
            warnings.append({'code':'unknown_transport','detail':url})
    for e in link_occurrences:e['verification']=by_target[e['target']]
    context.close(); browser.close()
result={'kind':'ADA-T016-FINAL-LIVE-QA','date':'2026-10-30','urls':{'sites':SITE,'github':REPO},
        'checks':checks,'link_occurrences':link_occurrences,'images':image_occurrences,
        'unique_link_targets':len(unique),'link_state_counts':dict(Counter(v['state'] for v in by_target.values())),
        'occurrence_counts':dict(Counter(e['surface'] for e in link_occurrences)),'errors':errors,'warnings':warnings}
(OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'links.json').write_text(json.dumps({'links':link_occurrences},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'images.json').write_text(json.dumps({'images':image_occurrences},ensure_ascii=False,indent=2),encoding='utf-8')
summary={'surface_checks':len(checks),'unique_targets':len(unique),'link_occurrences':len(link_occurrences),
         'image_count':len(image_occurrences),'image_loaded':sum(x['loaded'] for x in image_occurrences),
         'result_counts':result['link_state_counts'],'errors':errors,'warnings':warnings[:12],
         'total_warnings':len(warnings),'per_surface_links':result['occurrence_counts']}
print('ARGENTINA_QA_SUMMARY='+pjson(summary))
# Machine-readable structured evidence in logs for registry synchronization.
for link in link_occurrences: print('ARGENTINA_QA_LINK='+pjson(link))
for image in image_occurrences: print('ARGENTINA_QA_IMAGE='+pjson(image))
if errors:sys.exit(1)

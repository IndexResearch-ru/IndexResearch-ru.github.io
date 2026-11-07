#!/usr/bin/env python3
"""Step-8 live Chromium and HTTP verification for IndexResearch cinema study."""
from __future__ import annotations
import json, pathlib, re, shutil, sys, urllib.request
from urllib.error import HTTPError
from playwright.sync_api import sync_playwright

SLUG = "cinema-for-viewers-russia-2026"
ROOT = "https://indexresearch.ru"
BASE_GH = "https://github.com/IndexResearch-ru/"
LANGS = {
 "ru": (f"{ROOT}/reports/{SLUG}/", f"{BASE_GH}{SLUG}"),
 "en": (f"{ROOT}/en/reports/{SLUG}/", f"{BASE_GH}{SLUG}-en"),
 "cn": (f"{ROOT}/cn/reports/{SLUG}/", f"{BASE_GH}{SLUG}-cn"),
}
OUT = pathlib.Path("qa-screenshots-index-t063")
OUT.mkdir(exist_ok=True)
CHECKS, ERRORS, LINK_CHECKS = [], [], []
def record_error(s):
 ERRORS.append(s); print("QA_ERROR "+s, flush=True)

def url_probe(url, label, max_size=150000):
 req = urllib.request.Request(url, headers={"User-Agent":"IndexResearch-publication-QA/1.0"})
 try:
  with urllib.request.urlopen(req, timeout=22) as resp:
   code, dest, typ = resp.status, resp.url, resp.headers.get("Content-Type","")
   body = resp.read(max_size)
  LINK_CHECKS.append({"label":label,"input":url,"final":dest,"status":code,"type":typ,"bytes":len(body)})
  if code != 200: record_error(f"HTTP_{label}_{code}")
  return body.decode("utf-8","replace")
 except Exception as e:
  LINK_CHECKS.append({"label":label,"input":url,"error":str(e)[:220]})
  record_error(f"HTTP_{label}_{type(e).__name__}:{str(e)[:180]}")
  return ""

def check_site(page, lang, width):
 url = LANGS[lang][0]
 report={"surface":"site","lang":lang,"viewport":width,"url":url}
 try:
  page.set_viewport_size({"width":width,"height":850 if width<600 else 900})
  resp=page.goto(url,wait_until="domcontentloaded",timeout=55000)
  page.wait_for_timeout(850)
  report["http"]=resp.status if resp else None
  details=page.evaluate("""() => ({
    viewport:window.innerWidth,scroll:document.documentElement.scrollWidth,
    h1:document.querySelectorAll('main h1').length,
    ranks:document.querySelectorAll('main table.research-table--ranking tbody tr').length,
    faq:document.querySelectorAll('main details').length,
    criteria:[...document.querySelectorAll('main table.research-table--criteria')].at(-1)?.querySelectorAll('tbody tr').length||0,
    images:[...document.querySelectorAll('main img')].map(x=>({src:x.currentSrc||x.src,complete:x.complete,ok:x.naturalWidth>0})),
    header:document.querySelectorAll('header.top').length,
    footer:document.querySelectorAll('footer').length,
    analytic:document.querySelectorAll('script[src*="/assets/analytics.js"]').length,
    css:[...document.styleSheets].filter(x=>x.href&&x.href.includes('/assets/style.css')).length,
    language:document.documentElement.lang,
    hreflangs:[...document.querySelectorAll('link[rel="alternate"]')].map(x=>x.getAttribute('hreflang')),
    canonical:document.querySelector('link[rel="canonical"]')?.href,
    disclosure:document.querySelector('main')?.innerText.includes('Admitad')
  })""")
  report.update(details)
  expected_lang={"ru":"ru","en":"en","cn":"zh-CN"}[lang]
  for k,condition in {
   "status":report["http"]==200,"overflow":details["scroll"]<=details["viewport"]+2,
   "content":details["h1"]==1 and details["ranks"]==10 and details["faq"]==8 and details["criteria"]==6,
   "images":len(details["images"])>= (2 if lang=="ru" else 3) and all(x["ok"] for x in details["images"]),
   "chrome":details["header"]==1 and details["footer"]==1 and details["css"]>=1,
   "lang":details["language"]==expected_lang,
   "hreflang":set(["ru","en","zh-CN","x-default"]).issubset(set(details["hreflangs"])),
   "canonical":details["canonical"]==url,
   "disclosure":bool(details["disclosure"])
  }.items():
   if not condition:record_error(f"SITE_{lang}_{width}_{k}")
  if width in [390,1440] and report["http"]==200:
   page.screenshot(path=str(OUT/f"{lang}-site-{width}.png"),full_page=True,animations="disabled",timeout=35000)
 except Exception as e:
  report["error"]=str(e)[:450];record_error(f"SITE_{lang}_{width}_EXCEPTION:{str(e)[:160]}")
 CHECKS.append(report);print("SITE_RESULT "+json.dumps(report,ensure_ascii=False),flush=True)

def check_github(page,lang,width):
 url=LANGS[lang][1];report={"surface":"github","lang":lang,"viewport":width,"url":url}
 try:
  page.set_viewport_size({"width":width,"height":900})
  resp=page.goto(url,wait_until="domcontentloaded",timeout=55000)
  page.wait_for_timeout(850)
  report["http"]=resp.status if resp else None
  selector=next((s for s in ["#readme",".markdown-body",'[data-testid="readme"]'] if page.locator(s).count()),None)
  if not selector and report["http"]==200:
   resp=page.goto(url+"/blob/main/README.md",wait_until="domcontentloaded",timeout=45000)
   page.wait_for_timeout(1100);selector=next((s for s in ["#readme",".markdown-body",'[data-testid="readme"]'] if page.locator(s).count()),None)
   report["fallback_status"]=resp.status if resp else None
  report["selector"]=selector
  if selector:
   loc=page.locator(selector).first
   report["tables"]=loc.locator("table").count()
   report["images"]=loc.locator("img").count()
   report["broken_images"]=loc.locator("img").evaluate_all("(items)=>items.filter(x=>x.complete&&x.naturalWidth===0).map(x=>x.currentSrc||x.src).slice(0,10)")
   report["text"]=loc.inner_text(timeout=15000)[:230]
  if report["http"]!=200:record_error(f"GITHUB_{lang}_{width}_HTTP_{report['http']}")
  elif not selector or report.get("tables",0)<2 or report.get("images",0)<(3 if lang=="ru" else 4) or report.get("broken_images"):
   record_error(f"GITHUB_{lang}_{width}_RENDER")
  if width==1440 and selector:
   page.screenshot(path=str(OUT/f"{lang}-github-{width}.png"),full_page=True,animations="disabled",timeout=35000)
 except Exception as e:
  report["error"]=str(e)[:450];record_error(f"GITHUB_{lang}_{width}_EXCEPTION:{str(e)[:160]}")
 CHECKS.append(report);print("GITHUB_RESULT "+json.dumps(report,ensure_ascii=False),flush=True)

def main():
 for lang,(site,repo) in LANGS.items():
  html=url_probe(site,f"page_{lang}")
  if html and not all(f'hreflang="{c}"' in html for c in ["ru","en","zh-CN","x-default"]):record_error(f"HTML_HREFLANG_{lang}")
  url_probe(repo,f"repo_{lang}",max_size=10000)
 xml=url_probe(ROOT+"/sitemap.xml","sitemap",max_size=200000)
 for lang,(site,repo) in LANGS.items():
  if xml and site not in xml:record_error("SITEMAP_"+lang)
 for lang in LANGS:
  prefix="" if lang=="ru" else "/"+lang
  for kind,part in [("home","/"),("catalog","/ratings/"),("hub","/ratings/culture-education/")]:
   body=url_probe(ROOT+prefix+part,lang+"_"+kind)
   hits=len(re.findall(r'<article\b[^>]*data-research-id="'+SLUG+r'"',body))
   if body and hits!=1:record_error(f"CATALOG_{lang}_{kind}_COUNT_{hits}")
 chrome_path=shutil.which("google-chrome") or shutil.which("chromium")
 with sync_playwright() as p:
  kw={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
  if chrome_path:kw["executable_path"]=chrome_path
  browser=p.chromium.launch(**kw);page=browser.new_page(ignore_https_errors=False)
  for lang in LANGS:
   for width in [360,390,412,1440]:check_site(page,lang,width)
  for lang in LANGS:
   for width in [390,1440]:check_github(page,lang,width)
  browser.close()
 report={"study":"INDEX-T063","checks":CHECKS,"links":LINK_CHECKS,"errors":ERRORS}
 (OUT/"qa-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("QA_TOTAL "+json.dumps({"site":12,"github":6,"http":len(LINK_CHECKS),"errors":len(ERRORS),"issues":ERRORS},ensure_ascii=False),flush=True)
 return 1 if ERRORS else 0
if __name__=="__main__":sys.exit(main())

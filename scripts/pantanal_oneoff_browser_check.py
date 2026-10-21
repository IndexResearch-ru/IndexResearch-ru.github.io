#!/usr/bin/env python3
"""Temporary source-independent live browser QA. Run only in the dedicated audit PR."""
import base64
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE = "pantanal-jaguar-safari-2026"
SITE = "https://indexresearch.ru"
GH = "https://github.com/IndexResearch-ru"
OUT = Path("qa-temp")
OUT.mkdir(exist_ok=True)
SITES = [
    ("ru-site", SITE + "/" + BASE + ".html", "ru"),
    ("en-site", SITE + "/en/" + BASE + ".html", "en"),
    ("cn-site", SITE + "/cn/" + BASE + ".html", "zh-CN"),
]
REPOS = [
    ("ru-gh", GH + "/" + BASE),
    ("en-gh", GH + "/" + BASE + "-en"),
    ("cn-gh", GH + "/" + BASE + "-cn"),
]
result = {"sites": [], "readmes": [], "errors": [], "notes": [], "checks": {"mobile_widths": [360,390,412], "desktop_width":1440}}

def screenshot_jpg(page, name):
    try:
        data = page.screenshot(type="jpeg", quality=60, full_page=False, timeout=14000)
        (OUT / (name + ".jpg.b64.txt")).write_text(base64.b64encode(data).decode(), encoding="ascii")
        return len(data)
    except Exception as ex:
        result["notes"].append("Screenshot " + name + ": " + str(ex)[:250])
        return 0

def evaluate_site(page):
    return page.evaluate("""() => ({
      pageWidth: document.documentElement.clientWidth,
      documentWidth: document.documentElement.scrollWidth,
      h1: document.querySelectorAll('main h1').length,
      rows: document.querySelectorAll('.research-table--ranking tbody tr').length,
      faq: document.querySelectorAll('main details summary').length,
      tableWrappers: [...document.querySelectorAll('.research-table-wrap')].map(el => ({
        clientWidth: el.clientWidth, scrollWidth: el.scrollWidth
      })),
      brokenImages: [...document.querySelectorAll('main img')].filter(img => !img.complete || img.naturalWidth <= 0).map(img => img.getAttribute('src')),
      canonical: document.querySelector('link[rel=canonical]')?.href,
      lang: document.documentElement.lang
    })""")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    for label,url,lang in SITES:
        for width in [360,390,412,1440]:
            page = browser.new_page(viewport={"width":width,"height":950}, device_scale_factor=1)
            rec = {"page":label,"url":url,"viewport":width}
            try:
                response = page.goto(url,wait_until="domcontentloaded",timeout=35000)
                page.wait_for_timeout(650)
                try: page.wait_for_load_state("load",timeout=14000)
                except Exception: pass
                rec["http"] = response.status if response else None
                rec.update(evaluate_site(page))
                rec["overflow"] = rec["documentWidth"] > rec["pageWidth"]+2
                rec["tableOverflow"] = any(x["scrollWidth"]>x["clientWidth"]+2 for x in rec["tableWrappers"])
                checks=[rec["http"]==200,rec["h1"]==1,rec["rows"]==15,rec["faq"]==9,rec["lang"]==lang,not rec["overflow"],not rec["tableOverflow"],not rec["brokenImages"]]
                rec["pass"] = all(checks)
                if width == 390:
                    rec["topScreenshotBytes"] = screenshot_jpg(page,label+"-top-390")
                    try:
                        el=page.locator(".research-table--ranking")
                        el.scroll_into_view_if_needed(timeout=8000)
                        rec["tableScreenshotBytes"] = screenshot_jpg(page,label+"-table-390")
                    except Exception as ex:result["notes"].append("Table shot "+label+": "+str(ex)[:120])
                if not rec["pass"]:result["errors"].append("Site check failed: "+label+" width "+str(width))
            except Exception as ex:
                rec["pass"]=False;rec["error"]=str(ex)[:600]
                result["errors"].append("Site navigation: "+label+" width "+str(width)+": "+str(ex)[:160])
            result["sites"].append(rec)
            page.close()
    for label,url in REPOS:
        page=browser.new_page(viewport={"width":390,"height":950},device_scale_factor=1)
        rec={"page":label,"url":url}
        try:
            response=page.goto(url,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(1100)
            rec["http"] = response.status if response else None
            markdown=page.locator("#readme .markdown-body")
            if markdown.count() == 0:markdown=page.locator(".markdown-body")
            rec["markdownFound"] = markdown.count()>0
            if rec["markdownFound"]:
                imgs=markdown.locator("img")
                rec["imgCount"]=imgs.count()
                for i in range(imgs.count()):
                    try:imgs.nth(i).scroll_into_view_if_needed(timeout=8000)
                    except Exception:pass
                page.wait_for_timeout(1000)
                rec["brokenImages"]=markdown.evaluate("""el => [...el.querySelectorAll('img')].filter(i => !i.complete || i.naturalWidth===0).map(i=>i.getAttribute('src'))""")
                rec["sections"]=markdown.locator("h3").count()
            else:
                rec["imgCount"]=0;rec["brokenImages"]=[];rec["sections"]=0
            rec["pass"]=rec["http"]==200 and rec["markdownFound"] and rec["imgCount"]>=4 and not rec["brokenImages"]
            rec["topScreenshotBytes"] = screenshot_jpg(page,label+"-top-390") if label=="ru-gh" else 0
            if not rec["pass"]:result["errors"].append("GitHub README render: "+label+" status="+str(rec["http"])+", imgs="+str(rec["imgCount"]))
        except Exception as ex:
            rec["pass"]=False;rec["error"]=str(ex)[:600];result["errors"].append("GitHub navigation: "+label+": "+str(ex)[:160])
        result["readmes"].append(rec);page.close()
    browser.close()
result["passed"]=not result["errors"]
(OUT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"passed":result["passed"],"siteTests":len(result["sites"]),"readmeTests":len(result["readmes"]),"errors":result["errors"][:12]},ensure_ascii=False))
if not result["passed"]:
    raise SystemExit(1)

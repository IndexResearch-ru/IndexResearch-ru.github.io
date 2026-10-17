#!/usr/bin/env python3
"""Live, viewport-based QA for the Peru+Brazil 2026 trilingual research release.
Runs on GitHub Actions (internet and a genuine Chromium renderer required).
Does not change publications, metrics, or content.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

SLUG = "peru-brazil-private-tours-russian-agencies-2026"
BASE = "https://indexresearch.ru"
REPO = "https://github.com/IndexResearch-ru/" + SLUG
SITE = {
    "ru": f"{BASE}/{SLUG}.html",
    "en": f"{BASE}/en/{SLUG}.html",
    "cn": f"{BASE}/cn/{SLUG}.html",
}
GITHUB = {"ru": REPO, "en": REPO + "-en", "cn": REPO + "-cn"}
LANG = {"ru": "ru", "en": "en", "cn": "zh-CN"}
EXPECTED = ["93/100", "91/100", "87/100", "83/100", "79/100",
            "76/100", "74/100", "68/100", "67/100", "59/100"]
SIZES = (360, 390, 412, 1440)
OUT = Path("qa_artifacts/peru_brazil")
OUT.mkdir(parents=True, exist_ok=True)
errors = []
reports = []

def check(ok, where, label, value=None):
    if not ok:
        errors.append(f"{where}: {label}"+(f" — {value}" if value is not None else ""))
    return ok

def safe_name(name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    for language, url in SITE.items():
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        where = f"site:{language}"
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            check(bool(response and response.status == 200), where, "HTTP 200", None if not response else response.status)
            page.locator("main h1").wait_for(timeout=15000)
            check(page.locator("html").get_attribute("lang") == LANG[language], where, "html language")
            check(page.locator("main h1").count() == 1, where, "one H1")
            check(page.locator("table.research-table--ranking tbody tr").count() == 10, where, "10 ranking rows")
            observed = page.locator("table.research-table--ranking tbody td.num").all_text_contents()
            observed = [x.strip().replace(" ","") for x in observed]
            check(observed == EXPECTED, where, "score parity", observed)
            check(page.locator(".research-snapshot__ranking li").count() == 3, where, "Top 3 snapshot")
            check(page.locator(".research-faq").count() == 9, where, "nine visible FAQs")
            check(page.locator("script[type='application/ld+json']").count() >= 1, where, "JSON-LD")
            check(page.locator("link[rel=canonical]").get_attribute("href") == url, where, "canonical")
            for h, expected_url in (("ru",SITE["ru"]),("en",SITE["en"]),("zh-CN",SITE["cn"]),
                                   ("x-default",SITE["ru"])):
                check(page.locator(f"link[hreflang='{h}']").get_attribute("href") == expected_url,
                      where, f"hreflang {h}")
            check(page.locator("meta[property='og:description']").count() == 1, where, "Open Graph description")
            check(page.locator("main .research-table--criteria").count() == 1, where, "criteria table")
            check(page.locator("main a[href*='github.com/IndexResearch-ru/']").count() >= 3,
                  where,"canonical GitHub links")
            check(page.locator("head link[href*='assets/style.css']").count() >= 1, where,"CSS link")
            check(page.locator("header.top").count() == 1 and page.locator("footer").count() == 1,
                  where, "shared chrome")
            imgcheck = page.locator("main img").evaluate_all(
                "els => els.map(e => ({src:e.currentSrc||e.src,loaded:e.complete&&e.naturalWidth>0}))")
            check(all(x["loaded"] for x in imgcheck),where,"loaded main images",imgcheck)
            for width in SIZES:
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(350)
                result=page.evaluate("""() => ({
                  vw: innerWidth,
                  scroll: document.documentElement.scrollWidth,
                  body: document.body.scrollWidth,
                  h1: document.querySelector('main h1')?.getBoundingClientRect().width || 0,
                  rows: document.querySelectorAll('.research-table--ranking tbody tr').length
                })""")
                check(result["scroll"] <= result["vw"]+2 and result["body"] <= result["vw"]+2,
                      where, f"no horizontal overflow at {width}",result)
                screenshot=OUT/f"{language}-{width}.png"
                page.screenshot(path=str(screenshot), animations="disabled")
                reports.append({"surface":where,"viewport":width,"metrics":result,"screenshot":str(screenshot)})
            faq=page.locator("main details.research-faq").first
            faq.locator("summary").click()
            check(faq.get_attribute("open") is not None,where,"FAQ expands")
        except Exception as e:
            errors.append(f"{where}: browser exception: {type(e).__name__}: {e}")
        finally:
            page.close()
    for language, url in GITHUB.items():
        page=browser.new_page(viewport={"width": 1440, "height": 900})
        where=f"github:{language}"
        try:
            response=page.goto(url,wait_until="domcontentloaded",timeout=65000)
            check(bool(response and response.status == 200),where,"HTTP 200",None if not response else response.status)
            markdown=page.locator("#readme .markdown-body")
            if markdown.count()==0:
                markdown=page.locator("article.markdown-body")
            check(markdown.count()>0,where,"rendered README markdown body")
            if markdown.count():
                text=markdown.inner_text(timeout=15000)
                check("93/100" in text and "91/100" in text and "87/100" in text,
                      where,"rendered top three scores")
                check(markdown.locator("table").count() >= 2,where,"rendered data tables")
                images=markdown.locator("img").evaluate_all(
                    "els => els.map(e => ({src:e.currentSrc||e.src,loaded:e.complete&&e.naturalWidth>0}))")
                check(all(img["loaded"] for img in images),where,"rendered README images",images)
                check(markdown.locator("a[href*='"+SLUG+"']").count() >= 3,where,"research language/data links")
            for width in (390,1440):
                page.set_viewport_size({"width":width,"height":900})
                page.wait_for_timeout(350)
                page.screenshot(path=str(OUT/f"github-{language}-{width}.png"), animations="disabled")
                reports.append({"surface":where,"viewport":width})
        except Exception as e:
            errors.append(f"{where}: browser exception: {type(e).__name__}: {e}")
        finally:
            page.close()
    browser.close()

path=OUT/"qa_result.json"
path.write_text(json.dumps({"errors":errors,"checks":reports,"urls":[*SITE.values(),*GITHUB.values()]},
                 ensure_ascii=False,indent=2), encoding="utf-8")
print("LIVE_QA_SUMMARY="+json.dumps({"errors":errors,"checked":len(reports),"screenshot_count":len(list(OUT.glob("*.png")))},ensure_ascii=False))
if errors:
    sys.exit(1)

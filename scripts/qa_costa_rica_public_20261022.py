#!/usr/bin/env python3
"""One-off public browser QA for INDEX-T045. No site changes or private sources."""
import json
import re
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

SLUG = "costa-rica-private-tours-2026"
ROOT = "https://indexresearch.ru"
GITHUB = "https://github.com/IndexResearch-ru"
SITE = {
    "ru": ROOT + "/" + SLUG + ".html",
    "en": ROOT + "/en/" + SLUG + ".html",
    "cn": ROOT + "/cn/" + SLUG + ".html",
}
REPOS = {
    "ru": GITHUB + "/" + SLUG,
    "en": GITHUB + "/" + SLUG + "-en",
    "cn": GITHUB + "/" + SLUG + "-cn",
}
LANG = {"ru": "ru", "en": "en", "cn": "zh-CN"}
SIZES = [360, 390, 412, 1440]
OUT = Path("qa_artifacts/costa_rica")
OUT.mkdir(parents=True, exist_ok=True)
ERRORS = []
PAGES = []
REPO_REPORT = []
URLS = set()
LINK_CHECKS = []

def record(ok, name, detail=""):
    if not ok:
        msg = name + (": " + str(detail)[:300] if detail else "")
        ERRORS.append(msg)
        print("LIVE_QA_ERROR " + msg, flush=True)

def goto(page, url):
    response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(550)
    return response.status if response else None

def audit_jsonld(page, lang):
    try:
        s = page.locator('script[type="application/ld+json"]').first.inner_text()
        obj = json.loads(s)
        d = {e.get("@type"): e for e in obj.get("@graph", []) if isinstance(e, dict)}
        required = {"Dataset", "Article", "ItemList", "FAQPage", "BreadcrumbList"}
        record(required.issubset(d), lang + " schema types", sorted(d))
        ds = d.get("Dataset", {})
        art = d.get("Article", {})
        li = d.get("ItemList", {})
        faq = d.get("FAQPage", {})
        record(ds.get("sameAs") == REPOS["ru"], lang + " canonical Dataset.sameAs")
        record(art.get("sameAs") == REPOS[lang], lang + " language Article.sameAs")
        if lang != "ru":
            based = art.get("isBasedOn")
            based = based.get("@id") if isinstance(based, dict) else based
            record(based == REPOS["ru"], lang + " Article.isBasedOn")
        record(ds.get("version") == "1.0.0", lang + " version")
        record(ds.get("temporalCoverage") == "2026-10-21", lang + " cutoff")
        record(li.get("itemListOrder") == "https://schema.org/ItemListUnordered", lang + " unordered schema")
        record(len(li.get("itemListElement") or []) == 20, lang + " ItemList size")
        record(len(faq.get("mainEntity") or []) == 9, lang + " FAQPage size")
    except Exception as exc:
        record(False, lang + " JSON-LD parsing", repr(exc))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    for lang, url in SITE.items():
        for width in SIZES:
            page = browser.new_page(viewport={"width": width, "height": 920}, device_scale_factor=1)
            row = {"surface": "site", "lang": lang, "width": width, "url": url}
            try:
                row["http"] = goto(page, url)
                page.locator("main h1").wait_for(timeout=15000)
                row.update(page.evaluate("""() => ({
                    htmlLang: document.documentElement.lang,
                    pageWidth: document.documentElement.clientWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    h1: document.querySelectorAll('main h1').length,
                    rows: document.querySelectorAll('main .research-table--ranking tbody tr').length,
                    faq: document.querySelectorAll('main details summary').length,
                    hasHeader: !!document.querySelector('header.top'),
                    hasFooter: !!document.querySelector('footer'),
                    brokenImages: [...document.querySelectorAll('main img')].filter(x => !x.complete || x.naturalWidth < 1).map(x => x.src),
                    tableWrapOverflow: [...document.querySelectorAll('.research-table-wrap')].map(x => [x.clientWidth, x.scrollWidth])
                })"""))
                row["pass"] = (
                    row["http"] == 200 and row["htmlLang"] == LANG[lang] and row["h1"] == 1
                    and row["rows"] == 20 and row["faq"] == 9 and row["hasHeader"] and row["hasFooter"]
                    and row["scrollWidth"] <= row["pageWidth"] + 2
                    and len(row["brokenImages"]) == 0
                    and not any(sw > cw + 2 for cw, sw in row["tableWrapOverflow"])
                )
                record(row["pass"], lang + " viewport " + str(width), row)
                if width == 390:
                    for name, css in [("top", "main h1"), ("table", "main .research-table--ranking")]:
                        try:
                            page.locator(css).first.scroll_into_view_if_needed(timeout=7000)
                            page.screenshot(path=str(OUT / (lang + "-" + name + "-390.png")), animations="disabled")
                        except Exception as exc:
                            record(False, lang + " screenshot " + name, repr(exc))
                if width == 1440:
                    canonical = page.locator('link[rel="canonical"]').first.get_attribute("href")
                    record(canonical == url, lang + " canonical", canonical)
                    for code, target in [
                        ("ru", SITE["ru"]), ("en", SITE["en"]),
                        ("zh-CN", SITE["cn"]), ("x-default", SITE["ru"])
                    ]:
                        matches = page.locator('link[hreflang="' + code + '"]')
                        actual = matches.first.get_attribute("href") if matches.count() else None
                        record(actual == target, lang + " hreflang " + code, actual)
                    record(page.locator('meta[property="og:url"]').count() == 1, lang + " Open Graph URL")
                    record(page.locator('meta[name="robots"]').first.get_attribute("content").startswith("index,follow"), lang + " robots")
                    record(page.locator('script[src*="analytics.js"]').count() >= 1, lang + " analytics")
                    record("Ada Tours" in page.locator("main").inner_text(), lang + " commercial disclosure")
                    audit_jsonld(page, lang)
                    URLS.update(page.locator("main a[href]").evaluate_all("""els => els.map(e => e.href)"""))
            except Exception as exc:
                row["pass"] = False
                row["exception"] = repr(exc)[:400]
                record(False, lang + " browser", repr(exc))
            finally:
                PAGES.append(row)
                page.close()
    for lang, url in REPOS.items():
        page = browser.new_page(viewport={"width": 390, "height": 920}, device_scale_factor=1)
        row = {"surface": "GitHub", "lang": lang, "url": url}
        try:
            row["http"] = goto(page, url)
            readme = page.locator("#readme .markdown-body")
            if not readme.count():
                readme = page.locator(".markdown-body").first
            row["readme"] = readme.count() > 0
            if row["readme"]:
                images = readme.locator("img")
                row["images"] = images.count()
                for j in range(images.count()):
                    try: images.nth(j).scroll_into_view_if_needed(timeout=7000)
                    except Exception: pass
                page.wait_for_timeout(750)
                row["brokenImages"] = readme.evaluate("""e => [...e.querySelectorAll('img')].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)""")
                row["companySections"] = readme.locator("h3").count()
            else:
                row["images"] = 0
                row["brokenImages"] = []
                row["companySections"] = 0
            row["pass"] = row["http"] == 200 and row["readme"] and row["images"] >= 3 and not row["brokenImages"]
            record(row["pass"], lang + " Github README", row)
            if lang == "ru":
                page.screenshot(path=str(OUT / "github-ru-top-390.png"), animations="disabled")
            if row["readme"]:
                URLS.update(readme.locator("a[href]").evaluate_all("""els => els.map(e => e.href)"""))
        except Exception as exc:
            row["pass"] = False
            row["exception"] = repr(exc)[:400]
            record(False, lang + " GitHub browser", repr(exc))
        finally:
            REPO_REPORT.append(row)
            page.close()
    browser.close()

def check_url(url):
    if not url.startswith(("https://indexresearch.ru/", "https://github.com/IndexResearch-ru/")):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IndexResearch-live-check/1.0"})
        with urllib.request.urlopen(req, timeout=16) as resp:
            return {"url": url, "status": resp.status, "final": resp.url}
    except Exception as exc:
        return {"url": url, "status": None, "error": str(exc)[:200]}

firstparty = sorted({u.split("#")[0] for u in URLS if u.startswith(("https://indexresearch.ru/", "https://github.com/IndexResearch-ru/"))})
with ThreadPoolExecutor(max_workers=7) as executor:
    for r in executor.map(check_url, firstparty):
        if r:
            LINK_CHECKS.append(r)
            if r["status"] != 200:
                record(False, "First-party link destination", r)

result = {
    "site_views": PAGES, "github_readmes": REPO_REPORT,
    "link_check": LINK_CHECKS, "errors": ERRORS,
    "checked": {"site_viewports": len(PAGES), "readmes": len(REPO_REPORT), "firstparty_urls": len(LINK_CHECKS)}
}
(OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("COSTA_RICA_LIVE_QA=" + json.dumps({"passed": not ERRORS, "counts": result["checked"], "errors": ERRORS[:12]}, ensure_ascii=False), flush=True)
if ERRORS:
    raise SystemExit(1)

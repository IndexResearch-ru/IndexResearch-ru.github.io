#!/usr/bin/env python3
"""One-off browser QA for INDEX-T053: RU/EN/CN site and GitHub surfaces."""
import json
import os
import pathlib
import shutil
import sys
from playwright.sync_api import sync_playwright

SLUG = "urgent-automated-packaging-fulfillment-moscow-2026"
ROOT = "https://indexresearch.ru/"
GITHUB = "https://github.com/IndexResearch-ru/"
SCREENSHOTS = pathlib.Path("qa-screenshots-index-t053")
SCREENSHOTS.mkdir(exist_ok=True)
CHECKS = []
ERRORS = []

def inspect(page, lang, kind, viewport):
    width, height = viewport
    page.set_viewport_size({"width": width, "height": height})
    url = (ROOT + ("" if lang == "ru" else lang + "/") + SLUG + ".html") if kind == "site" else (
        GITHUB + SLUG + ("" if lang == "ru" else "-" + lang))
    result = {"lang": lang, "kind": kind, "width": width, "height": height, "url": url}
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        result["http_status"] = response.status if response else None
        page.wait_for_timeout(1700)
        result["title"] = page.title()
        result["h1_count"] = page.locator("h1").count()
        result["viewport_width"] = page.evaluate("window.innerWidth")
        result["scroll_width"] = page.evaluate("document.documentElement.scrollWidth")
        result["horizontal_overflow_px"] = max(0, result["scroll_width"] - result["viewport_width"])
        result["broken_images"] = page.evaluate("""() => [...document.querySelectorAll('img')]
          .filter(x => x.complete && x.naturalWidth === 0)
          .map(x => x.currentSrc || x.src).slice(0, 20)""")
        if kind == "site" and result["http_status"] == 200:
            result["profiles"] = page.locator("main article").count()
            result["faq"] = page.locator("main details").count()
            result["canonical"] = page.locator('link[rel="canonical"]').first.get_attribute("href")
            result["language"] = page.locator("html").first.get_attribute("lang")
            result["hreflang"] = {
                key: page.locator('link[rel="alternate"][hreflang="' + key + '"]').count()
                for key in ["ru", "en", "zh-CN", "x-default"]
            }
            result["analytics_scripts"] = page.locator('script[src="/assets/analytics.js"]').count()
            result["shared_chrome"] = page.locator("header.top").count() == 1 and page.locator("footer").count() == 1
            expected = ROOT + ("" if lang == "ru" else lang + "/") + SLUG + ".html"
            if (result["profiles"], result["faq"], result["canonical"], result["language"]) != (
                21, 8, expected, {"ru":"ru","en":"en","cn":"zh-CN"}[lang]
            ):
                ERRORS.append("SITE_CONTENT_" + lang + "_" + str(width) + ":" + str(result))
            if result["horizontal_overflow_px"] > 2:
                ERRORS.append("SITE_OVERFLOW_" + lang + "_" + str(width) + ":" + str(result["horizontal_overflow_px"]))
            if not result["shared_chrome"] or not all(v == 1 for v in result["hreflang"].values()):
                ERRORS.append("SITE_CHROME_OR_HREFLANG_" + lang + "_" + str(width))
        elif kind == "site":
            ERRORS.append("SITE_HTTP_" + lang + "_" + str(result["http_status"]))
        elif kind == "github" and result["http_status"] == 200:
            selectors = ["#readme", "article.markdown-body", ".markdown-body", '[data-testid="readme"]']
            selected = next((s for s in selectors if page.locator(s).count() > 0), None)
            if not selected:
                page.screenshot(path=str(SCREENSHOTS / (lang + "-github-root-" + str(width) + ".png")),
                                full_page=False, timeout=15000)
                response = page.goto(url + "/blob/main/README.md", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(1300)
                result["fallback_status"] = response.status if response else None
                selected = next((s for s in selectors if page.locator(s).count() > 0), None)
            result["readme_selector"] = selected
            result["readme_exists"] = bool(selected)
            if selected:
                loc = page.locator(selected).first
                result["readme_tables"] = loc.locator("table").count()
                result["readme_images"] = loc.locator("img").count()
                result["readme_h3"] = loc.locator("h3").count()
                result["readme_source"] = loc.inner_text(timeout=5000)[:300]
            else:
                result["readme_tables"] = 0
                result["readme_images"] = 0
                result["readme_source"] = page.locator("body").inner_text(timeout=5000)[-700:]
            if not result["readme_exists"] or result["readme_tables"] < 2 or result["readme_images"] < 4:
                ERRORS.append("GITHUB_README_" + lang + "_" + str(width) + ":" + str(result))
        else:
            result["warning"] = "GitHub rendered page did not return HTTP 200 (may be rate-limited)"
        if result["http_status"] == 200:
            page.screenshot(path=str(SCREENSHOTS / (lang + "-" + kind + "-" + str(width) + ".png")), full_page=True, animations="disabled", timeout=30000)
    except Exception as exc:
        result["error"] = str(exc)[:900]
        ERRORS.append("BROWSER_ERROR_" + lang + "_" + kind + "_" + str(width) + ":" + result["error"])
    CHECKS.append(result)
    print("QA_RESULT " + json.dumps(result, ensure_ascii=False), flush=True)

with sync_playwright() as p:
    chrome_path = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    opts = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if chrome_path:
        opts["executable_path"] = chrome_path
    browser = p.chromium.launch(**opts)
    page = browser.new_page(ignore_https_errors=False)
    for lang in ["ru", "en", "cn"]:
        for width in [1440, 360, 390, 412]:
            inspect(page, lang, "site", (width, 900))
    for lang in ["ru", "en", "cn"]:
        for width in [1440, 390]:
            inspect(page, lang, "github", (width, 900))
    browser.close()

report = {"study": "INDEX-T053", "checks": CHECKS, "errors": ERRORS}
(SCREENSHOTS / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("QA_TOTAL " + json.dumps({"site_checks": 12, "github_checks": 6, "errors": ERRORS}, ensure_ascii=False), flush=True)
sys.exit(1 if ERRORS else 0)

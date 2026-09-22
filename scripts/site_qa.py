#!/usr/bin/env python3
from pathlib import Path
import hashlib
import html as html_module
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

from ensure_site_chrome import render_chrome
from research_topics import load_topic_config, topic_configuration_errors

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://indexresearch.ru"
errors = []

feed_check = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "reorder_home_research.py"), "--check"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
if feed_check.returncode != 0:
    errors.append(
        feed_check.stdout.strip()
        or feed_check.stderr.strip()
        or "Homepage research feed check failed."
    )

html_paths = sorted(
    path for path in ROOT.rglob("*.html")
    if not any(part in {"templates", ".git", ".github"} for part in path.relative_to(ROOT).parts)
)
if not html_paths:
    errors.append("No public HTML pages found.")

sitemap_path = ROOT / "sitemap.xml"
sitemap_urls = set()
if sitemap_path.exists():
    try:
        tree = ET.parse(sitemap_path)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = {n.text.strip() for n in tree.findall(".//s:loc", ns) if n.text}
    except Exception as exc:
        errors.append(f"sitemap.xml is invalid XML: {exc}")
else:
    errors.append("sitemap.xml is missing.")

ratings = (ROOT / "ratings.html").read_text(encoding="utf-8") if (ROOT / "ratings.html").exists() else ""
en_ratings = (ROOT / "en" / "ratings.html").read_text(encoding="utf-8") if (ROOT / "en" / "ratings.html").exists() else ""
cn_ratings = (ROOT / "cn" / "ratings.html").read_text(encoding="utf-8") if (ROOT / "cn" / "ratings.html").exists() else ""
en_home = (ROOT / "en" / "index.html").read_text(encoding="utf-8") if (ROOT / "en" / "index.html").exists() else ""
cn_home = (ROOT / "cn" / "index.html").read_text(encoding="utf-8") if (ROOT / "cn" / "index.html").exists() else ""
non_research = {"index.html", "ratings.html", "methodology.html", "404.html"}

# THEMATIC HUB QA
topic_by_research_id = {}
try:
    topic_config = load_topic_config()
    for topic_error in topic_configuration_errors():
        errors.append("research-topics.json: " + topic_error)
    for topic in topic_config.get("topics", []):
        hub_path = ROOT / "topics" / f"{topic['slug']}.html"
        if not hub_path.exists():
            errors.append(f"Missing thematic hub: {hub_path.relative_to(ROOT).as_posix()}.")
            continue
        hub_text = hub_path.read_text(encoding="utf-8")
        hub_ids = re.findall(
            r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\']',
            hub_text,
            re.I,
        )
        expected_ids = topic.get("research_ids") or []
        for research_id in expected_ids:
            topic_by_research_id[research_id] = topic
        if hub_ids != expected_ids:
            errors.append(
                f"{hub_path.relative_to(ROOT).as_posix()}: research cards must match topic config order "
                f"({len(expected_ids)} expected, {len(hub_ids)} found)."
            )
        if 'class="breadcrumbs"' not in hub_text:
            errors.append(f"{hub_path.relative_to(ROOT).as_posix()}: visible breadcrumbs are required.")

        jsonld_match = re.search(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
            hub_text,
            re.I,
        )
        if not jsonld_match:
            errors.append(f"{hub_path.relative_to(ROOT).as_posix()}: missing JSON-LD.")
        else:
            try:
                parsed = json.loads(jsonld_match.group(1))
                graph = parsed.get("@graph", []) if isinstance(parsed, dict) else []
                collection = next(
                    (
                        node for node in graph
                        if isinstance(node, dict) and node.get("@type") == "CollectionPage"
                    ),
                    None,
                )
                if not collection:
                    errors.append(
                        f"{hub_path.relative_to(ROOT).as_posix()}: missing CollectionPage in JSON-LD."
                    )
                else:
                    has_part = [
                        item for item in (collection.get("hasPart") or [])
                        if isinstance(item, dict)
                    ]
                    expected_part_ids = [
                        f"{BASE}/{research_id}.html#article"
                        for research_id in expected_ids
                    ]
                    actual_part_ids = [item.get("@id") for item in has_part]
                    if actual_part_ids != expected_part_ids:
                        errors.append(
                            f"{hub_path.relative_to(ROOT).as_posix()}: CollectionPage.hasPart must match "
                            f"topic research order/count ({len(expected_part_ids)} expected, {len(actual_part_ids)} found)."
                        )
            except Exception as exc:
                errors.append(
                    f"{hub_path.relative_to(ROOT).as_posix()}: invalid thematic JSON-LD: {exc}"
                )
except Exception as exc:
    errors.append(f"Thematic research configuration failed: {exc}")


LANGUAGES = {
    "ru": {"dir": None, "html_lang": "ru", "hreflang": "ru", "og_locale": "ru_RU"},
    "en": {"dir": "en", "html_lang": "en", "hreflang": "en", "og_locale": "en_US"},
    "cn": {"dir": "cn", "html_lang": "zh-CN", "hreflang": "zh-CN", "og_locale": "zh_CN"},
}
LOCALIZED_RATINGS = {"ru": ratings, "en": en_ratings, "cn": cn_ratings}

# Shared site chrome: RU, EN and CN header/footer each have one canonical source.
chrome_partial_paths = [
    ROOT / "templates" / "partials" / "site-header.html",
    ROOT / "templates" / "partials" / "site-footer.html",
    ROOT / "templates" / "partials" / "site-header-en.html",
    ROOT / "templates" / "partials" / "site-footer-en.html",
    ROOT / "templates" / "partials" / "site-header-cn.html",
    ROOT / "templates" / "partials" / "site-footer-cn.html",
]
for partial_path in chrome_partial_paths:
    if not partial_path.exists():
        errors.append(f"{partial_path.relative_to(ROOT).as_posix()} is missing.")

style_file_for_hash = ROOT / "assets" / "style.css"
expected_style_version = (
    hashlib.sha256(style_file_for_hash.read_bytes()).hexdigest()[:12]
    if style_file_for_hash.exists()
    else None
)

def visible_text(fragment):
    fragment = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html_module.unescape(fragment)).strip()

def jsonld_graph(page_text, page_name):
    objects = []
    for raw in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        page_text,
        re.I,
    ):
        try:
            parsed = json.loads(raw)
        except Exception as exc:
            errors.append(f"{page_name}: invalid JSON-LD: {exc}")
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("@graph"), list):
            objects.extend(parsed["@graph"])
        elif isinstance(parsed, list):
            objects.extend(parsed)
        else:
            objects.append(parsed)
    return objects


def schema_objects_by_type(page_text, page_name):
    by_type = {}
    for obj in jsonld_graph(page_text, page_name):
        if not isinstance(obj, dict):
            continue
        obj_type = obj.get("@type")
        types = obj_type if isinstance(obj_type, list) else [obj_type]
        for item_type in types:
            if item_type:
                by_type.setdefault(item_type, []).append(obj)
    return by_type



def language_key_for_rel(rel: str) -> str:
    if rel.startswith("en/"):
        return "en"
    if rel.startswith("cn/"):
        return "cn"
    return "ru"


def localized_file(page_name: str, lang_key: str) -> Path:
    directory = LANGUAGES[lang_key]["dir"]
    return ROOT / page_name if directory is None else ROOT / directory / page_name


def public_url_for_file(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{BASE}/"
    if rel.endswith("/index.html"):
        return f"{BASE}/" + rel[:-10]
    return f"{BASE}/{rel}"


def localized_href(page_name: str, lang_key: str) -> str:
    directory = LANGUAGES[lang_key]["dir"]
    if page_name == "index.html":
        return "/" if directory is None else f"/{directory}/"
    return f"/{page_name}" if directory is None else f"/{directory}/{page_name}"


def has_hreflang(page_text: str, code: str, href: str) -> bool:
    return bool(re.search(
        rf'<link\b(?=[^>]*\brel=["\']alternate["\'])(?=[^>]*\bhreflang=["\']{re.escape(code)}["\'])(?=[^>]*\bhref=["\']{re.escape(href)}["\'])[^>]*>',
        page_text,
        re.I,
    ))


def internal_href_target(href: str, source_url: str):
    if href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(urljoin(source_url, href))
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() not in {"indexresearch.ru", "www.indexresearch.ru"}:
        return None
    clean = parsed.path or "/"
    if clean in {"/", "/en/", "/cn/"}:
        if clean == "/en/":
            return "en", "index.html"
        if clean == "/cn/":
            return "cn", "index.html"
        return "ru", "index.html"
    if clean.startswith("/en/"):
        return "en", clean.removeprefix("/en/")
    if clean.startswith("/cn/"):
        return "cn", clean.removeprefix("/cn/")
    if clean.startswith("/"):
        return "ru", clean.removeprefix("/")
    return None


def itemlist_signature(item_list: dict) -> dict:
    elements = [item for item in (item_list.get("itemListElement") or []) if isinstance(item, dict)]
    scores = []
    for element in elements:
        payload = element.get("item") if isinstance(element.get("item"), dict) else {}
        match = re.search(r'([0-9]+(?:[.,][0-9]+)?)/100', json.dumps(payload, ensure_ascii=False))
        scores.append(match.group(1).replace(",", ".") if match else None)
    return {
        "numberOfItems": item_list.get("numberOfItems"),
        "itemListOrder": item_list.get("itemListOrder"),
        "positions": [item.get("position") for item in elements],
        "scores": scores,
    }


def catalog_card_ids(page_text):
    if page_text.count("<!-- RESEARCH_CATALOG_START -->") != 1 or page_text.count("<!-- RESEARCH_CATALOG_END -->") != 1:
        errors.append("ratings.html: must contain exactly one research catalog marker pair.")
        return []
    block = page_text.split("<!-- RESEARCH_CATALOG_START -->", 1)[1].split("<!-- RESEARCH_CATALOG_END -->", 1)[0]
    ids = re.findall(
        r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\']',
        block,
        re.I,
    )
    if len(ids) != len(set(ids)):
        errors.append("ratings.html: duplicate data-research-id in catalog.")
    return ids


catalog_ids = catalog_card_ids(ratings)

cn_catalog_ids = []
if cn_ratings:
    if cn_ratings.count("<!-- RESEARCH_CATALOG_CN_START -->") != 1 or cn_ratings.count("<!-- RESEARCH_CATALOG_CN_END -->") != 1:
        errors.append("cn/ratings.html: must contain exactly one Chinese research catalog marker pair.")
    else:
        cn_block = cn_ratings.split("<!-- RESEARCH_CATALOG_CN_START -->", 1)[1].split("<!-- RESEARCH_CATALOG_CN_END -->", 1)[0]
        cn_catalog_ids = re.findall(
            r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\']',
            cn_block,
            re.I,
        )
        if cn_catalog_ids != catalog_ids:
            errors.append(
                f"cn/ratings.html: catalog must match canonical RU catalog order/count ({len(catalog_ids)}); found {len(cn_catalog_ids)}."
            )

def home_feed_ids(page_text, label):
    if not page_text:
        return []
    if page_text.count("<!-- RESEARCH_FEED_START -->") != 1 or page_text.count("<!-- RESEARCH_FEED_END -->") != 1:
        errors.append(f"{label}: must contain exactly one research feed marker pair.")
        return []
    block = page_text.split("<!-- RESEARCH_FEED_START -->", 1)[1].split("<!-- RESEARCH_FEED_END -->", 1)[0]
    ids = re.findall(
        r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\']',
        block,
        re.I,
    )
    if len(ids) != len(set(ids)):
        errors.append(f"{label}: duplicate data-research-id in research feed.")
    return ids

for label, page_text in (("en/index.html", en_home), ("cn/index.html", cn_home)):
    if page_text:
        ids = home_feed_ids(page_text, label)
        if ids != catalog_ids:
            errors.append(
                f"{label}: research feed must match canonical RU catalog order/count ({len(catalog_ids)}); found {len(ids)}."
            )
for label, page_text in (("en/ratings.html", en_ratings), ("cn/ratings.html", cn_ratings)):
    if page_text:
        ids = re.findall(
            r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\']',
            page_text,
            re.I,
        )
        if ids != catalog_ids:
            errors.append(
                f"{label}: localized catalog must match canonical RU catalog order/count "
                f"({len(catalog_ids)}); found {len(ids)}."
            )

research_page_ids = sorted(
    path.stem for path in html_paths
    if path.parent == ROOT and path.name not in non_research
)
if sorted(catalog_ids) != research_page_ids:
    missing_cards = sorted(set(research_page_ids) - set(catalog_ids))
    missing_pages = sorted(set(catalog_ids) - set(research_page_ids))
    if missing_cards:
        errors.append("ratings.html: research pages missing from visible catalog: " + ", ".join(missing_cards))
    if missing_pages:
        errors.append("ratings.html: catalog cards without matching research pages: " + ", ".join(missing_pages))

catalog_dates = re.findall(
    r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-published=["\'](\d{4}-\d{2}-\d{2})["\']',
    ratings,
    re.I,
)
latest_catalog_date = max(catalog_dates) if catalog_dates else None

ratings_types = schema_objects_by_type(ratings, "ratings.html")
ratings_collections = ratings_types.get("CollectionPage", [])
ratings_catalogs = ratings_types.get("DataCatalog", [])
if len(ratings_collections) != 1:
    errors.append(f"ratings.html: expected exactly 1 CollectionPage, found {len(ratings_collections)}.")
if len(ratings_catalogs) != 1:
    errors.append(f"ratings.html: expected exactly 1 DataCatalog, found {len(ratings_catalogs)}.")

required_dataset_fields = [
    "@id", "name", "description", "url", "sameAs", "creator",
    "datePublished", "version", "inLanguage", "includedInDataCatalog",
]

if ratings_collections:
    collection = ratings_collections[0]
    has_part = [item for item in (collection.get("hasPart") or []) if isinstance(item, dict)]
    has_part_ids = [
        str(item.get("url", "")).removeprefix(BASE + "/").removesuffix(".html")
        for item in has_part
        if item.get("url")
    ]
    if has_part_ids != catalog_ids:
        errors.append(
            f"ratings.html: CollectionPage.hasPart must match visible catalog order/count ({len(catalog_ids)}); found {len(has_part_ids)}."
        )
    for item in has_part:
        missing = [field for field in required_dataset_fields if not item.get(field)]
        if missing:
            errors.append(
                f"ratings.html: Dataset summary {item.get('url') or item.get('name') or '[unknown]'} missing: {', '.join(missing)}."
            )
    if latest_catalog_date and collection.get("dateModified") != latest_catalog_date:
        errors.append(
            f"ratings.html: CollectionPage.dateModified is {collection.get('dateModified')!r}, expected {latest_catalog_date!r}."
        )

if ratings_catalogs:
    catalog = ratings_catalogs[0]
    refs = [
        str(item.get("@id", ""))
        for item in (catalog.get("dataset") or [])
        if isinstance(item, dict)
    ]
    expected_refs = [f"{BASE}/{research_id}.html#dataset" for research_id in catalog_ids]
    if refs != expected_refs:
        errors.append(
            f"ratings.html: DataCatalog.dataset must match visible catalog order/count ({len(expected_refs)}); found {len(refs)}."
        )
    if latest_catalog_date and catalog.get("dateModified") != latest_catalog_date:
        errors.append(
            f"ratings.html: DataCatalog.dateModified is {catalog.get('dateModified')!r}, expected {latest_catalog_date!r}."
        )

index_text_for_schema = (ROOT / "index.html").read_text(encoding="utf-8") if (ROOT / "index.html").exists() else ""
index_types = schema_objects_by_type(index_text_for_schema, "index.html")
home_datasets = index_types.get("Dataset", [])
home_dataset_ids = [
    str(item.get("url", "")).removeprefix(BASE + "/").removesuffix(".html")
    for item in home_datasets
    if isinstance(item, dict) and item.get("url")
]
if home_dataset_ids != catalog_ids:
    errors.append(
        f"index.html: Dataset graph must match visible catalog order/count ({len(catalog_ids)}); found {len(home_dataset_ids)}."
    )
for item in home_datasets:
    missing = [field for field in required_dataset_fields if not item.get(field)]
    if missing:
        errors.append(
            f"index.html: Dataset summary {item.get('url') or item.get('name') or '[unknown]'} missing: {', '.join(missing)}."
        )
home_collections = index_types.get("CollectionPage", [])
if len(home_collections) != 1:
    errors.append(f"index.html: expected exactly 1 CollectionPage, found {len(home_collections)}.")
elif latest_catalog_date and home_collections[0].get("dateModified") != latest_catalog_date:
    errors.append(
        f"index.html: CollectionPage.dateModified is {home_collections[0].get('dateModified')!r}, expected {latest_catalog_date!r}."
    )


for path in html_paths:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    name = path.name
    expected_url = (
        f"{BASE}/"
        if rel == "index.html"
        else (f"{BASE}/" + rel[:-10] if rel.endswith("/index.html") else f"{BASE}/{rel}")
    )
    lang_key = language_key_for_rel(rel)
    is_root_research = path.parent == ROOT and name not in non_research
    is_en_research = path.parent == ROOT / "en" and name not in non_research and (ROOT / name).exists()
    is_cn_research = path.parent == ROOT / "cn" and name not in non_research and (ROOT / name).exists()
    is_translated_research = is_en_research or is_cn_research

    is_research = is_root_research or is_translated_research

    html_tag = re.search(r'<html\b[^>]*>', text, re.I)
    if not html_tag or not re.search(r'\btranslate\s*=\s*["\']no["\']', html_tag.group(0), re.I):
        errors.append(f'{rel}: <html> must contain translate="no".')

    google_notranslate = re.findall(
        r'<meta\b(?=[^>]*\bname\s*=\s*["\']google["\'])(?=[^>]*\bcontent\s*=\s*["\']notranslate["\'])[^>]*>',
        text,
        re.I,
    )
    if len(google_notranslate) != 1:
        errors.append(
            f"{rel}: Google notranslate meta must appear exactly once; found {len(google_notranslate)}."
        )

    expected_header, expected_footer = render_chrome(text)
    expected_header_block = f"<!-- SITE_HEADER_START -->\n{expected_header}\n<!-- SITE_HEADER_END -->"
    expected_footer_block = f"<!-- SITE_FOOTER_START -->\n{expected_footer}\n<!-- SITE_FOOTER_END -->"
    if expected_header_block not in text:
        errors.append(f"{rel}: shared header differs from the canonical language-aware partial.")
    if expected_footer_block not in text:
        errors.append(f"{rel}: shared footer differs from the canonical language-aware partial.")
    if text.count("<!-- SITE_HEADER_START -->") != 1 or text.count("<!-- SITE_HEADER_END -->") != 1:
        errors.append(f"{rel}: shared header markers must appear exactly once.")
    if text.count("<!-- SITE_FOOTER_START -->") != 1 or text.count("<!-- SITE_FOOTER_END -->") != 1:
        errors.append(f"{rel}: shared footer markers must appear exactly once.")
    if expected_style_version:
        style_href = re.search(r'href=["\']/?assets/style\.css\?v=([^"\']+)["\']', text, re.I)
        if not style_href:
            errors.append(f"{rel}: stylesheet must use the generated cache-busting version.")
        elif style_href.group(1) != expected_style_version:
            errors.append(
                f"{rel}: stylesheet cache version {style_href.group(1)!r} does not match {expected_style_version!r}."
            )

    if len(re.findall(r'<script src="/assets/analytics\.js" defer></script>', text)) != 1:
        errors.append(f"{rel}: must contain exactly one shared analytics.js include.")
    if "mc.yandex.ru/metrika/tag.js" in text:
        errors.append(f"{rel}: contains legacy inline Yandex Metrika loader.")
    if text.count("mc.yandex.ru/watch/112773213") != 1:
        errors.append(f"{rel}: must contain exactly one Yandex noscript fallback.")

    favicon_checks = [
        'href="/android-chrome-192x192.png"',
        'href="/favicon.ico"',
        'href="/assets/indexresearch-shield.svg"',
        'href="/favicon-32x32.png"',
        'href="/favicon-16x16.png"',
        'href="/apple-touch-icon.png"',
        'content="/mstile-150x150.png"',
    ]
    for needle in favicon_checks:
        if text.count(needle) != 1:
            errors.append(f"{rel}: favicon metadata must contain exactly one {needle}.")

    if not re.search(r"<title>[^<]{3,}</title>", text, re.I):
        errors.append(f"{rel}: missing/non-empty <title>.")
    title_match = re.search(r"<title>([^<]+)</title>", text, re.I)
    title_text = visible_text(title_match.group(1)) if title_match else ""
    if lang_key == "en" and (
        re.search(r"\bTop\s+\d+\s+Russia\b", title_text, re.I)
        or re.search(r"\bTop\s+\d+\s+(?:Companies|Specialists|Providers|Operators|Systems)\s+Russia\b", title_text, re.I)
    ):
        errors.append(f"{rel}: unnatural EN title construction; use 'in Russia'.")
    if not re.search(r'<meta\s+name="description"\s+content="[^"]{20,}"', text, re.I):
        errors.append(f"{rel}: missing meta description.")
    canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', text, re.I)
    if not canonical:
        errors.append(f"{rel}: missing canonical.")
    elif canonical.group(1) != expected_url:
        errors.append(f"{rel}: canonical is {canonical.group(1)!r}, expected {expected_url!r}.")

    for counterpart_key, counterpart_cfg in LANGUAGES.items():
        counterpart = localized_file(name, counterpart_key)
        if not counterpart.exists():
            continue
        counterpart_url = public_url_for_file(counterpart)
        if not has_hreflang(text, counterpart_cfg["hreflang"], counterpart_url):
            errors.append(
                f"{rel}: missing hreflang={counterpart_cfg['hreflang']} for existing counterpart {counterpart_url}."
            )
    ru_counterpart = localized_file(name, "ru")
    if ru_counterpart.exists():
        ru_url = public_url_for_file(ru_counterpart)
        if not has_hreflang(text, "x-default", ru_url):
            errors.append(f"{rel}: x-default must point to RU counterpart {ru_url}.")
    if len(re.findall(r"<h1(?:\s[^>]*)?>", text, re.I)) != 1:
        errors.append(f"{rel}: must contain exactly one H1.")
    if 'application/ld+json' not in text:
        errors.append(f"{rel}: missing Schema.org JSON-LD.")

    page_schema = schema_objects_by_type(text, rel)
    needs_breadcrumb = is_research or name in {"ratings.html", "methodology.html"}
    if needs_breadcrumb:
        breadcrumb_nodes = page_schema.get("BreadcrumbList", [])
        if len(breadcrumb_nodes) != 1:
            errors.append(f"{rel}: expected exactly 1 BreadcrumbList, found {len(breadcrumb_nodes)}.")
        visible_breadcrumb = re.search(
            r'<nav\b[^>]*class=["\'][^"\']*\bbreadcrumbs\b[^"\']*["\'][^>]*>([\s\S]*?)</nav>',
            text,
            re.I,
        )
        if not visible_breadcrumb:
            errors.append(f"{rel}: missing visible breadcrumbs.")

        local_home = localized_file("index.html", lang_key)
        if local_home.exists():
            expected_home_href = localized_href("index.html", lang_key)
            if visible_breadcrumb:
                first_href = re.search(r'<a\b[^>]*href=["\']([^"\']+)["\']', visible_breadcrumb.group(1), re.I)
                if not first_href or first_href.group(1) != expected_home_href:
                    errors.append(
                        f"{rel}: first visible breadcrumb must link to local-language home {expected_home_href}."
                    )
            if breadcrumb_nodes:
                items = sorted(
                    [item for item in (breadcrumb_nodes[0].get("itemListElement") or []) if isinstance(item, dict)],
                    key=lambda item: item.get("position", 0),
                )
                expected_home_url = public_url_for_file(local_home)
                if not items or items[0].get("item") != expected_home_url:
                    errors.append(
                        f"{rel}: BreadcrumbList first item must be local-language home {expected_home_url}."
                    )

        local_catalog = localized_file("ratings.html", lang_key)
        if is_research and local_catalog.exists() and breadcrumb_nodes:
            items = sorted(
                [item for item in (breadcrumb_nodes[0].get("itemListElement") or []) if isinstance(item, dict)],
                key=lambda item: item.get("position", 0),
            )
            expected_catalog_url = public_url_for_file(local_catalog)
            if len(items) < 2 or items[1].get("item") != expected_catalog_url:
                errors.append(
                    f"{rel}: BreadcrumbList second item must be local-language catalog {expected_catalog_url}."
                )

    if is_root_research and breadcrumb_nodes:
        research_id = name[:-5]
        topic = topic_by_research_id.get(research_id)
        if topic:
            expected_topic_url = f"{BASE}/topics/{topic['slug']}.html"
            items = sorted(
                [item for item in (breadcrumb_nodes[0].get("itemListElement") or []) if isinstance(item, dict)],
                key=lambda item: item.get("position", 0),
            )
            if len(items) < 4 or items[2].get("item") != expected_topic_url or items[-1].get("item") != expected_url:
                errors.append(
                    f"{rel}: RU research breadcrumb must include thematic hub {expected_topic_url} before the current page."
                )
            expected_topic_href = f"/topics/{topic['slug']}.html"
            if visible_breadcrumb and f'href="{expected_topic_href}"' not in visible_breadcrumb.group(1):
                errors.append(
                    f"{rel}: visible RU breadcrumb must link to thematic hub {expected_topic_href}."
                )

    html_lang = re.search(r'<html\b[^>]*\blang=["\']([^"\']+)["\']', text, re.I)
    expected_lang = LANGUAGES[lang_key]["html_lang"]
    if not html_lang or html_lang.group(1).lower() != expected_lang.lower():
        errors.append(f"{rel}: <html lang> must be {expected_lang}.")

    required_og = ["og:type", "og:site_name", "og:locale", "og:title", "og:description", "og:url", "og:image", "og:image:alt"]
    expected_og_locale = LANGUAGES[lang_key]["og_locale"]
    locale_match = re.search(r'<meta\b(?=[^>]*\bproperty=["\']og:locale["\'])[^>]*\bcontent=["\']([^"\']+)["\'][^>]*>', text, re.I)
    if locale_match and locale_match.group(1) != expected_og_locale:
        errors.append(f"{rel}: og:locale is {locale_match.group(1)!r}, expected {expected_og_locale!r}.")
    for prop in required_og:
        count = len(re.findall(
            rf'<meta\b(?=[^>]*\bproperty=["\']{re.escape(prop)}["\'])[^>]*>',
            text,
            re.I,
        ))
        if count != 1:
            errors.append(f"{rel}: Open Graph property {prop} must appear exactly once; found {count}.")

    if "indexresearch-ru.github.io" in text:
        errors.append(f"{rel}: contains staging GitHub Pages hostname indexresearch-ru.github.io.")

    for href in re.findall(r'href=["\']([^"\']*)["\']', text, re.I):
        if not href:
            errors.append(f"{rel}: contains empty href.")
            continue
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        local = None
        if href.startswith("/"):
            local = href.split("#", 1)[0].split("?", 1)[0]
            if local == "/":
                local = "/index.html"
        elif re.match(r"^[^:/?#]+\.html(?:[?#].*)?$", href):
            local = "/" + href.split("#", 1)[0].split("?", 1)[0]
        if local and local.endswith(".html"):
            target = ROOT / local.lstrip("/")
            if not target.exists():
                errors.append(f"{rel}: internal link points to missing file: {href}.")

    if lang_key != "ru":
        for anchor in re.finditer(r'<a\b([^>]*)href=["\']([^"\']+)["\']([^>]*)>', text, re.I):
            attrs_text = (anchor.group(1) or "") + " " + (anchor.group(3) or "")
            href = anchor.group(2)
            if "lang-link" in attrs_text or re.search(r'\bhreflang\s*=', attrs_text, re.I):
                continue
            target_info = internal_href_target(href, expected_url)
            if not target_info:
                continue
            target_lang, target_name = target_info
            if target_lang == lang_key:
                continue
            local_counterpart = localized_file(target_name, lang_key)
            if local_counterpart.exists():
                errors.append(
                    f"{rel}: internal link {href!r} crosses language although local counterpart exists: "
                    f"{localized_href(target_name, lang_key)!r}."
                )

    robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', text, re.I)
    indexed = not (robots and "noindex" in robots.group(1).lower())
    if indexed and expected_url not in sitemap_urls:
        errors.append(f"{rel}: missing from sitemap.xml.")

    if is_research:
        slug = name[:-5]
        canonical_github_repo = f"https://github.com/IndexResearch-ru/{slug}"

        catalog_text = LOCALIZED_RATINGS[lang_key]
        expected_catalog_href = localized_href(name, lang_key)
        catalog_label = localized_file("ratings.html", lang_key).relative_to(ROOT).as_posix()

        # v4.1 migration model:
        # RU always uses the canonical data/evidence repo.
        # EN/CN use a language presentation repo once the localized catalog links to it;
        # legacy pages may continue to fall back to the canonical repo until migrated.
        if lang_key == "en":
            localized_github_repo = f"{canonical_github_repo}-en"
        elif lang_key == "cn":
            localized_github_repo = f"{canonical_github_repo}-cn"
        else:
            localized_github_repo = canonical_github_repo

        presentation_github_repo = (
            localized_github_repo
            if catalog_text and f'href="{localized_github_repo}"' in catalog_text
            else canonical_github_repo
        )

        if catalog_text:
            if f'href="{expected_catalog_href}"' not in catalog_text:
                errors.append(f"{rel}: research page is not linked from {catalog_label}.")

            if f'href="{presentation_github_repo}"' not in catalog_text:
                errors.append(
                    f"{rel}: language-matched GitHub repository is not linked directly from {catalog_label}."
                )

        if presentation_github_repo == canonical_github_repo:
            if len(re.findall(rf'href="{re.escape(canonical_github_repo)}"', text)) < 2:
                errors.append(
                    f"{rel}: summary page must contain at least 2 visible links to the canonical GitHub repository."
                )
        else:
            if not re.search(rf'href="{re.escape(presentation_github_repo)}"', text):
                errors.append(
                    f"{rel}: summary page must contain a visible link to the language presentation GitHub repository."
                )
            if not re.search(rf'href="{re.escape(canonical_github_repo)}"', text):
                errors.append(
                    f"{rel}: localized summary page must also link to the canonical data/evidence GitHub repository."
                )

        site_url = expected_url
        if not re.search(rf'"url"\s*:\s*"{re.escape(site_url)}"', text):
            errors.append(f"{rel}: Dataset.url must point to the IndexResearch summary page.")
        if not re.search(rf'"sameAs"\s*:\s*"{re.escape(canonical_github_repo)}"', text):
            errors.append(f"{rel}: Dataset.sameAs must point to the canonical data/evidence GitHub repository.")
        if not re.search(rf'"@id"\s*:\s*"{re.escape(site_url)}#dataset"', text):
            errors.append(f"{rel}: Dataset @id must use the IndexResearch summary URL.")

        if not re.search(r'<link[^>]+href=["\']/?assets/style\.css\?v=[^"\']+["\']', text, re.I):
            errors.append(f"{rel}: research page stylesheet must use cache-busting ?v=.")

        required_components = [
            "research-snapshot",
            "research-facts",
            "research-table--ranking",
            "research-table--criteria",
            "research-prose",
            "research-top3",
            "research-source-list",
            "research-citation",
        ]
        for component in required_components:
            if component not in text:
                errors.append(f"{rel}: missing required v3.3.2 component .{component}.")

        snapshot = re.search(
            r'<div[^>]+class=["\'][^"\']*research-snapshot[^"\']*["\'][^>]*>([\s\S]*?)</div>',
            text,
            re.I,
        )
        if snapshot and re.search(r"<(?:img|svg)\b", snapshot.group(1), re.I):
            errors.append(f"{rel}: research-snapshot must remain text-first; img/svg found inside it.")

        graph = jsonld_graph(text, rel)
        by_type = {}
        for obj in graph:
            if not isinstance(obj, dict):
                continue
            obj_type = obj.get("@type")
            types = obj_type if isinstance(obj_type, list) else [obj_type]
            for item_type in types:
                if item_type:
                    by_type.setdefault(item_type, []).append(obj)

        for schema_type in ["Dataset", "Article", "ItemList", "FAQPage", "BreadcrumbList"]:
            if schema_type not in by_type:
                errors.append(f"{rel}: missing Schema.org {schema_type}.")

        article_objects = by_type.get("Article", [])
        if article_objects:
            article_obj = article_objects[0]
            article_same_as = article_obj.get("sameAs")
            article_based_on = article_obj.get("isBasedOn")
            if presentation_github_repo != canonical_github_repo:
                if article_same_as != presentation_github_repo:
                    errors.append(
                        f"{rel}: Article.sameAs must point to the language presentation GitHub repository."
                    )
                based_on_id = (
                    article_based_on.get("@id")
                    if isinstance(article_based_on, dict)
                    else article_based_on
                )
                if based_on_id != canonical_github_repo:
                    errors.append(
                        f"{rel}: localized Article.isBasedOn must point to the canonical data/evidence GitHub repository."
                    )

        ranking_match = re.search(
            r'<table[^>]+class=["\'][^"\']*research-table--ranking[^"\']*["\'][^>]*>[\s\S]*?<tbody>([\s\S]*?)</tbody>',
            text,
            re.I,
        )
        ranking_rows = (
            len(re.findall(r"<tr(?:\s[^>]*)?>", ranking_match.group(1), re.I))
            if ranking_match
            else 0
        )
        if ranking_rows < 3:
            errors.append(f"{rel}: full ranking/result table has only {ranking_rows} rows.")

        item_lists = by_type.get("ItemList", [])
        if item_lists:
            item_count = len(item_lists[0].get("itemListElement") or [])
            if item_count != ranking_rows:
                errors.append(
                    f"{rel}: ItemList count {item_count} does not match visible ranking rows {ranking_rows}."
                )

        main_scope_match = re.search(r"<main\b[^>]*>([\s\S]*?)</main>", text, re.I)
        faq_scope = main_scope_match.group(1) if main_scope_match else text
        visible_faq = [
            visible_text(question)
            for question in re.findall(
                r"<details[^>]*>\s*<summary>([\s\S]*?)</summary>",
                faq_scope,
                re.I,
            )
        ]
        if not 5 <= len(visible_faq) <= 10:
            errors.append(f"{rel}: visible FAQ must contain 5-10 questions; found {len(visible_faq)}.")

        faq_pages = by_type.get("FAQPage", [])
        if faq_pages:
            schema_faq = [
                visible_text(entity.get("name", ""))
                for entity in (faq_pages[0].get("mainEntity") or [])
                if isinstance(entity, dict)
            ]
            if schema_faq != visible_faq:
                errors.append(f"{rel}: FAQPage questions/order must match visible FAQ exactly.")

        datasets = by_type.get("Dataset", [])
        if datasets:
            dataset_dump = json.dumps(datasets[0], ensure_ascii=False)
            if "RESULTS.json" not in dataset_dump:
                errors.append(f"{rel}: Dataset.distribution must expose RESULTS.json.")
            if "SOURCE_REGISTER.csv" not in dataset_dump:
                errors.append(f"{rel}: Dataset.distribution must expose SOURCE_REGISTER.csv.")
            if not any(
                candidate in dataset_dump
                for candidate in ["SCORE_MATRIX.csv", "OBSERVATION_MATRIX.csv", "CURRENT_RECHECK.csv"]
            ):
                errors.append(f"{rel}: Dataset.distribution must expose SCORE_MATRIX.csv or an equivalent matrix.")

        # A translated research page must preserve quantitative results and release identity.
        if is_translated_research:
            translated_label = "EN" if is_en_research else "CN"
            expected_schema_language = "en" if is_en_research else "zh-CN"
            ru_path = ROOT / name
            ru_text = ru_path.read_text(encoding="utf-8")
            ru_scores = [
                value.replace(",", ".")
                for value in re.findall(r'<td class=["\']num["\']>(?:<strong>)?([0-9]+(?:[.,][0-9]+)?/100)', ru_text, re.I)
            ]
            translated_scores = [
                value.replace(",", ".")
                for value in re.findall(r'<td class=["\']num["\']>(?:<strong>)?([0-9]+(?:[.,][0-9]+)?/100)', text, re.I)
            ]
            if ru_scores != translated_scores:
                errors.append(
                    f"{rel}: {translated_label} ranking scores differ from the RU canonical research page."
                )

            ru_ranking_match = re.search(
                r'<table[^>]+class=["\'][^"\']*research-table--ranking[^"\']*["\'][^>]*>[\s\S]*?<tbody>([\s\S]*?)</tbody>',
                ru_text,
                re.I,
            )
            ru_ranking_rows = (
                len(re.findall(r"<tr(?:\s[^>]*)?>", ru_ranking_match.group(1), re.I))
                if ru_ranking_match else 0
            )
            if ranking_rows != ru_ranking_rows:
                errors.append(
                    f"{rel}: visible ranking row count {ranking_rows} differs from RU canonical {ru_ranking_rows}."
                )

            ru_types = schema_objects_by_type(ru_text, name)
            translated_types = schema_objects_by_type(text, rel)
            ru_datasets = ru_types.get("Dataset", [])
            translated_datasets = translated_types.get("Dataset", [])
            if ru_datasets and translated_datasets:
                for field in ("datePublished", "dateModified", "version"):
                    if ru_datasets[0].get(field) != translated_datasets[0].get(field):
                        errors.append(
                            f"{rel}: Dataset.{field} differs from RU canonical page "
                            f"({translated_datasets[0].get(field)!r} vs {ru_datasets[0].get(field)!r})."
                        )
                if translated_datasets[0].get("inLanguage") != expected_schema_language:
                    errors.append(f"{rel}: Dataset.inLanguage must be {expected_schema_language!r}.")

            translated_articles = translated_types.get("Article", [])
            if translated_articles and translated_articles[0].get("inLanguage") != expected_schema_language:
                errors.append(f"{rel}: Article.inLanguage must be {expected_schema_language!r}.")

            ru_item_lists = ru_types.get("ItemList", [])
            translated_item_lists = translated_types.get("ItemList", [])
            if ru_item_lists and translated_item_lists:
                if itemlist_signature(ru_item_lists[0]) != itemlist_signature(translated_item_lists[0]):
                    errors.append(
                        f"{rel}: ItemList quantitative identity/order differs from RU canonical page."
                    )

index_text = (ROOT / "index.html").read_text(encoding="utf-8") if (ROOT / "index.html").exists() else ""
if not re.search(r'"sameAs"\s*:\s*\[[^\]]*"https://github.com/IndexResearch-ru"', index_text, re.S):
    errors.append("index.html: Organization.sameAs must include the IndexResearch GitHub organization.")

if not (ROOT / "assets" / "analytics.js").exists():
    errors.append("assets/analytics.js is missing.")

style_path = ROOT / "assets" / "style.css"
if not style_path.exists():
    errors.append("assets/style.css is missing.")
else:
    style_text = style_path.read_text(encoding="utf-8")
    required_style_tokens = [
        "--brand:#0E3455",
        ".research-facts{grid-template-columns:repeat(2,minmax(0,1fr))",
        ".research-table-wrap{overflow:visible",
        ".research-table--ranking tr",
        ".research-table--criteria tr",
    ]
    for token in required_style_tokens:
        if token not in style_text:
            errors.append(f"assets/style.css: missing v3.3.2 mobile/style rule containing {token!r}.")
    if "#1f4d3f" in style_text.lower():
        errors.append("assets/style.css: obsolete green #1f4d3f is still present.")

for favicon_name in [
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "mstile-150x150.png",
]:
    if not (ROOT / favicon_name).exists():
        errors.append(f"{favicon_name} is missing.")
if not (ROOT / "assets" / "indexresearch-shield.svg").exists():
    errors.append("assets/indexresearch-shield.svg is missing.")

indexnow_key = "7e92dc3e0c4b67cbf9bf7eaa809b842e96af1ec78c042a056bf07e233eb6836d"
indexnow_key_path = ROOT / f"{indexnow_key}.txt"
if not indexnow_key_path.exists():
    errors.append("IndexNow key file is missing from the site root.")
elif indexnow_key_path.read_text(encoding="utf-8").strip() != indexnow_key:
    errors.append("IndexNow key file content does not match the configured key.")
if not (ROOT / "scripts" / "indexnow_submit.py").exists():
    errors.append("scripts/indexnow_submit.py is missing.")

robots_path = ROOT / "robots.txt"
if not robots_path.exists():
    errors.append("robots.txt is missing.")
else:
    robots_text = robots_path.read_text(encoding="utf-8")
    required_robots_lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /.github/",
        "Disallow: /scripts/",
        "Disallow: /templates/",
        "Disallow: /README.md",
        "Sitemap: https://indexresearch.ru/sitemap.xml",
    ]
    for line in required_robots_lines:
        if line not in robots_text:
            errors.append(f"robots.txt is missing required rule: {line}")

    if "Clean-param:" not in robots_text:
        errors.append("robots.txt must contain Yandex Clean-param rules for tracking parameters.")

    for param in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "gclid", "fbclid", "yclid"]:
        if param not in robots_text:
            errors.append(f"robots.txt Clean-param rules are missing expected tracking parameter: {param}")

if errors:
    print("SITE QA FAILED")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print(f"SITE QA PASSED: {len(html_paths)} HTML pages checked.")

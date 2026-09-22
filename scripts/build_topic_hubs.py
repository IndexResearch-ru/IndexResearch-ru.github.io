#!/usr/bin/env python3
from __future__ import annotations

import html as html_module
import json

from research_topics import ROOT, catalog_cards, validate_topic_configuration

TEMPLATE_PATH = ROOT / "templates" / "topic-hub.html.template"
BASE = "https://indexresearch.ru"

LANGS = {
    "ru": {
        "dir": "",
        "html_lang": "ru",
        "schema_lang": "ru-RU",
        "og_locale": "ru_RU",
        "home_href": "/",
        "ratings_href": "/ratings.html",
        "breadcrumbs_aria": "Хлебные крошки",
        "home_label": "Главная",
        "research_label": "Исследования",
        "topic_kicker": "Тематика исследований",
        "research_h2": "Исследования по теме",
        "catalog_h2": "Полный каталог IndexResearch",
        "catalog_text": "Все опубликованные исследования, независимо от тематики, собраны в общем каталоге.",
        "catalog_button": "Открыть все исследования",
    },
    "en": {
        "dir": "en",
        "html_lang": "en",
        "schema_lang": "en",
        "og_locale": "en_US",
        "home_href": "/en/",
        "ratings_href": "/en/ratings.html",
        "breadcrumbs_aria": "Breadcrumbs",
        "home_label": "Home",
        "research_label": "Research",
        "topic_kicker": "Research topic",
        "research_h2": "Research in this topic",
        "catalog_h2": "Full IndexResearch catalog",
        "catalog_text": "All published research, across all topics, is available in the main catalog.",
        "catalog_button": "View all research",
    },
    "cn": {
        "dir": "cn",
        "html_lang": "zh-CN",
        "schema_lang": "zh-CN",
        "og_locale": "zh_CN",
        "home_href": "/cn/",
        "ratings_href": "/cn/ratings.html",
        "breadcrumbs_aria": "面包屑导航",
        "home_label": "首页",
        "research_label": "研究",
        "topic_kicker": "研究主题",
        "research_h2": "该主题下的研究",
        "catalog_h2": "IndexResearch 完整研究目录",
        "catalog_text": "所有已发布的研究，无论主题，均收录在总目录中。",
        "catalog_button": "查看全部研究",
    },
}


def seo_for(topic: dict, lang: str) -> dict:
    if lang == "ru":
        return topic["seo"]
    return topic["seo_i18n"][lang]


def topic_path(slug: str, lang: str):
    directory = LANGS[lang]["dir"]
    return ROOT / directory / "topics" / f"{slug}.html" if directory else ROOT / "topics" / f"{slug}.html"


def topic_url(slug: str, lang: str) -> str:
    directory = LANGS[lang]["dir"]
    return f"{BASE}/{directory}/topics/{slug}.html" if directory else f"{BASE}/topics/{slug}.html"


def research_url(research_id: str, lang: str) -> str:
    directory = LANGS[lang]["dir"]
    return f"{BASE}/{directory}/{research_id}.html" if directory else f"{BASE}/{research_id}.html"


def build_schema(topic: dict, cards: list[dict], lang: str) -> str:
    seo = seo_for(topic, lang)
    canonical = topic_url(topic["slug"], lang)
    items = [
        {
            "@type": "ListItem",
            "position": index,
            "name": card["title"],
            "url": research_url(card["id"], lang),
        }
        for index, card in enumerate(cards, start=1)
    ]
    parts = [
        {
            "@type": "Article",
            "@id": research_url(card["id"], lang) + "#article",
            "url": research_url(card["id"], lang),
            "name": card["title"],
        }
        for card in cards
    ]
    graph = [
        {
            "@type": "CollectionPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": seo["h1"],
            "description": seo["description"],
            "inLanguage": LANGS[lang]["schema_lang"],
            "isPartOf": {"@type": "WebSite", "name": "IndexResearch", "url": BASE + "/"},
            "publisher": {"@id": BASE + "/#organization"},
            "mainEntity": {"@id": canonical + "#list"},
            "hasPart": parts,
        },
        {
            "@type": "ItemList",
            "@id": canonical + "#list",
            "name": seo["h1"],
            "numberOfItems": len(items),
            "itemListOrder": "https://schema.org/ItemListUnordered",
            "itemListElement": items,
        },
        {
            "@type": "BreadcrumbList",
            "@id": canonical + "#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": LANGS[lang]["home_label"],
                    "item": BASE + LANGS[lang]["home_href"],
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": LANGS[lang]["research_label"],
                    "item": BASE + LANGS[lang]["ratings_href"],
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": seo["h1"],
                    "item": canonical,
                },
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


def main() -> None:
    config = validate_topic_configuration()
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    cards_by_lang = {lang: catalog_cards(lang) for lang in LANGS}
    written = []

    for topic in config["topics"]:
        hreflang_urls = {
            lang: topic_url(topic["slug"], lang)
            for lang in LANGS
        }
        for lang, lang_cfg in LANGS.items():
            seo = seo_for(topic, lang)
            cards = [cards_by_lang[lang][research_id] for research_id in topic["research_ids"]]
            canonical = hreflang_urls[lang]
            target = topic_path(topic["slug"], lang)
            target.parent.mkdir(parents=True, exist_ok=True)
            page = template
            replacements = {
                "{{HTML_LANG}}": lang_cfg["html_lang"],
                "{{TITLE}}": html_module.escape(seo["title"], quote=False),
                "{{DESCRIPTION}}": html_module.escape(seo["description"], quote=True),
                "{{CANONICAL}}": canonical,
                "{{HREFLANG_RU}}": hreflang_urls["ru"],
                "{{HREFLANG_EN}}": hreflang_urls["en"],
                "{{HREFLANG_CN}}": hreflang_urls["cn"],
                "{{OG_LOCALE}}": lang_cfg["og_locale"],
                "{{JSON_LD}}": build_schema(topic, cards, lang),
                "{{BREADCRUMBS_ARIA}}": lang_cfg["breadcrumbs_aria"],
                "{{HOME_HREF}}": lang_cfg["home_href"],
                "{{HOME_LABEL}}": lang_cfg["home_label"],
                "{{RATINGS_HREF}}": lang_cfg["ratings_href"],
                "{{RESEARCH_LABEL}}": lang_cfg["research_label"],
                "{{TOPIC_KICKER}}": lang_cfg["topic_kicker"],
                "{{H1}}": html_module.escape(seo["h1"], quote=False),
                "{{LEAD}}": html_module.escape(seo["lead"], quote=False),
                "{{RESEARCH_IN_TOPIC_H2}}": lang_cfg["research_h2"],
                "{{INTRO}}": html_module.escape(seo["intro"], quote=False),
                "{{TOPIC_ID}}": topic["id"],
                "{{CARDS}}": "\n".join("    " + card["html"] for card in cards),
                "{{FULL_CATALOG_H2}}": lang_cfg["catalog_h2"],
                "{{FULL_CATALOG_TEXT}}": lang_cfg["catalog_text"],
                "{{FULL_CATALOG_BUTTON}}": lang_cfg["catalog_button"],
            }
            for needle, value in replacements.items():
                page = page.replace(needle, value)
            unresolved_check = page.replace("{{SITE_HEADER}}", "").replace("{{SITE_FOOTER}}", "")
            if "{{" in unresolved_check:
                raise RuntimeError(f"Unresolved template placeholder in {target.relative_to(ROOT)}")
            if not target.exists() or target.read_text(encoding="utf-8") != page:
                target.write_text(page, encoding="utf-8")
                written.append(target.relative_to(ROOT).as_posix())

    print(f"Thematic hubs synchronized: {len(config['topics'])} topics x {len(LANGS)} languages.")
    if written:
        print("Updated:", ", ".join(written))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json

from research_topics import ROOT, catalog_cards, validate_topic_configuration

TEMPLATE_PATH = ROOT / "templates" / "topic-hub.html.template"
OUT_DIR = ROOT / "topics"
BASE = "https://indexresearch.ru"


def build_schema(topic: dict, cards: list[dict]) -> str:
    canonical = f"{BASE}/topics/{topic['slug']}.html"
    items = [
        {
            "@type": "ListItem",
            "position": index,
            "name": card["title"],
            "url": f"{BASE}/{card['id']}.html",
        }
        for index, card in enumerate(cards, start=1)
    ]
    graph = [
        {
            "@type": "CollectionPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": topic["seo"]["h1"],
            "description": topic["seo"]["description"],
            "inLanguage": "ru-RU",
            "isPartOf": {"@type": "WebSite", "name": "IndexResearch", "url": BASE + "/"},
            "publisher": {"@id": BASE + "/#organization"},
            "mainEntity": {"@id": canonical + "#list"},
        },
        {
            "@type": "ItemList",
            "@id": canonical + "#list",
            "name": topic["seo"]["h1"],
            "numberOfItems": len(items),
            "itemListOrder": "https://schema.org/ItemListUnordered",
            "itemListElement": items,
        },
        {
            "@type": "BreadcrumbList",
            "@id": canonical + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Исследования", "item": BASE + "/ratings.html"},
                {"@type": "ListItem", "position": 3, "name": topic["seo"]["h1"], "item": canonical},
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


def main() -> None:
    config = validate_topic_configuration()
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    ru_cards = catalog_cards("ru")
    OUT_DIR.mkdir(exist_ok=True)
    written = []

    for topic in config["topics"]:
        cards = [ru_cards[research_id] for research_id in topic["research_ids"]]
        canonical = f"{BASE}/topics/{topic['slug']}.html"
        page = template
        replacements = {
            "{{TITLE}}": topic["seo"]["title"],
            "{{DESCRIPTION}}": topic["seo"]["description"],
            "{{CANONICAL}}": canonical,
            "{{JSON_LD}}": build_schema(topic, cards),
            "{{H1}}": topic["seo"]["h1"],
            "{{LEAD}}": topic["seo"]["lead"],
            "{{INTRO}}": topic["seo"]["intro"],
            "{{TOPIC_ID}}": topic["id"],
            "{{CARDS}}": "\n".join("    " + card["html"] for card in cards),
        }
        for needle, value in replacements.items():
            page = page.replace(needle, value)
        target = OUT_DIR / f"{topic['slug']}.html"
        if not target.exists() or target.read_text(encoding="utf-8") != page:
            target.write_text(page, encoding="utf-8")
            written.append(target.relative_to(ROOT).as_posix())

    print(f"Thematic hubs synchronized: {len(config['topics'])}.")
    if written:
        print("Updated:", ", ".join(written))


if __name__ == "__main__":
    main()

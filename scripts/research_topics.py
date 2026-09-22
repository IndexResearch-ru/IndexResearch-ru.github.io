#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import html as html_module
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "templates" / "research-topics.json"
RATINGS_PATHS = {
    "ru": ROOT / "ratings.html",
    "en": ROOT / "en" / "ratings.html",
    "cn": ROOT / "cn" / "ratings.html",
}
LANG_PREFIX = {"ru": "", "en": "/en", "cn": "/cn"}


def visible_text(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html_module.unescape(fragment)).strip()


def load_topic_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError("templates/research-topics.json is missing")
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data.get("topics"), list) or not data["topics"]:
        raise RuntimeError("research-topics.json must contain a non-empty topics list")
    return data


def catalog_cards(lang: str) -> dict[str, dict]:
    path = RATINGS_PATHS[lang]
    if not path.exists():
        raise RuntimeError(f"Localized ratings page is missing: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    cards: dict[str, dict] = {}
    pattern = re.compile(
        r'<article\b(?=[^>]*\bdata-research-card=["\']true["\'])(?=[^>]*\bdata-research-id=["\']([^"\']+)["\'])[^>]*>[\s\S]*?</article>',
        re.I,
    )
    for match in pattern.finditer(text):
        block = match.group(0)
        research_id = match.group(1)
        heading = re.search(
            r'<h2\b[^>]*>\s*<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>\s*</h2>',
            block,
            re.I,
        )
        published = re.search(r'\bdata-published=["\']([^"\']+)["\']', block, re.I)
        if not heading:
            raise RuntimeError(f"{path.relative_to(ROOT)}: card {research_id} has no linked H2")
        cards[research_id] = {
            "id": research_id,
            "href": heading.group(1),
            "title": visible_text(heading.group(2)),
            "published": published.group(1) if published else "",
            "html": block,
        }
    return cards


def canonical_catalog_ids() -> list[str]:
    return list(catalog_cards("ru").keys())


def topic_configuration_errors() -> list[str]:
    config = load_topic_config()
    canonical = canonical_catalog_ids()
    flat: list[str] = []
    topic_ids: list[str] = []
    slugs: list[str] = []
    errors: list[str] = []

    for topic in config["topics"]:
        topic_ids.append(str(topic.get("id", "")))
        slugs.append(str(topic.get("slug", "")))
        flat.extend(topic.get("research_ids") or [])
        labels = topic.get("labels") or {}
        for lang in ("ru", "en", "cn"):
            if not labels.get(lang):
                errors.append(f"Topic {topic.get('id')} is missing label for {lang}.")

    duplicates = sorted({item for item in flat if flat.count(item) > 1})
    missing = sorted(set(canonical) - set(flat))
    extra = sorted(set(flat) - set(canonical))
    if duplicates:
        errors.append("Research IDs assigned to multiple topics: " + ", ".join(duplicates))
    if missing:
        errors.append("Research IDs missing a topic: " + ", ".join(missing))
    if extra:
        errors.append("Topic config contains unknown research IDs: " + ", ".join(extra))
    if len(topic_ids) != len(set(topic_ids)):
        errors.append("Duplicate topic id in research-topics.json.")
    if len(slugs) != len(set(slugs)):
        errors.append("Duplicate topic slug in research-topics.json.")

    for lang in ("en", "cn"):
        localized = catalog_cards(lang)
        absent = [item for item in canonical if item not in localized]
        if absent:
            errors.append(f"{lang}/ratings.html is missing research IDs used by topic navigation: " + ", ".join(absent))
    return errors


def validate_topic_configuration() -> dict:
    errors = topic_configuration_errors()
    if errors:
        raise RuntimeError(" | ".join(errors))
    return load_topic_config()


def render_topic_navigation(lang: str) -> tuple[str, str]:
    config = validate_topic_configuration()
    cards = catalog_cards(lang)
    labels = config["menu_labels"][lang]
    prefix = LANG_PREFIX[lang]
    desktop_topics = []
    mobile_topics = []

    for topic in config["topics"]:
        topic_label = html_module.escape(topic["labels"][lang])
        hub_href = f"/topics/{topic['slug']}.html"
        research_links = []
        for research_id in topic["research_ids"]:
            card = cards[research_id]
            href = f"{prefix}/{research_id}.html" if prefix else f"/{research_id}.html"
            research_links.append(f'<a href="{href}">{html_module.escape(card["title"])}</a>')
        research_html = "".join(research_links)
        open_label = html_module.escape(
            f'{labels["open_topic"]}: {topic["labels"][lang]}',
            quote=True,
        )
        desktop_topics.append(
            '<div class="nav-topic-entry">'
            f'<a class="nav-topic-link" href="{hub_href}" hreflang="ru">{topic_label}</a>'
            '<details class="nav-topic-more">'
            f'<summary aria-label="{open_label}"></summary>'
            f'<div class="nav-research-panel">{research_html}</div>'
            '</details></div>'
        )
        mobile_topics.append(
            '<details class="mobile-research">'
            f'<summary aria-label="{open_label}"></summary>'
            f'<a class="mobile-topic-link" href="{hub_href}" hreflang="ru">{topic_label}</a>'
            f'<div class="mobile-research-panel">{research_html}</div>'
            '</details>'
        )

    topics_label = html_module.escape(labels["topics"])
    desktop = (
        '<details class="nav-topics">'
        f'<summary>{topics_label}</summary>'
        f'<div class="nav-topics-panel">{"".join(desktop_topics)}</div>'
        '</details>'
    )
    mobile = (
        '<details class="mobile-topics">'
        f'<summary>{topics_label}</summary>'
        f'<div class="mobile-topics-panel">{"".join(mobile_topics)}</div>'
        '</details>'
    )
    return desktop, mobile

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
RATINGS = ROOT / "ratings.html"

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

INDEX_START = "<!-- RESEARCH_FEED_START -->"
INDEX_END = "<!-- RESEARCH_FEED_END -->"
INDEX_CARD_RE = re.compile(
    r'(<article\b[^>]*class="research-teaser"[^>]*\bdata-research-card="true"[^>]*>[\s\S]*?</article>)',
    re.IGNORECASE,
)

CATALOG_START = "<!-- RESEARCH_CATALOG_START -->"
CATALOG_END = "<!-- RESEARCH_CATALOG_END -->"
CATALOG_CARD_RE = re.compile(
    r'(<article\b[^>]*\bdata-research-card="true"[^>]*>[\s\S]*?</article>)',
    re.IGNORECASE,
)

P_RE = re.compile(r'<p(?:\s+class="([^"]*)")?>([\s\S]*?)</p>', re.IGNORECASE)
TITLE_RE = re.compile(r'<h2>([\s\S]*?)</h2>', re.IGNORECASE)
SUMMARY_LINK_RE = re.compile(r'<a class="button" href="(/[^"]+\.html)"', re.IGNORECASE)

RU_MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


class FeedError(RuntimeError):
    pass


def parse_card(card: str) -> dict[str, str]:
    opening = card.split(">", 1)[0] + ">"
    attrs = dict(ATTR_RE.findall(opening))
    required = ("data-published", "data-beneficiary", "data-research-id")
    missing = [name for name in required if not attrs.get(name)]
    if missing:
        raise FeedError(f"research card missing attributes: {', '.join(missing)}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", attrs["data-published"]):
        raise FeedError(
            f'{attrs["data-research-id"]}: data-published must be YYYY-MM-DD'
        )
    return attrs


def stable_priority(date: str, beneficiary: str) -> str:
    return hashlib.sha256(f"{date}|{beneficiary}".encode("utf-8")).hexdigest()


def mix_one_date(cards: list[str], date: str) -> list[str]:
    queues: dict[str, deque[str]] = defaultdict(deque)
    seen_ids: set[str] = set()

    parsed = []
    for card in cards:
        attrs = parse_card(card)
        rid = attrs["data-research-id"]
        if rid in seen_ids:
            raise FeedError(f"duplicate data-research-id: {rid}")
        seen_ids.add(rid)
        parsed.append((attrs["data-beneficiary"], rid, card))

    for beneficiary, rid, card in sorted(parsed, key=lambda x: (x[0], x[1])):
        queues[beneficiary].append(card)

    beneficiary_order = sorted(
        queues,
        key=lambda beneficiary: stable_priority(date, beneficiary),
    )

    result: list[str] = []
    while any(queues.values()):
        for beneficiary in beneficiary_order:
            if queues[beneficiary]:
                result.append(queues[beneficiary].popleft())

    return result


def normalize_catalog(html: str) -> tuple[str, list[str]]:
    if html.count(CATALOG_START) != 1 or html.count(CATALOG_END) != 1:
        raise FeedError("ratings.html must contain exactly one research marker pair")

    before, rest = html.split(CATALOG_START, 1)
    block, after = rest.split(CATALOG_END, 1)
    cards = CATALOG_CARD_RE.findall(block)
    if not cards:
        raise FeedError("ratings.html: research catalog contains no cards")

    if len(CATALOG_CARD_RE.findall(html)) != len(cards):
        raise FeedError("ratings.html: data-research-card found outside catalog markers")

    if CATALOG_CARD_RE.sub("", block).strip():
        raise FeedError("ratings.html: catalog markers may contain only research cards")

    by_date: dict[str, list[str]] = defaultdict(list)
    ids: set[str] = set()
    for card in cards:
        attrs = parse_card(card)
        rid = attrs["data-research-id"]
        if rid in ids:
            raise FeedError(f"ratings.html: duplicate data-research-id: {rid}")
        ids.add(rid)
        by_date[attrs["data-published"]].append(card)

    ordered: list[str] = []
    for date in sorted(by_date, reverse=True):
        ordered.extend(mix_one_date(by_date[date], date))

    normalized_block = "\n\n".join(card.strip() for card in ordered)
    normalized_html = f"{before}{CATALOG_START}\n{normalized_block}\n{CATALOG_END}{after}"
    return normalized_html, ordered


def ru_date(iso_date: str) -> str:
    year, month, day = (int(part) for part in iso_date.split("-"))
    return f"{day} {RU_MONTHS[month - 1]} {year}"


TAG_RE = re.compile(r"<[^>]+>")


def text_only(fragment: str) -> str:
    return re.sub(r"\\s+", " ", html.unescape(TAG_RE.sub("", fragment))).strip()


def ranking_paragraph(text: str) -> bool:
    return bool(
        re.search(r"\\b[123] место:", text, re.IGNORECASE)
        or re.search(r"(?:TOP|ТОП)-3:", text, re.IGNORECASE)
        or text.startswith("Максимальное соответствие сценарию:")
    )


def extract_top_items(paragraphs: list[str], research_id: str) -> tuple[list[str], int]:
    ranking_parts: list[str] = []
    consumed = 0

    for paragraph in paragraphs[1:]:
        plain = text_only(paragraph)
        if ranking_paragraph(plain):
            ranking_parts.append(plain)
            consumed += 1
            continue
        break

    if not ranking_parts:
        raise FeedError(f"{research_id}: compact homepage card has no TOP-3 block")

    ranking_text = " ".join(ranking_parts)
    items: dict[int, str] = {}

    for match in re.finditer(
        r"([123])\\s+место:\\s*(.*?)(?=(?:\\.\\s*[123]\\s+место:)|$)",
        ranking_text,
        re.IGNORECASE,
    ):
        items[int(match.group(1))] = match.group(2).strip().rstrip(".")

    snapshot = re.search(
        r"(?:TOP|ТОП)-3:\\s*(.+)$",
        ranking_text,
        re.IGNORECASE,
    )
    if snapshot and len(items) < 3:
        names = [part.strip().rstrip(".") for part in snapshot.group(1).split(",")]
        if len(names) >= 3:
            items = {1: names[0], 2: names[1], 3: names[2]}

    if 1 not in items and ranking_text.startswith("Максимальное соответствие сценарию:"):
        first = ranking_text.split("2 место:", 1)[0]
        first = first.replace("Максимальное соответствие сценарию:", "", 1).strip().rstrip(".")
        if first:
            items[1] = first

    if set(items) != {1, 2, 3}:
        raise FeedError(
            f"{research_id}: TOP-3 must resolve to exactly 3 ordered items, got {sorted(items)}"
        )

    return [items[1], items[2], items[3]], consumed


def split_meta_items(fragment: str) -> list[str]:
    text = text_only(fragment).rstrip(".")

    text = re.sub(
        r"^(\\d+\\s+[^,.]+?)\\s+оценены по\\s+(\\d+\\s+критериям?)\\.\\s*",
        r"\\1, \\2, ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\\.\\s*Опубликованы\\s+", ", ", text, flags=re.IGNORECASE)
    text = re.sub(r"\\s+и\\s+(?=\\d)", ", ", text)

    items = [part.strip().rstrip(".") for part in text.split(",") if part.strip()]
    return items or [text]


def render_home_card(catalog_card: str) -> str:
    attrs = parse_card(catalog_card)
    title_match = TITLE_RE.search(catalog_card)
    link_match = SUMMARY_LINK_RE.search(catalog_card)
    if not title_match or not link_match:
        raise FeedError(f'{attrs["data-research-id"]}: missing catalog title or summary link')

    paragraphs = []
    for match in P_RE.finditer(catalog_card):
        classes = set((match.group(1) or "").split())
        if "kicker" in classes or "note" in classes:
            continue
        paragraphs.append(match.group(2).strip())

    if len(paragraphs) < 3:
        raise FeedError(
            f'{attrs["data-research-id"]}: expected at least 3 compact-home paragraphs'
        )

    top_items, ranking_count = extract_top_items(
        paragraphs,
        attrs["data-research-id"],
    )

    meta_index = 1 + ranking_count
    if meta_index >= len(paragraphs):
        raise FeedError(f'{attrs["data-research-id"]}: compact homepage card has no corpus line')

    scenario = html.escape(text_only(paragraphs[0]))
    title = html.escape(text_only(title_match.group(1)))
    top_html = "\\n".join(
        f"<li>{html.escape(item)}</li>"
        for item in top_items
    )
    meta_html = "\\n".join(
        f"<li>{html.escape(item)}</li>"
        for item in split_meta_items(paragraphs[meta_index])
    )

    return f'''<article class="research-teaser" data-research-card="true" data-published="{attrs["data-published"]}" data-beneficiary="{attrs["data-beneficiary"]}" data-research-id="{attrs["data-research-id"]}">
<p class="research-teaser__date"><time datetime="{attrs["data-published"]}">{ru_date(attrs["data-published"])}</time></p>
<h3 class="research-teaser__title"><a href="{link_match.group(1)}">{title}</a></h3>
<p class="research-teaser__scenario">{scenario}</p>
<ol class="research-teaser__top-list">
{top_html}
</ol>
<ul class="research-teaser__meta-list">
{meta_html}
</ul>
</article>'''


def sync_home(index_html: str, catalog_cards: list[str]) -> str:
    if index_html.count(INDEX_START) != 1 or index_html.count(INDEX_END) != 1:
        raise FeedError("index.html must contain exactly one research marker pair")

    before, rest = index_html.split(INDEX_START, 1)
    _, after = rest.split(INDEX_END, 1)

    rendered = "\n\n".join(render_home_card(card) for card in catalog_cards)
    normalized = f"{before}{INDEX_START}\n{rendered}\n{INDEX_END}{after}"

    home_cards = INDEX_CARD_RE.findall(normalized)
    if len(home_cards) != len(catalog_cards):
        raise FeedError(
            f"index.html: expected {len(catalog_cards)} homepage research cards, got {len(home_cards)}"
        )

    home_ids = [parse_card(card)["data-research-id"] for card in home_cards]
    catalog_ids = [parse_card(card)["data-research-id"] for card in catalog_cards]
    if home_ids != catalog_ids:
        raise FeedError("index.html: homepage research order differs from ratings.html")

    feed = normalized.split(INDEX_START, 1)[1].split(INDEX_END, 1)[0]
    if 'class="note"' in feed:
        raise FeedError("index.html: disclosure note must not appear in compact homepage cards")

    return normalized


def normalize_all() -> dict[Path, tuple[str, str]]:
    original_ratings = RATINGS.read_text(encoding="utf-8")
    original_index = INDEX.read_text(encoding="utf-8")

    normalized_ratings, ordered_catalog = normalize_catalog(original_ratings)
    normalized_index = sync_home(original_index, ordered_catalog)

    return {
        RATINGS: (original_ratings, normalized_ratings),
        INDEX: (original_index, normalized_index),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate canonical catalog order and homepage synchronization",
    )
    args = parser.parse_args()

    try:
        pairs = normalize_all()
    except FeedError as exc:
        print(f"RESEARCH ORDER FAILED: {exc}")
        return 1

    changed = [path for path, (original, normalized) in pairs.items() if original != normalized]

    if args.check:
        if changed:
            print(
                "RESEARCH ORDER FAILED: non-canonical or unsynchronized "
                + ", ".join(path.name for path in changed)
            )
            return 1
        print("RESEARCH ORDER PASSED")
        return 0

    for path in changed:
        _, normalized = pairs[path]
        path.write_text(normalized, encoding="utf-8")

    if changed:
        print("Research listings updated:", ", ".join(path.name for path in changed))
    else:
        print("Research listings already canonical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

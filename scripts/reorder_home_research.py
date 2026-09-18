#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
    r'(<section\b[^>]*\bdata-research-card="true"[^>]*>[\s\S]*?</section>)',
    re.IGNORECASE,
)

CATALOG_START = "<!-- RESEARCH_CATALOG_START -->"
CATALOG_END = "<!-- RESEARCH_CATALOG_END -->"
CATALOG_CARD_RE = re.compile(
    r'(<article\b[^>]*\bdata-research-card="true"[^>]*>[\s\S]*?</article>)',
    re.IGNORECASE,
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

    # Stable order inside one beneficiary keeps repeated runs idempotent.
    for beneficiary, rid, card in sorted(parsed, key=lambda x: (x[0], x[1])):
        queues[beneficiary].append(card)

    totals = {beneficiary: len(queue) for beneficiary, queue in queues.items()}
    used = {beneficiary: 0 for beneficiary in queues}
    priorities = {
        beneficiary: stable_priority(date, beneficiary)
        for beneficiary in queues
    }

    result: list[str] = []
    previous: str | None = None

    while any(queues.values()):
        available = [beneficiary for beneficiary, queue in queues.items() if queue]
        alternatives = [beneficiary for beneficiary in available if beneficiary != previous]
        candidates = alternatives or available

        # Proportional round-robin. Each beneficiary gets an early slot,
        # while larger series are spread across the full publication-date group.
        beneficiary = min(
            candidates,
            key=lambda name: (
                used[name] / totals[name],
                priorities[name],
            ),
        )

        result.append(queues[beneficiary].popleft())
        used[beneficiary] += 1
        previous = beneficiary

    return result


def normalize_block(
    html: str,
    *,
    page_name: str,
    start: str,
    end: str,
    card_re: re.Pattern[str],
) -> str:
    if html.count(start) != 1 or html.count(end) != 1:
        raise FeedError(f"{page_name} must contain exactly one research marker pair")

    before, rest = html.split(start, 1)
    block, after = rest.split(end, 1)

    cards = card_re.findall(block)
    if not cards:
        raise FeedError(f"{page_name}: research block contains no cards")

    all_marked_cards = card_re.findall(html)
    if len(all_marked_cards) != len(cards):
        raise FeedError(
            f"{page_name}: data-research-card found outside research markers"
        )

    residual = card_re.sub("", block)
    if residual.strip():
        raise FeedError(
            f"{page_name}: research markers may contain only data-research-card items"
        )

    by_date: dict[str, list[str]] = defaultdict(list)
    global_ids: set[str] = set()
    for card in cards:
        attrs = parse_card(card)
        rid = attrs["data-research-id"]
        if rid in global_ids:
            raise FeedError(f"{page_name}: duplicate data-research-id: {rid}")
        global_ids.add(rid)
        by_date[attrs["data-published"]].append(card)

    ordered: list[str] = []
    for date in sorted(by_date, reverse=True):
        ordered.extend(mix_one_date(by_date[date], date))

    normalized = "\n\n".join(card.strip() for card in ordered)
    return f"{before}{start}\n{normalized}\n{end}{after}"


def validate_index_guards(html: str) -> None:
    research_like_re = re.compile(
        r'<section\b[^>]*class="section alt"[^>]*>[\s\S]*?'
        r'<p class="kicker">(?:Новый выпуск · )?\d{1,2} [^<]+ 20\d{2}[^<]*</p>'
        r'[\s\S]*?<a class="button" href="/[^"]+\.html"',
        re.IGNORECASE,
    )
    for match in research_like_re.finditer(html):
        opening = match.group(0).split(">", 1)[0] + ">"
        if 'data-research-card="true"' not in opening:
            raise FeedError(
                "index.html: dated research card found without feed metadata"
            )


def normalize_all() -> dict[Path, tuple[str, str]]:
    originals = {
        INDEX: INDEX.read_text(encoding="utf-8"),
        RATINGS: RATINGS.read_text(encoding="utf-8"),
    }

    validate_index_guards(originals[INDEX])

    normalized = {
        INDEX: normalize_block(
            originals[INDEX],
            page_name="index.html",
            start=INDEX_START,
            end=INDEX_END,
            card_re=INDEX_CARD_RE,
        ),
        RATINGS: normalize_block(
            originals[RATINGS],
            page_name="ratings.html",
            start=CATALOG_START,
            end=CATALOG_END,
            card_re=CATALOG_CARD_RE,
        ),
    }
    return {path: (originals[path], normalized[path]) for path in originals}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate canonical ordering without rewriting files",
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
                "RESEARCH ORDER FAILED: non-canonical order in "
                + ", ".join(path.name for path in changed)
            )
            return 1
        print("RESEARCH ORDER PASSED")
        return 0

    for path in changed:
        _, normalized = pairs[path]
        path.write_text(normalized, encoding="utf-8")

    if changed:
        print("Research ordering updated:", ", ".join(path.name for path in changed))
    else:
        print("Research ordering already canonical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

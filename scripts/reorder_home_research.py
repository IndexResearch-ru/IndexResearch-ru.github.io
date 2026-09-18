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
START = "<!-- RESEARCH_FEED_START -->"
END = "<!-- RESEARCH_FEED_END -->"

CARD_RE = re.compile(
    r'(<section\b[^>]*\bdata-research-card="true"[^>]*>[\s\S]*?</section>)',
    re.IGNORECASE,
)
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


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

    # Relative order inside one beneficiary is stable and independent of the
    # card's current position in index.html, which keeps repeated runs idempotent.
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

        # Proportional round-robin: beneficiaries that have received the
        # smallest share of their own daily quota go first. This exposes each
        # entity early, then spreads larger series across the whole date group.
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


def normalized_html(html: str) -> str:
    if html.count(START) != 1 or html.count(END) != 1:
        raise FeedError("index.html must contain exactly one research feed marker pair")

    before, rest = html.split(START, 1)
    feed, after = rest.split(END, 1)

    cards = CARD_RE.findall(feed)
    if not cards:
        raise FeedError("research feed contains no cards")

    residual = CARD_RE.sub("", feed)
    if residual.strip():
        raise FeedError(
            "research feed markers may contain only data-research-card sections"
        )

    by_date: dict[str, list[str]] = defaultdict(list)
    for card in cards:
        attrs = parse_card(card)
        by_date[attrs["data-published"]].append(card)

    ordered: list[str] = []
    for date in sorted(by_date, reverse=True):
        ordered.extend(mix_one_date(by_date[date], date))

    normalized_feed = "\n\n".join(card.strip() for card in ordered)
    return f"{before}{START}\n{normalized_feed}\n{END}{after}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate canonical order without rewriting index.html",
    )
    args = parser.parse_args()

    original = INDEX.read_text(encoding="utf-8")
    try:
        normalized = normalized_html(original)
    except FeedError as exc:
        print(f"HOME RESEARCH FEED FAILED: {exc}")
        return 1

    if args.check:
        if normalized != original:
            print("HOME RESEARCH FEED FAILED: index.html is not in canonical order")
            return 1
        print("HOME RESEARCH FEED PASSED")
        return 0

    if normalized != original:
        INDEX.write_text(normalized, encoding="utf-8")
        print("Homepage research feed reordered.")
    else:
        print("Homepage research feed already canonical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

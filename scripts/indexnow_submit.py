#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
HOST = "indexresearch.ru"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY = "7e92dc3e0c4b67cbf9bf7eaa809b842e96af1ec78c042a056bf07e233eb6836d"
KEY_FILE = f"{KEY}.txt"
KEY_LOCATION = f"{BASE}/{KEY_FILE}"
# A key rotation should bootstrap all current URLs once.
# Other maintenance-script changes do not affect public page content and should not trigger a full resubmission.
SETUP_FILES = {
    "scripts/indexnow_submit.py",
    KEY_FILE,
}


def git_changed(before: str | None) -> tuple[set[str], set[str]]:
    """Return (changed paths, deleted/renamed-away root HTML paths)."""
    if not before or set(before) == {"0"}:
        return set(), set()

    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-status", "--find-renames", before, "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        return set(), set()

    changed: set[str] = set()
    removed_html: set[str] = set()

    for raw in out.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        status = parts[0]

        if status.startswith("R") and len(parts) >= 3:
            old, new = parts[1], parts[2]
            changed.update({old, new})
            if _is_root_html(old):
                removed_html.add(old)
            continue

        if len(parts) < 2:
            continue

        path = parts[1]
        changed.add(path)
        if status.startswith("D") and _is_root_html(path):
            removed_html.add(path)

    return changed, removed_html


def _is_root_html(path: str) -> bool:
    p = Path(path)
    return p.parent == Path(".") and p.suffix.lower() == ".html"


def url_for_html(path: str) -> str:
    return f"{BASE}/" if path == "index.html" else f"{BASE}/{path}"


def all_current_urls() -> list[str]:
    return [
        url_for_html(p.name)
        for p in sorted(ROOT.glob("*.html"))
        if p.is_file()
    ]


def newly_linked_html(before: str | None) -> set[str]:
    """Find newly added root HTML links in index.html/ratings.html.

    This covers multi-commit publishing where the summary page is created first,
    its initial workflow fails QA, and a later catalog/homepage commit makes the
    release complete. The later successful push will submit both the linking page
    and the newly linked research URL.
    """
    if not before or set(before) == {"0"}:
        return set()

    try:
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0", before, "HEAD", "--", "index.html", "ratings.html"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        return set()

    linked: set[str] = set()
    pattern = re.compile(r'href=["\\\']/?([^"\\\']+\\.html)["\\\']')

    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        for match in pattern.finditer(line):
            path = match.group(1)
            if _is_root_html(path) and (ROOT / path).exists():
                linked.add(path)

    return linked


def changed_urls(before: str | None, force_all: bool) -> list[str]:
    changed, removed_html = git_changed(before)

    if force_all or bool(changed & SETUP_FILES):
        return all_current_urls()

    urls: set[str] = set()

    for path in changed:
        if _is_root_html(path):
            urls.add(url_for_html(path))

    # A research page may have been created in an earlier commit whose QA failed.
    # If the current commit adds that page to the catalog/homepage, submit it now.
    for path in newly_linked_html(before):
        urls.add(url_for_html(path))

    # Submit deleted / renamed-away pages too. IndexNow can report removed URLs;
    # the public URL should then return 404/410 or redirect as appropriate.
    for path in removed_html:
        urls.add(url_for_html(path))

    return sorted(urls)


def wait_for_key(max_attempts: int = 18, delay: int = 10) -> None:
    """Wait until GitHub Pages serves the verification key."""
    for attempt in range(1, max_attempts + 1):
        try:
            req = request.Request(KEY_LOCATION, headers={"User-Agent": "IndexResearch-IndexNow/1.0"})
            with request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8").strip()
                if resp.status == 200 and body == KEY:
                    print(f"IndexNow key is publicly reachable: {KEY_LOCATION}")
                    return
        except Exception as exc:
            print(f"Key check {attempt}/{max_attempts}: {exc}")

        if attempt < max_attempts:
            time.sleep(delay)

    raise SystemExit(f"IndexNow key file is not publicly reachable after waiting: {KEY_LOCATION}")


def post_indexnow(urls: list[str]) -> int:
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            req = request.Request(
                ENDPOINT,
                data=data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "IndexResearch-IndexNow/1.0",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=30) as resp:
                code = resp.status
                body = resp.read().decode("utf-8", errors="replace").strip()
                print(f"IndexNow response: HTTP {code} {body}".rstrip())
                if code in (200, 202):
                    return code
                raise RuntimeError(f"Unexpected IndexNow HTTP {code}: {body}")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()
            print(f"IndexNow HTTP error {exc.code}: {body}")
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except Exception as exc:
            print(f"IndexNow attempt {attempt}/3 failed: {exc}")
            last_error = exc

        if attempt < 3:
            time.sleep(10 * attempt)

    raise SystemExit(f"IndexNow submission failed after retries: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", default="", help="Previous Git SHA from the push event.")
    parser.add_argument("--all", action="store_true", help="Submit all current root HTML pages.")
    args = parser.parse_args()

    urls = changed_urls(args.before or None, args.all)
    if not urls:
        print("IndexNow: no changed root HTML URLs to submit.")
        return

    if len(urls) > 10000:
        raise SystemExit("IndexNow urlList exceeds the 10,000 URL protocol limit.")

    print(f"IndexNow: preparing {len(urls)} URL(s):")
    for url in urls:
        print(f"  {url}")

    wait_for_key()
    code = post_indexnow(urls)
    print(f"IndexNow: submitted {len(urls)} URL(s), HTTP {code}.")


if __name__ == "__main__":
    main()

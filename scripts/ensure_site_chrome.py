#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import hashlib
import re

from research_topics import render_topic_navigation

ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "assets" / "style.css"

PARTIALS = {
    "ru": (
        ROOT / "templates" / "partials" / "site-header.html",
        ROOT / "templates" / "partials" / "site-footer.html",
    ),
    "en": (
        ROOT / "templates" / "partials" / "site-header-en.html",
        ROOT / "templates" / "partials" / "site-footer-en.html",
    ),
    "cn": (
        ROOT / "templates" / "partials" / "site-header-cn.html",
        ROOT / "templates" / "partials" / "site-footer-cn.html",
    ),
}

HEADER_START = "<!-- SITE_HEADER_START -->"
HEADER_END = "<!-- SITE_HEADER_END -->"
FOOTER_START = "<!-- SITE_FOOTER_START -->"
FOOTER_END = "<!-- SITE_FOOTER_END -->"

HEADER_BLOCK_RE = re.compile(rf"{re.escape(HEADER_START)}[\s\S]*?{re.escape(HEADER_END)}")
FOOTER_BLOCK_RE = re.compile(rf"{re.escape(FOOTER_START)}[\s\S]*?{re.escape(FOOTER_END)}")
LEGACY_HEADER_RE = re.compile(r'<header class="top">[\s\S]*?</header>', re.I)
LEGACY_FOOTER_RE = re.compile(r'<footer>[\s\S]*?</footer>', re.I)
STYLE_RE = re.compile(r'/?assets/style\.css(?:\?v=[^"\']*)?')
HTML_LANG_RE = re.compile(r'<html\b[^>]*\blang=["\']([^"\']+)["\']', re.I)
LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
ATTR_RE = re.compile(
    r'''([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>]+))''',
    re.S,
)


def attrs(tag: str) -> dict[str, str]:
    result = {}
    for match in ATTR_RE.finditer(tag):
        result[match.group(1).lower()] = next(
            (value for value in (match.group(2), match.group(3), match.group(4)) if value is not None),
            "",
        )
    return result


def page_language(text: str) -> str:
    match = HTML_LANG_RE.search(text)
    if match:
        value = match.group(1).lower()
        if value.startswith("en"):
            return "en"
        if value.startswith("zh"):
            return "cn"
    return "ru"


def hreflang_href(text: str, code: str) -> str | None:
    for tag in LINK_TAG_RE.findall(text):
        values = attrs(tag)
        rels = {item.lower() for item in values.get("rel", "").split()}
        if "alternate" in rels and values.get("hreflang", "").lower() == code.lower():
            return values.get("href") or None
    return None


def local_href(url: str | None, fallback: str) -> str:
    if not url:
        return fallback
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {"indexresearch.ru", "www.indexresearch.ru"}:
            return fallback
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if parsed.fragment:
            path += "#" + parsed.fragment
        return path
    return url if url.startswith("/") else fallback


def replace_lang_href(fragment: str, lang_class: str, href: str) -> str:
    pattern = re.compile(
        rf'(<a\b[^>]*\bclass=["\'][^"\']*\b{re.escape(lang_class)}\b[^"\']*["\'][^>]*\bhref=["\'])[^"\']*(["\'])',
        re.I,
    )
    return pattern.sub(lambda match: match.group(1) + href + match.group(2), fragment)


def render_chrome(text: str) -> tuple[str, str]:
    lang = page_language(text)
    header_path, footer_path = PARTIALS[lang]
    header = header_path.read_text(encoding="utf-8").strip()
    footer = footer_path.read_text(encoding="utf-8").strip()

    topics_desktop, topics_mobile = render_topic_navigation(lang)
    header = header.replace("{{TOPICS_DESKTOP}}", topics_desktop)
    header = header.replace("{{TOPICS_MOBILE}}", topics_mobile)
    if "{{TOPICS_" in header:
        raise SystemExit(f"Unresolved topic navigation placeholder in {header_path.relative_to(ROOT)}")

    ru_href = local_href(hreflang_href(text, "ru"), "/")
    en_href = local_href(hreflang_href(text, "en"), "/en/methodology.html")
    cn_href = local_href(hreflang_href(text, "zh-CN"), "/cn/")

    for css_class, href in (("lang-ru", ru_href), ("lang-en", en_href), ("lang-cn", cn_href)):
        header = replace_lang_href(header, css_class, href)
        footer = replace_lang_href(footer, css_class, href)

    return header, footer


def ensure_no_translate(text: str) -> str:
    html_match = re.search(r'<html\b[^>]*>', text, re.I)
    if not html_match:
        raise SystemExit("HTML document is missing <html> tag")

    html_tag = html_match.group(0)
    if re.search(r'\btranslate\s*=', html_tag, re.I):
        html_tag = re.sub(
            r'\s+translate\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
            ' translate="no"',
            html_tag,
            count=1,
            flags=re.I,
        )
    else:
        html_tag = html_tag[:-1] + ' translate="no">'
    text = text[:html_match.start()] + html_tag + text[html_match.end():]

    google_meta_re = re.compile(
        r'<meta\b(?=[^>]*\bname\s*=\s*["\']google["\'])[^>]*>',
        re.I,
    )
    text = google_meta_re.sub("", text)
    google_meta = '<meta name="google" content="notranslate">'
    head_match = re.search(r'<head\b[^>]*>', text, re.I)
    if not head_match:
        raise SystemExit("HTML document is missing <head> tag")
    text = text[:head_match.end()] + "\n" + google_meta + text[head_match.end():]

    return text

def sync_file(path: Path, style_version: str) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    text = ensure_no_translate(text)
    header, footer = render_chrome(text)
    header_block = f"{HEADER_START}\n{header}\n{HEADER_END}"
    footer_block = f"{FOOTER_START}\n{footer}\n{FOOTER_END}"
    rel = path.relative_to(ROOT).as_posix()

    if "{{SITE_HEADER}}" in text:
        text = text.replace("{{SITE_HEADER}}", header_block, 1)
    elif HEADER_START in text or HEADER_END in text:
        text, count = HEADER_BLOCK_RE.subn(lambda _: header_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{rel}: invalid shared header markers")
    else:
        text, count = LEGACY_HEADER_RE.subn(lambda _: header_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{rel}: canonical header not found")

    if "{{SITE_FOOTER}}" in text:
        text = text.replace("{{SITE_FOOTER}}", footer_block, 1)
    elif FOOTER_START in text or FOOTER_END in text:
        text, count = FOOTER_BLOCK_RE.subn(lambda _: footer_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{rel}: invalid shared footer markers")
    else:
        text, count = LEGACY_FOOTER_RE.subn(lambda _: footer_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{rel}: canonical footer not found")

    if text.count(HEADER_START) != 1 or text.count(HEADER_END) != 1:
        raise SystemExit(f"{rel}: shared header must appear exactly once")
    if text.count(FOOTER_START) != 1 or text.count(FOOTER_END) != 1:
        raise SystemExit(f"{rel}: shared footer must appear exactly once")

    text = STYLE_RE.sub(f"/assets/style.css?v={style_version}", text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    for lang, pair in PARTIALS.items():
        for path in pair:
            if not path.exists():
                raise SystemExit(f"Missing {lang} chrome partial: {path.relative_to(ROOT)}")
    if not STYLE_PATH.exists():
        raise SystemExit("Missing assets/style.css")

    style_version = hashlib.sha256(STYLE_PATH.read_bytes()).hexdigest()[:12]
    changed = []

    for path in sorted(ROOT.rglob("*.html")):
        if any(part in {"templates", ".git", ".github"} for part in path.parts):
            continue
        if sync_file(path, style_version):
            changed.append(path.relative_to(ROOT).as_posix())

    print(f"Shared IndexResearch RU/EN/CN chrome synchronized; CSS version {style_version}.")
    if changed:
        print("Updated:", ", ".join(changed))
    else:
        print("No HTML changes required.")


if __name__ == "__main__":
    main()

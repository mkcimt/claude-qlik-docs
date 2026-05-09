"""MS0 spike: fetch one Talend doc page and convert to clean Markdown with frontmatter.

Usage:
    uv run python spike/extract_one_page.py <url>
    uv run python spike/extract_one_page.py  # uses default sample URL

Validates the SSR + httpx + BeautifulSoup + markdownify path before MS1.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

USER_AGENT = "qlik-docs-skill-builder/0.1 (personal use; spike)"
DEFAULT_URL = (
    "https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-04/"
    "what-is-talend-studio"
)

# URL pattern: /talend/en-US/<product-slug>/<version>/<page-slug>
URL_RE = re.compile(
    r"^https?://help\.qlik\.com/talend/(?P<locale>[a-z]{2}-[A-Z]{2})/"
    r"(?P<product>[^/]+)/(?P<version>[^/]+)/(?P<slug>[^/?#]+)/?$"
)


def parse_url(url: str) -> dict[str, str]:
    m = URL_RE.match(url)
    if not m:
        raise ValueError(f"URL does not match expected pattern: {url}")
    parts = m.groupdict()
    # Major version: "Cloud" stays "Cloud"; "8.0-R2026-04" -> major "8.0", r_code "R2026-04"
    v = parts["version"]
    if v.lower() == "cloud":
        parts["major_version"] = "Cloud"
        parts["r_code"] = ""
    else:
        rm = re.match(r"^(\d+\.\d+)(?:-(R\d{4}-\d{2}.*))?$", v)
        parts["major_version"] = rm.group(1) if rm else v
        parts["r_code"] = rm.group(2) or "" if rm else ""
    return parts


def fetch(url: str) -> str:
    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=30.0,
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def extract_main(html: str) -> tuple[str, str, list[str], list[str]]:
    """Returns (title, content_html, breadcrumbs, version_constraints)."""
    soup = BeautifulSoup(html, "lxml")

    # Strip global junk before isolating main
    for sel in ["script", "style", "noscript", "iframe", "svg"]:
        for el in soup.select(sel):
            el.decompose()

    # Main content: <main id="main"> contains <div id="topicContent"> on Talend pages.
    main = soup.select_one("div#topicContent") or soup.select_one("main#main")
    if main is None:
        raise RuntimeError("Could not locate main content container")

    # Strip in-page chrome: nav, footer, version-selector remnants, feedback widgets
    junk_selectors = [
        "nav",
        "footer",
        "header",
        ".feedback",
        ".rating",
        "[class*=version-selector]",
        "[class*=breadcrumb]",
        "[class*=footer]",
        "[id*=feedback]",
        ".did-this-help",
        ".doc-feedback",
        "button",
    ]
    for sel in junk_selectors:
        for el in main.select(sel):
            el.decompose()

    # Title: first h1 inside main, fallback to <title>
    h1 = main.find("h1")
    title = (
        h1.get_text(strip=True)
        if h1
        else (soup.title.string.strip() if soup.title and soup.title.string else "")
    )

    # Breadcrumbs: from outer document, before stripping
    bc_soup = BeautifulSoup(html, "lxml")
    breadcrumbs: list[str] = []
    bc = bc_soup.select_one("[class*=breadcrumb]")
    if bc:
        breadcrumbs = [
            t.strip() for t in bc.stripped_strings if t.strip() and t.strip() != ">"
        ]

    # Version constraints: heuristically scan for "available since", "applies to"
    text = main.get_text(" ", strip=True)
    version_constraints = []
    for pat in [
        r"available (?:as of|since|in)\s+(?:Talend\s+)?[A-Za-z0-9.\- ]+",
        r"applies (?:only )?to\s+(?:version\s+)?[0-9.\-RxX ]+",
        r"deprecated (?:as of|since|in)\s+[0-9.\-RxX ]+",
    ]:
        version_constraints += re.findall(pat, text, flags=re.IGNORECASE)
    version_constraints = list(dict.fromkeys(version_constraints))[:5]

    return title, str(main), breadcrumbs, version_constraints


def html_to_markdown(content_html: str) -> str:
    md = markdownify(content_html, heading_style="ATX", bullets="-", strip=["a"])
    # markdownify "strip=['a']" preserves link text but removes <a>; we keep links by default? Actually we want link text only when href is internal anchor garbage. For now keep links.
    md = markdownify(content_html, heading_style="ATX", bullets="-")
    # Collapse 3+ blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md


def build_frontmatter(url: str, title: str, breadcrumbs, version_constraints) -> str:
    parts = parse_url(url)
    fm = {
        "source_url": url,
        "title": title,
        "product": parts["product"],
        "version": parts["version"],
        "major_version": parts["major_version"],
        "r_code": parts["r_code"],
        "locale": parts["locale"],
        "slug": parts["slug"],
        "breadcrumbs": breadcrumbs,
        "version_constraints": version_constraints,
        "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    import yaml

    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True) + "---\n\n"


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    html = fetch(url)
    sha = hashlib.sha256(html.encode()).hexdigest()[:12]
    title, content_html, breadcrumbs, version_constraints = extract_main(html)
    md_body = html_to_markdown(content_html)
    fm = build_frontmatter(url, title, breadcrumbs, version_constraints)
    # add content_sha to frontmatter (post-build, hacky but spike)
    fm = fm.replace("crawled_at:", f"content_sha: {sha}\ncrawled_at:")
    out_dir = Path("spike/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = parse_url(url)
    out_path = out_dir / f"{parts['product']}__{parts['version']}__{parts['slug']}.md"
    out_path.write_text(fm + md_body, encoding="utf-8")
    stats = {
        "url": url,
        "title": title,
        "out_file": str(out_path),
        "raw_html_bytes": len(html),
        "markdown_bytes": len(md_body),
        "compression_ratio": round(len(md_body) / max(len(html), 1), 3),
        "breadcrumbs": breadcrumbs,
        "version_constraints": version_constraints,
        "content_sha12": sha,
    }
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

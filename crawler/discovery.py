"""Discovery: resolve sitemap names to a list of page URLs.

- Reads the Talend sitemap-index to discover the latest Studio R-code.
- Fetches each sub-sitemap and yields page URLs grouped by logical product.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

from crawler.config import (
    LOCALE,
    PRODUCT_SITEMAPS,
    SITEMAP_URL_TEMPLATE,
    TALEND_SITEMAP_INDEX,
    USER_AGENT,
)

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
R_CODE_RE = re.compile(r"^studio-user-guide_(8\.0-R\d{4}-\d{2})(?:-and-earlier)?$")


@dataclass(frozen=True)
class SitemapRef:
    product: str  # logical product name (key of PRODUCT_SITEMAPS)
    name: str  # resolved sitemap name (no R-code placeholders)
    url: str


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30.0
    )


def fetch_sitemap_index() -> list[str]:
    """Returns all sub-sitemap names (without `.xml` and locale suffix) listed in the
    Talend sitemap index. Used only to resolve the latest Studio R-code."""
    with _client() as c:
        r = c.get(TALEND_SITEMAP_INDEX)
        r.raise_for_status()
    root = ET.fromstring(r.content)
    names: list[str] = []
    for sm in root.findall("sm:sitemap/sm:loc", NS):
        url = (sm.text or "").strip()
        # extract sitemap_<name>_<locale>.xml
        m = re.search(r"/sitemap_(.+?)_([a-z]{2}-[A-Z]{2})\.xml$", url)
        if m and m.group(2) == LOCALE:
            names.append(m.group(1))
    return names


def resolve_latest_studio_r_code(index_names: list[str]) -> str:
    """Returns the highest-sorting R-code from sitemap names like `studio-user-guide_8.0-R2026-04`."""
    candidates: list[str] = []
    for n in index_names:
        m = R_CODE_RE.match(n)
        if m:
            candidates.append(m.group(1))
    if not candidates:
        raise RuntimeError("No studio-user-guide sitemap found in index")
    return sorted(candidates)[-1]  # 8.0-R2026-04 sorts last among R-codes


def resolve_sitemap_refs() -> list[SitemapRef]:
    index_names = fetch_sitemap_index()
    latest_r = resolve_latest_studio_r_code(index_names)
    available = set(index_names)
    refs: list[SitemapRef] = []
    skipped: list[str] = []
    for product, names in PRODUCT_SITEMAPS.items():
        for n in names:
            resolved = n.replace("<latest-r>", latest_r)
            if resolved not in available:
                skipped.append(f"{product}/{resolved}")
                continue
            url = SITEMAP_URL_TEMPLATE.format(name=resolved, locale=LOCALE)
            refs.append(SitemapRef(product=product, name=resolved, url=url))
    if skipped:
        print(f"[discovery] skipped (not in index): {skipped}")
    return refs


def fetch_urls(ref: SitemapRef) -> list[str]:
    with _client() as c:
        r = c.get(ref.url)
        r.raise_for_status()
    root = ET.fromstring(r.content)
    return [
        (loc.text or "").strip()
        for loc in root.findall("sm:url/sm:loc", NS)
        if (loc.text or "").strip()
    ]


if __name__ == "__main__":
    refs = resolve_sitemap_refs()
    total = 0
    for ref in refs:
        urls = fetch_urls(ref)
        total += len(urls)
        print(f"{len(urls):5d}  {ref.product:18s}  {ref.name}")
    print(f"------\n{total:5d}  TOTAL across {len(refs)} sitemaps")

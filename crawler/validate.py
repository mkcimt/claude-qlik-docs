"""Post-crawl QA: manifest stats + sanity checks on raw output.

Run: uv run python -m crawler.validate
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "skill-output" / "qlik-talend" / "meta" / "manifest.json"
RAW = ROOT / "skill-output" / "qlik-talend" / "raw"


def load_frontmatter(p: Path) -> dict:
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    return yaml.safe_load(text[4:end]) or {}


def main() -> int:
    if not MANIFEST.exists():
        print("manifest.json not found — run the crawler first.", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text())
    pages = manifest.get("pages", {})
    stats = manifest.get("stats", {})

    print(f"\n=== Manifest summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n=== URL → output coverage ===")
    expected = len(pages)
    actual_files = list(RAW.rglob("*.md"))
    print(f"  manifest pages: {expected}")
    print(f"  files on disk:  {len(actual_files)}")

    print(f"\n=== Per product_group ===")
    by_group: dict[str, int] = Counter()
    by_status: dict[int, int] = Counter()
    for url, meta in pages.items():
        by_group[meta.get("product_group", "?")] += 1
        if meta.get("status"):
            by_status[meta["status"]] += 1
    for g, n in sorted(by_group.items()):
        print(f"  {g:18s} {n:5d}")

    if by_status:
        print(f"\n=== Non-2xx status ===")
        for s, n in sorted(by_status.items()):
            print(f"  HTTP {s}: {n}")

    print(f"\n=== Frontmatter sanity (sample 50 files) ===")
    issues: list[str] = []
    sample = actual_files[:50]
    required = {
        "source_url",
        "title",
        "product_group",
        "version",
        "major_version",
        "slug",
        "content_sha",
    }
    for f in sample:
        fm = load_frontmatter(f)
        missing = required - set(fm.keys())
        if missing:
            issues.append(f"  {f.relative_to(ROOT)}: missing {sorted(missing)}")
        if not fm.get("title"):
            issues.append(f"  {f.relative_to(ROOT)}: empty title")
    if issues:
        print(f"  {len(issues)} issues:")
        for i in issues[:10]:
            print(i)
    else:
        print("  ok")

    print(f"\n=== Major-version distribution ===")
    by_major: dict[str, int] = Counter()
    for f in actual_files:
        fm = load_frontmatter(f)
        by_major[str(fm.get("major_version", "?"))] += 1
    for v, n in sorted(by_major.items()):
        print(f"  {v}: {n}")

    print(f"\n=== Markdown-size distribution ===")
    sizes = sorted(f.stat().st_size for f in actual_files)
    if sizes:
        n = len(sizes)
        print(f"  count: {n}")
        print(f"  min:   {sizes[0]} bytes")
        print(f"  p50:   {sizes[n // 2]} bytes")
        print(f"  p90:   {sizes[int(n * 0.9)]} bytes")
        print(f"  max:   {sizes[-1]} bytes")
        print(f"  total: {sum(sizes) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

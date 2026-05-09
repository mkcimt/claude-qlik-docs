"""Validate citations in distilled topic files.

Each topic.md ends with a ## Citations table mapping `[^P-N]` → raw file path
+ source URL. We verify:
- Every `[^P-N]` anchor used in the body has a row in the citations table.
- Every raw file path referenced exists on disk.
- Every source URL appears in the manifest.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = ROOT / "skill-output" / "qlik-talend" / "topics"
MANIFEST = ROOT / "skill-output" / "qlik-talend" / "meta" / "manifest.json"

ANCHOR_RE = re.compile(r"\[\^(P-\d+)\]")
CITATION_ROW_RE = re.compile(r"\|\s*`\[\^(P-\d+)\]`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")


def main() -> int:
    if not MANIFEST.exists():
        print("manifest.json not found", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text())
    valid_urls = set(manifest.get("pages", {}).keys())

    n_topics = 0
    n_anchors = 0
    issues: list[str] = []
    for topic_file in TOPICS_DIR.rglob("*.md"):
        n_topics += 1
        text = topic_file.read_text(encoding="utf-8")
        # split body / citations
        if "## Citations" not in text:
            issues.append(f"{topic_file.relative_to(ROOT)}: no Citations section")
            continue
        body, _, citations_section = text.partition("## Citations")

        body_anchors = set(ANCHOR_RE.findall(body))
        citation_rows = CITATION_ROW_RE.findall(citations_section)
        cited_anchors = {a for a, _, _ in citation_rows}

        unmatched = body_anchors - cited_anchors
        if unmatched:
            issues.append(
                f"{topic_file.relative_to(ROOT)}: anchors used in body but not in table: {sorted(unmatched)}"
            )

        for anchor, raw_path, url in citation_rows:
            n_anchors += 1
            url = url.strip()
            full = ROOT / raw_path
            if not full.exists():
                issues.append(
                    f"{topic_file.relative_to(ROOT)}: [^{anchor}] raw file missing: {raw_path}"
                )
            if url not in valid_urls:
                issues.append(
                    f"{topic_file.relative_to(ROOT)}: [^{anchor}] URL not in manifest: {url}"
                )

    print(f"validated {n_topics} topic files, {n_anchors} citation anchors")
    if issues:
        print(f"\n{len(issues)} issues:")
        for i in issues[:30]:
            print(f"  {i}")
        if len(issues) > 30:
            print(f"  ... and {len(issues) - 30} more")
        return 2
    print("all citations valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

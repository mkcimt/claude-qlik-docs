"""Build distilled topic.md files from raw pages, mechanically (no LLM).

For each topic in topic_map.yaml, produce a topic file with:
- TL;DR per page (= first sentence after H1)
- Procedure outline (H2/H3 list)
- Notes/Restrictions blocks (literal extraction)
- Cross-link to raw file path + canonical URL

This is hybrid: structured summary + raw-file pointer. Citation-perfect by
construction (no paraphrasing, no LLM).

Run: uv run python -m distill.build_topics
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOPIC_MAP = ROOT / "topic_map.yaml"
SKILL_OUT = ROOT / "skill-output" / "qlik-talend"
TOPICS_DIR = SKILL_OUT / "topics"

NOTE_PATTERN = re.compile(
    r"(?:^|\n)\s*Information note(?P<kind>Note|Restriction|Important|Tip|Warning|Caution)?\s*[:\-]?\s*(?P<body>[^\n]+)",
    flags=re.IGNORECASE,
)
H2_H3_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", flags=re.MULTILINE)


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fm = yaml.safe_load(text[4:end]) or {}
    return fm, text[end + 5 :]


def extract_tldr(body: str) -> str:
    """First non-empty paragraph after the H1."""
    # strip leading H1
    lines = body.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    # skip blank lines
    paragraph: list[str] = []
    started = False
    for line in lines:
        if line.strip():
            started = True
            paragraph.append(line.strip())
            # paragraph ends on empty line OR heading start
        elif started:
            break
        if started and (line.startswith("#") or line.startswith("|")):
            paragraph.pop()  # this was a heading; not a TL;DR
            break
    text = " ".join(paragraph)
    text = re.sub(r"\s+", " ", text).strip()
    # cap to ~280 chars at sentence boundary
    if len(text) > 280:
        cut = text[:280].rsplit(". ", 1)[0]
        if len(cut) >= 100:
            text = cut + "."
        else:
            text = text[:280].rstrip() + "…"
    return text


def extract_outline(body: str) -> list[str]:
    """Return ordered H2/H3 headings, deduped, max 12."""
    hits = [
        f"{'  ' * (len(level) - 2)}- {title}"
        for level, title in H2_H3_RE.findall(body)
    ]
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h in seen:
            continue
        seen.add(h)
        out.append(h)
        if len(out) >= 12:
            break
    return out


def extract_notes(body: str) -> list[str]:
    """Return Note:/Restriction:/Important: blocks (first line each), max 6."""
    out: list[str] = []
    for m in NOTE_PATTERN.finditer(body):
        kind = (m.group("kind") or "Note").strip()
        body_line = re.sub(r"\s+", " ", m.group("body")).strip()
        if not body_line:
            continue
        # drop trailing "see Foo." references that lose meaning
        out.append(f"**{kind}:** {body_line}")
        if len(out) >= 6:
            break
    return out


def render_topic(
    *, group: str, guide: str, version: str, topic: dict
) -> str:
    page_md_blocks: list[str] = []
    citations: list[tuple[str, str, str]] = []  # (anchor, raw_path, url)
    raw_total = 0
    for i, page in enumerate(topic["pages"], 1):
        out_path = ROOT / page["out_path"]
        if not out_path.exists():
            continue
        text = out_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        raw_total += len(body)
        anchor = f"P-{i}"
        tldr = extract_tldr(body) or "(no summary available)"
        outline = extract_outline(body)
        notes = extract_notes(body)
        version_constraints = fm.get("version_constraints") or []
        title = fm.get("title", page.get("title", page["slug"]))

        block_lines = [
            f"### {i}. {title} [^{anchor}]",
            "",
            f"_TL;DR:_ {tldr}",
        ]
        if outline:
            block_lines += ["", "**Procedure outline:**", *outline]
        if notes:
            block_lines += ["", "**Notes / restrictions:**", *[f"- {n}" for n in notes]]
        if version_constraints:
            block_lines += [
                "",
                "**Version constraints:**",
                *[f"- {v}" for v in version_constraints[:4]],
            ]
        block_lines.append("")
        page_md_blocks.append("\n".join(block_lines))
        citations.append(
            (anchor, str(out_path.relative_to(ROOT)), page["url"])
        )

    # Header / overview
    topic_title = topic["id"].replace("-", " ").title()
    n = len(citations)
    header = [
        "---",
        yaml.safe_dump(
            {
                "topic_id": topic["id"],
                "product_group": group,
                "guide": guide,
                "version": version,
                "page_count": n,
                "raw_bytes_aggregated": raw_total,
            },
            sort_keys=False,
            allow_unicode=True,
        ).rstrip(),
        "---",
        "",
        f"# {topic_title} — {guide}",
        "",
        f"_Guide:_ `{guide}`  ·  _Version:_ `{version}`  ·  _Pages:_ {n}",
        "",
        "## Pages",
        "",
        "| # | Title | Slug |",
        "|---:|-------|------|",
    ]
    for i, page in enumerate(topic["pages"], 1):
        title = page.get("title") or page["slug"]
        # markdown-escape pipes
        title = title.replace("|", r"\|")
        header.append(f"| {i} | {title} | `{page['slug']}` |")
    header.append("")
    header.append("## Per-page summaries")
    header.append("")

    citation_table = ["", "## Citations", "", "| Anchor | Raw file | Source URL |", "|--------|----------|-----------|"]
    for anchor, raw_path, url in citations:
        citation_table.append(f"| `[^{anchor}]` | `{raw_path}` | {url} |")
    citation_table.append("")

    return "\n".join(header) + "\n".join(page_md_blocks) + "\n".join(citation_table)


def safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)[:120]


def main() -> int:
    if not TOPIC_MAP.exists():
        print("topic_map.yaml not found — run distill.cluster first", file=sys.stderr)
        return 1
    tm = yaml.safe_load(TOPIC_MAP.read_text())
    n_topics = 0
    n_pages = 0
    for guide_block in tm["guides"]:
        group = guide_block["product_group"]
        guide = guide_block["product_slug"]
        version = guide_block["version"]
        out_dir = TOPICS_DIR / group / safe_id(guide) / safe_id(version)
        out_dir.mkdir(parents=True, exist_ok=True)
        for topic in guide_block["topics"]:
            md = render_topic(
                group=group, guide=guide, version=version, topic=topic
            )
            (out_dir / f"{safe_id(topic['id'])}.md").write_text(md, encoding="utf-8")
            n_topics += 1
            n_pages += len(topic["pages"])
    print(f"[build_topics] wrote {n_topics} topic files covering {n_pages} pages")
    print(f"[build_topics] output dir: {TOPICS_DIR.relative_to(ROOT)}")
    # Size summary
    sizes = sorted(p.stat().st_size for p in TOPICS_DIR.rglob("*.md"))
    if sizes:
        n = len(sizes)
        print(
            f"[build_topics] topic-file sizes: min={sizes[0]}  p50={sizes[n // 2]}  "
            f"p90={sizes[int(n * 0.9)]}  max={sizes[-1]}  total={sum(sizes) // 1024} KB"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

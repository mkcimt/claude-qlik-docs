"""Build a self-contained skill bundle for upload to claude.ai (Claude Chat).

Differences from the local Claude Code skill:
- No `raw/` directory (Chat has no filesystem access).
- **Topics consolidated per guide** so the file count stays under claude.ai's
  200-file Skill-upload limit. Each topic becomes an anchored section
  (`<a id="topic-<id>"></a>`) inside one combined guide file.
- Each topic's Citations table drops the local "Raw file" column; only the
  canonical source URL remains. Claude in Chat can WebFetch when exact
  wording is needed.
- Sub-indexes are rebuilt to link to the anchored topic sections inside
  the consolidated guide files.
- SKILL.md is rewritten to point at URLs and consolidated guide files.

Output:
- dist/qlik-talend-chat/   (the bundle directory)
- dist/qlik-talend-chat.zip (zipped, ready to upload)

Run: uv run python -m package.build_chat_bundle
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skill-output" / "qlik-talend"
TOPIC_MAP = ROOT / "topic_map.yaml"
DIST = ROOT / "dist"
BUNDLE_DIR = DIST / "qlik-talend-chat"
BUNDLE_ZIP = DIST / "qlik-talend-chat.zip"

CITATION_HEADER_RE = re.compile(r"\|\s*Anchor\s*\|\s*Raw file\s*\|\s*Source URL\s*\|")
CITATION_SEPARATOR_RE = re.compile(r"\|-+\|-+\|-+\|")
CITATION_ROW_RE = re.compile(
    r"\|\s*(`\[\^P-\d+\]`)\s*\|\s*`[^`]+`\s*\|\s*([^|]+?)\s*\|"
)
H1_RE = re.compile(r"^#\s+", flags=re.MULTILINE)


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    return yaml.safe_load(text[4:end]) or {}, text[end + 5 :]


def transform_topic_body(text: str) -> str:
    """Strip frontmatter, drop Raw-file column, demote H1 to H2 (so the
    consolidated guide file's structure is: H1 = guide, H2 = topic)."""
    _, body = split_frontmatter(text)
    body = body.lstrip()
    out_lines: list[str] = []
    for line in body.splitlines():
        if CITATION_HEADER_RE.search(line):
            out_lines.append("| Anchor | Source URL |")
            continue
        if CITATION_SEPARATOR_RE.search(line):
            out_lines.append("|--------|-----------|")
            continue
        m = CITATION_ROW_RE.match(line)
        if m:
            anchor, url = m.group(1), m.group(2).strip()
            out_lines.append(f"| {anchor} | {url} |")
            continue
        out_lines.append(line)
    body = "\n".join(out_lines)
    # Demote every H1/H2/H3 by one level so the topic body fits under a
    # guide-level H1 and topic-level H2 (added by the consolidator).
    demoted: list[str] = []
    for line in body.splitlines():
        if line.startswith("### "):
            demoted.append("#### " + line[4:])
        elif line.startswith("## "):
            demoted.append("### " + line[3:])
        elif line.startswith("# "):
            demoted.append("## " + line[2:])
        else:
            demoted.append(line)
    return "\n".join(demoted).rstrip() + "\n"


def safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)[:120]


def consolidate_guide(
    *, group: str, guide: str, version: str, topic_blocks: list[dict]
) -> tuple[str, list[dict]]:
    """Build one combined markdown for a single guide+version.

    Returns (markdown_text, [{topic_id, blurb, anchor}, ...]).
    """
    src_topic_dir = SRC / "topics" / group / safe_id(guide) / safe_id(version)
    out_lines: list[str] = [
        f"# {guide} — {version}",
        "",
        f"_Group:_ `{group}`  ·  _Version:_ `{version}`  ·  "
        f"_Topics:_ {len(topic_blocks)}",
        "",
        "## Table of contents",
        "",
    ]
    topic_summaries: list[dict] = []
    body_blocks: list[str] = []

    for tb in topic_blocks:
        topic_id = tb["id"]
        anchor = f"topic-{safe_id(topic_id)}"
        topic_file = src_topic_dir / f"{safe_id(topic_id)}.md"
        if not topic_file.exists():
            continue
        text = topic_file.read_text(encoding="utf-8")
        # blurb = first TL;DR
        m = re.search(r"_TL;DR:_\s+(.+?)\n", text)
        blurb = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        if len(blurb) > 200:
            blurb = blurb[:200] + "…"
        topic_summaries.append(
            {"topic_id": topic_id, "blurb": blurb, "anchor": anchor, "pages": len(tb["pages"])}
        )
        out_lines.append(f"- [{topic_id}](#{anchor}) ({len(tb['pages'])} pages) — {blurb}")
        body = transform_topic_body(text)
        body_blocks.append(
            f'\n<a id="{anchor}"></a>\n\n## Topic: `{topic_id}`\n\n{body}'
        )

    return "\n".join(out_lines) + "\n" + "\n".join(body_blocks), topic_summaries


CHAT_SKILL_MD = """---
name: qlik-talend
description: Authoritative reference for Qlik Talend (Studio 8.0, Talend Management Console, Remote Engine, SDLC/CI-CD, installation/migration). Use when answering questions about Talend Studio jobs/components, TMC promotions/schedules/users, Remote Engine setup/configuration, Dynamic Engine, hybrid installations, Studio→TMC publishing, Git/CI-CD with Talend, or anything mentioning Talend on Qlik Cloud. Sourced from help.qlik.com/talend.
---

# Qlik Talend Documentation Skill (Chat edition)

## When to use this skill

Trigger on questions that mention Talend products or workflows:

- **Talend Studio**: jobs, joblets, routes, components (`tFooBar`), context variables, metadata, palette, projects, Git, build/export, publish to cloud, debug, MapReduce/Spark, ESB.
- **Talend Management Console (TMC)**: promotions, environments, workspaces, run profiles, schedules, plans, tasks, artifact repository, users/roles/tokens, audit logs, SSO.
- **Remote Engine / Dynamic Engine**: install (Linux & Windows), configure, pair with TMC, run jobs/pipelines, troubleshooting, upgrade, Gen2.
- **Installation / migration / upgrade**: Studio installer, TAC upgrade paths, hybrid deployments, JDK requirements, Tomcat upgrades.
- **SDLC / CI-CD with Talend**: development life-cycle, environment promotions, Git workflows, automation patterns.
- **Talend Cloud platform**: getting started, glossary, regions, account migration, Qlik-Talend integration.

If a question is *vaguely* Talend-related but really about a non-Talend product (Qlik Sense, QlikView, Replicate, Compose, NPrinting), do **not** rely on this skill — it does not contain those docs.

## Coverage scope

| Group | Versions | Pages |
|-------|---------|------:|
| studio | 8.0 (latest R-code at crawl) | ~1,068 |
| tmc | Cloud | ~328 |
| remote-engine | Cloud | ~324 |
| installation | Cloud + 8.0 | ~1,032 |
| sdlc-cicd | Cloud + 8.0 | ~68 |
| cloud-platform | Cloud | ~127 |

**Out of scope (do not assume coverage):** Components/connectors reference, Data Catalog, Data Quality, Data Stewardship, Data Preparation, ESB, API Designer, MDM, Data Inventory, all 7.x docs.

## How to look something up — progressive disclosure

This Chat-edition bundle has **no local raw files** and **topics are consolidated per guide** (one file per guide+version, with a Table of contents at the top and anchored sections per topic). Structure:

1. `index.md` — top-level navigation across the six product groups.
2. `index/<group>.md` — per-group topic listing with one-line blurbs and links to anchored topic sections in the consolidated guide files.
3. `topics/<group>/<guide>__<version>.md` — **one combined file per guide+version**, containing the guide's TOC plus all topics as anchored sections (`<a id="topic-<id>">`).

For a typical question, work outside-in:

1. **Read `index.md`** (~2 KB). Identify the **product group**.
2. **Read `index/<group>.md`** (~10–30 KB). Find the matching **topic** and its link → guide-file + anchor.
3. **Read the consolidated guide file** (`topics/<group>/<guide>__<version>.md`). Use `Read` with `offset`/`limit` to navigate to the topic section if the file is large — large guide files like Studio User Guide can be ~400 KB.
4. **Only if you need exact procedure text or verbatim quotes**, fetch the source URL from the topic's Citations table via WebFetch.

## Citation discipline

When you answer, **always cite**:
- The Qlik major version (`Cloud` or `8.0`) and, for Studio, the R-code (e.g. `8.0-R2026-04`).
- The source URL from the topic's Citations table.

Example: "In TMC (Cloud), promotion environments are configured under … [source: help.qlik.com/talend/en-US/management-console-user-guide/Cloud/manage-promotion]."

## Versioning gotchas

- Studio R-codes (`R2026-04`, etc.) bump monthly. The R-code in this bundle is whatever was latest at crawl time.
- Cloud docs are continuously updated; treat as "as of crawl date".
- 7.x is **not** included. If the user is on 7.x, say so explicitly and do not extrapolate.

## Anti-patterns

- Do NOT load all guide files at once — progressive disclosure means one group + one guide is enough for almost every answer.
- Do NOT answer "from memory" if the topic disagrees — the skill is the source of truth.
- Do NOT cite the topic file's TL;DR alone for safety-relevant answers (security, encryption, license, upgrade compatibility) — fetch the source URL and verify.
"""


GROUP_DESCRIPTIONS: dict[str, str] = {
    "studio": "Talend Studio (8.0) — job design, components, projects, Git, metadata, deployment.",
    "tmc": "Talend Management Console (Cloud) — promotions, schedules, users, tokens, environments, audit.",
    "remote-engine": "Talend Remote Engine (Cloud, Linux & Windows) + Dynamic Engine — install, configure, run.",
    "installation": "Studio + TMC + Engine installation, hybrid deployments, migration / upgrade (Cloud + 8.0).",
    "sdlc-cicd": "Software Development Life Cycle, CI/CD, Git, environments, promotions, operational mgmt.",
    "cloud-platform": "Talend Cloud platform basics — getting started, glossary, account, regions.",
}


def build_top_index(by_group: dict) -> str:
    n_topics = sum(
        len(g["topics"]) for guides in by_group.values() for g in guides
    )
    n_pages = sum(g["page_count"] for guides in by_group.values() for g in guides)
    n_guides = sum(len(guides) for guides in by_group.values())
    lines = [
        "# Qlik Talend Documentation — Skill Index (Chat edition)",
        "",
        "Distilled hybrid skill for Qlik Talend documentation, packaged for "
        "claude.ai. Topics are consolidated per guide+version into single "
        "files with anchored sections, to fit within Skill-upload file-count "
        "limits.",
        "",
        "## Product groups",
        "",
        "| Group | Description | Guides | Topics | Pages |",
        "|-------|-------------|-------:|-------:|------:|",
    ]
    for group in sorted(by_group):
        guides = by_group[group]
        gt = sum(len(g["topics"]) for g in guides)
        gp = sum(g["page_count"] for g in guides)
        desc = GROUP_DESCRIPTIONS.get(group, "")
        lines.append(
            f"| [`{group}`](index/{group}.md) | {desc} | {len(guides)} | {gt} | {gp} |"
        )
    lines += [
        "",
        f"**Total:** {len(by_group)} groups, {n_guides} guides, {n_topics} "
        f"topics, {n_pages} pages.",
        "",
        "## How to navigate",
        "",
        "1. Pick the product group that matches the user's question.",
        "2. Open `index/<group>.md` for the topic listing with anchored links.",
        "3. Open the consolidated guide file `topics/<group>/<guide>__<version>.md` and jump to the topic anchor.",
        "4. For exact wording or full detail, follow the canonical URL in the topic's Citations table (WebFetch).",
    ]
    return "\n".join(lines) + "\n"


def build_group_index(group: str, guides: list[dict], summaries_by_guide: dict) -> str:
    lines = [
        f"# {group} — Topic Index",
        "",
        GROUP_DESCRIPTIONS.get(group, ""),
        "",
    ]
    for guide_block in sorted(guides, key=lambda x: x["product_slug"]):
        guide = guide_block["product_slug"]
        version = guide_block["version"]
        guide_filename = f"{safe_id(guide)}__{safe_id(version)}.md"
        summaries = summaries_by_guide.get((guide, version), [])
        lines += [
            f"## {guide} (`{version}`) — {guide_block['page_count']} pages, "
            f"{len(guide_block['topics'])} topics",
            "",
            f"Combined guide file: [`topics/{group}/{guide_filename}`](../topics/{group}/{guide_filename})",
            "",
            "| Topic | Pages | Blurb |",
            "|-------|------:|-------|",
        ]
        for s in summaries:
            blurb = (s["blurb"] or "").replace("|", r"\|")
            link = f"../topics/{group}/{guide_filename}#{s['anchor']}"
            lines.append(
                f"| [`{s['topic_id']}`]({link}) | {s['pages']} | {blurb} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not SRC.exists() or not (SRC / "topics").exists():
        print(
            "skill-output/qlik-talend not built — run `make build` first",
            file=sys.stderr,
        )
        return 1
    if not TOPIC_MAP.exists():
        print("topic_map.yaml not found — run `make cluster` first", file=sys.stderr)
        return 1

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True)

    tm = yaml.safe_load(TOPIC_MAP.read_text())
    by_group: dict[str, list[dict]] = {}
    for g in tm["guides"]:
        by_group.setdefault(g["product_group"], []).append(g)

    # SKILL.md (chat edition)
    (BUNDLE_DIR / "SKILL.md").write_text(CHAT_SKILL_MD, encoding="utf-8")

    # Consolidated guide files + collect summaries for sub-indexes
    summaries_by_guide: dict[tuple[str, str], list[dict]] = {}
    n_guide_files = 0
    for group, guides in by_group.items():
        group_dir = BUNDLE_DIR / "topics" / group
        group_dir.mkdir(parents=True, exist_ok=True)
        for guide_block in guides:
            guide = guide_block["product_slug"]
            version = guide_block["version"]
            md, summaries = consolidate_guide(
                group=group,
                guide=guide,
                version=version,
                topic_blocks=guide_block["topics"],
            )
            (group_dir / f"{safe_id(guide)}__{safe_id(version)}.md").write_text(
                md, encoding="utf-8"
            )
            summaries_by_guide[(guide, version)] = summaries
            n_guide_files += 1

    # Top-level + per-group sub-indexes
    (BUNDLE_DIR / "index.md").write_text(build_top_index(by_group), encoding="utf-8")
    (BUNDLE_DIR / "index").mkdir(parents=True)
    for group, guides in by_group.items():
        (BUNDLE_DIR / "index" / f"{group}.md").write_text(
            build_group_index(group, guides, summaries_by_guide), encoding="utf-8"
        )

    # BUNDLE-INFO.txt
    (BUNDLE_DIR / "BUNDLE-INFO.txt").write_text(
        f"qlik-talend Chat bundle\n"
        f"Built at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Source repo: https://github.com/ElRakiti/claude-qlik-docs\n"
        f"Guide files: {n_guide_files}\n"
        f"\n"
        f"Upload this folder (or the .zip) to claude.ai under Settings -> Skills,\n"
        f"or attach as Project Knowledge in a Project.\n",
        encoding="utf-8",
    )

    # Zip
    DIST.mkdir(exist_ok=True)
    if BUNDLE_ZIP.exists():
        BUNDLE_ZIP.unlink()
    with zipfile.ZipFile(BUNDLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(BUNDLE_DIR.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(BUNDLE_DIR.parent))

    n_files = sum(1 for _ in BUNDLE_DIR.rglob("*") if _.is_file())
    print(
        f"[chat-bundle] {n_guide_files} consolidated guide files + "
        f"{1 + 1 + len(by_group) + 1} index/SKILL/info files = {n_files} files total"
    )
    print(f"[chat-bundle] dir: {BUNDLE_DIR.relative_to(ROOT)}")
    print(
        f"[chat-bundle] zip: {BUNDLE_ZIP.relative_to(ROOT)} "
        f"({BUNDLE_ZIP.stat().st_size // 1024} KB)"
    )
    if n_files > 200:
        print(
            f"[chat-bundle] WARNING: {n_files} files exceeds claude.ai's 200-file limit",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

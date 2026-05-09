"""Build a self-contained skill bundle for upload to claude.ai (Claude Chat).

Differences from the local Claude Code skill:
- No `raw/` directory (Chat has no filesystem access).
- Each topic's Citations table drops the local "Raw file" column; only the
  canonical source URL remains. Claude in Chat can fetch via WebFetch when
  exact wording is needed.
- SKILL.md navigation guidance is rewritten to point at URLs rather than
  raw/<...>.md paths.
- All other artefacts (index.md, per-group sub-indexes, topic files) are
  copied as-is.

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

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skill-output" / "qlik-talend"
DIST = ROOT / "dist"
BUNDLE_DIR = DIST / "qlik-talend-chat"
BUNDLE_ZIP = DIST / "qlik-talend-chat.zip"

# Match a Citations-table row like:
# | `[^P-1]` | `skill-output/.../foo.md` | https://help.qlik.com/... |
CITATION_ROW_RE = re.compile(
    r"\|\s*(`\[\^P-\d+\]`)\s*\|\s*`[^`]+`\s*\|\s*([^|]+?)\s*\|"
)
CITATION_HEADER_RE = re.compile(r"\|\s*Anchor\s*\|\s*Raw file\s*\|\s*Source URL\s*\|")
CITATION_SEPARATOR_RE = re.compile(r"\|-+\|-+\|-+\|")


def transform_topic(text: str) -> str:
    """Drop the 'Raw file' column from the Citations table."""
    out_lines: list[str] = []
    for line in text.splitlines():
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
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


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

| Group | Versions | Pages | Topics |
|-------|---------|------:|-------:|
| studio | 8.0 (latest R-code at crawl) | ~1,068 | ~110 |
| tmc | Cloud | ~328 | ~18 |
| remote-engine | Cloud | ~324 | ~30 |
| installation | Cloud + 8.0 | ~1,032 | ~120 |
| sdlc-cicd | Cloud + 8.0 | ~68 | ~12 |
| cloud-platform | Cloud | ~127 | ~14 |

**Out of scope (do not assume coverage):** Components/connectors reference, Data Catalog, Data Quality, Data Stewardship, Data Preparation, ESB, API Designer, MDM, Data Inventory, all 7.x docs.

## How to look something up — progressive disclosure

This Chat-edition bundle has **no local raw files**. The structure is:

1. `index.md` — top-level navigation across the six product groups.
2. `index/<group>.md` — per-group topic listing with one-line blurbs.
3. `topics/<group>/<guide>/<version>/<topic>.md` — distilled topic with TL;DR per page, procedure outline, notes, and a `## Citations` table mapping each `[^P-N]` anchor → canonical source URL on `help.qlik.com/talend`.

For a typical question, work outside-in:

1. **Read `index.md`** (≈2 KB). Identify which **product group** matches.
2. **Read `index/<group>.md`** (≈10–30 KB). Find the matching **topic**.
3. **Read `topics/<group>/<guide>/<version>/<topic>.md`** (≈3–10 KB). Use the TL;DRs and procedure outlines to answer.
4. **Only if you need exact procedure text or verbatim quotes**, fetch the source URL from the topic's Citations table via WebFetch and read the original Qlik documentation page.

## Citation discipline

When you answer, **always cite**:
- The Qlik major version (`Cloud` or `8.0`) and, for Studio, the R-code (e.g. `8.0-R2026-04`).
- The source URL from the topic's Citations table.

Example: "In TMC (Cloud), promotion environments are configured under … [source: help.qlik.com/talend/en-US/management-console-user-guide/Cloud/manage-promotion]."

## Versioning gotchas

- Studio R-codes (`R2026-04`, etc.) bump monthly. The R-code in this bundle is whatever was latest at crawl time. If the user is on an older R-code, flag that some procedures may have shifted.
- Cloud docs are continuously updated; treat as "as of crawl date".
- 7.x is **not** included. If the user is on 7.x, say so explicitly and do not extrapolate.

## Anti-patterns

- Do NOT load all topic files at once — defeats the purpose of progressive disclosure.
- Do NOT answer "from memory" if the topic file disagrees — the skill is the source of truth.
- Do NOT cite the topic file's TL;DR alone for safety-relevant answers (security, encryption, license, upgrade compatibility) — fetch the source URL and verify.
"""


def main() -> int:
    if not SRC.exists() or not (SRC / "index.md").exists():
        print(
            "skill-output/qlik-talend not built — run `make build` first",
            file=sys.stderr,
        )
        return 1

    # Clean target
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True)

    # 1. Chat-specific SKILL.md
    (BUNDLE_DIR / "SKILL.md").write_text(CHAT_SKILL_MD, encoding="utf-8")

    # 2. index.md (copy as-is — already filesystem-agnostic)
    shutil.copy(SRC / "index.md", BUNDLE_DIR / "index.md")

    # 3. index/<group>.md (copy as-is)
    shutil.copytree(SRC / "index", BUNDLE_DIR / "index")

    # 4. topics/**/*.md — transform Citations table to drop local-file column
    n_topics = 0
    for src_topic in (SRC / "topics").rglob("*.md"):
        rel = src_topic.relative_to(SRC / "topics")
        dst = BUNDLE_DIR / "topics" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            transform_topic(src_topic.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        n_topics += 1

    # 5. BUNDLE-INFO.txt for traceability
    info = (
        f"qlik-talend Chat bundle\n"
        f"Built at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Source repo: https://github.com/ElRakiti/claude-qlik-docs\n"
        f"Topics: {n_topics}\n"
        f"\n"
        f"Upload this folder (or the .zip) to claude.ai under Settings -> Skills,\n"
        f"or attach as Project Knowledge in a Project.\n"
    )
    (BUNDLE_DIR / "BUNDLE-INFO.txt").write_text(info, encoding="utf-8")

    # 6. Zip
    DIST.mkdir(exist_ok=True)
    if BUNDLE_ZIP.exists():
        BUNDLE_ZIP.unlink()
    with zipfile.ZipFile(BUNDLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in BUNDLE_DIR.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(BUNDLE_DIR.parent))

    print(f"[chat-bundle] {n_topics} topics + index + SKILL.md")
    print(f"[chat-bundle] dir: {BUNDLE_DIR.relative_to(ROOT)}")
    print(f"[chat-bundle] zip: {BUNDLE_ZIP.relative_to(ROOT)} "
          f"({BUNDLE_ZIP.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Build a self-contained Skill bundle for upload to claude.ai (Slash command).

In claude.ai, Skills are explicitly invoked via `/qlik-talend`. The
description in the SKILL.md frontmatter shows up in the slash-picker as the
human-readable summary; it has less of a "trigger" role than in Claude Code
(where the model decides when to load the skill based on the description).

Output:
- dist/qlik-talend-chat/   (the bundle directory)
- dist/qlik-talend-chat.zip (zipped, ready for Settings -> Skills upload)

Run: uv run python -m package.build_chat_bundle
"""
from __future__ import annotations

import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Re-export transform_topic_body so existing tests keep working.
from package._consolidate import (  # noqa: F401
    ROOT,
    reset_dir,
    transform_topic_body,
    write_consolidated_artefacts,
)

DIST = ROOT / "dist"
BUNDLE_DIR = DIST / "qlik-talend-chat"
BUNDLE_ZIP = DIST / "qlik-talend-chat.zip"


CHAT_SKILL_MD = """---
name: qlik-talend
description: Authoritative reference for Qlik Talend documentation (Studio 8.0, Talend Management Console Cloud, Remote Engine Linux/Windows + Gen2, Dynamic Engine, hybrid installations, SDLC/CI-CD, Talend Cloud platform). Use when answering questions about Talend Studio jobs/joblets/routes/components/context-variables/metadata/projects/Git, TMC promotions/schedules/tasks/users/tokens/environments/audit, Remote Engine setup/configuration/troubleshooting, Studio→TMC publishing, Git or CI/CD workflows in Talend, hybrid installation/migration/upgrade, or anything mentioning Talend on Qlik Cloud. Sourced from help.qlik.com/talend. Bundle contains 28 consolidated guide files with TOC + topic anchors + citation URLs.
---

# Qlik Talend Documentation Skill (Chat edition)

In claude.ai this skill can either be invoked explicitly via `/qlik-talend`
in the slash picker, or auto-triggered by Claude when the user's question
matches the description above. Once active, use the structure below.

## Tool requirements

This skill is **designed to work with WebFetch**. The bundle itself contains
distilled summaries (TL;DRs, procedure outlines, notes, version
constraints) — enough to answer most questions directly. For exact
procedure text, parameter lists, code snippets, or verbatim quotes, every
topic file has a `## Citations` table mapping its anchors to canonical URLs
on `help.qlik.com/talend`; use `WebFetch` on those URLs to retrieve the
full source page.

- **WebFetch (required for verbatim text):** if unavailable, the skill
  still answers most questions from the distilled summaries, but cannot
  retrieve exact wording.
- **WebSearch (optional fallback):** if a user asks about content not in
  the bundle (e.g. a Talend product marked out-of-scope below, or a topic
  that has shifted since the crawl date), WebSearch over `help.qlik.com`
  is a reasonable next step before declining.

## What's in the bundle (and what's not)

The bundle includes, per page in the source documentation:
- A TL;DR (~1 sentence).
- A procedure outline (the page's H2/H3 headings).
- Notes / restrictions / warnings extracted verbatim.
- Version constraints declared on the page.
- A citation entry with the canonical URL.

The bundle **does not** include:
- Full procedure text (the actual step-by-step prose between headings).
- Exact parameter tables for components.
- Code snippets / configuration examples in full.
- Screenshots, diagrams, or image captions.

If the question can be answered from a TL;DR + outline + notes (e.g.
"what does TMC promotions do?", "what version of Studio do I need for X?",
"what's the entry point for configuring Remote Engine on Linux?"), answer
directly. If it needs verbatim text or exact configuration values, fetch
the source URL.

## What's in this bundle

- **Coverage:** Talend Studio 8.0 (Studio User Guide + companion docs),
  Talend Management Console (Cloud), Remote Engine Linux + Windows (Cloud) +
  Gen2, Dynamic Engine, installation/migration/upgrade guides (Cloud + 8.0),
  SDLC/CI-CD best practices, Talend Cloud getting-started + glossary.
- **Out of scope:** Components/connectors reference, Data Catalog, Data
  Quality, Data Stewardship, Data Preparation, ESB, API Designer, MDM, Data
  Inventory, all 7.x docs.
- **No raw files:** Chat has no filesystem; bundle stores distilled topics
  consolidated per guide+version with citation URLs to the live Qlik docs.

## Coverage at a glance

| Group | Versions | Pages |
|-------|---------|------:|
| studio | 8.0 (latest R-code at crawl) | ~1,068 |
| tmc | Cloud | ~328 |
| remote-engine | Cloud | ~324 |
| installation | Cloud + 8.0 | ~1,032 |
| sdlc-cicd | Cloud + 8.0 | ~68 |
| cloud-platform | Cloud | ~127 |

## File layout

```
SKILL.md                                          (this file)
index.md                                          top-level group index
index/<group>.md                                  per-group topic listing
topics/<group>/<guide>__<version>.md              consolidated guide files
                                                  with TOC + topic anchors
```

## How to navigate (progressive disclosure)

1. Read `index.md` to identify the relevant **product group**.
2. Read `index/<group>.md` to find the matching **topic** and its anchored
   link to the consolidated guide file.
3. Read `topics/<group>/<guide>__<version>.md`. Use `Read` with `offset` /
   `limit` on large guide files (Studio User Guide is ~595 KB) — jump to
   the `<a id="topic-<id>">` anchor for the relevant topic.
4. For exact wording, full procedure text, or verbatim quotes: WebFetch the
   canonical URL from the topic's Citations table.

## Citation discipline

Always cite:
- The Qlik major version (`Cloud` or `8.0`) and, for Studio, the R-code
  (e.g. `8.0-R2026-04`).
- The source URL from the topic's Citations table.

Example: "In TMC (Cloud), promotion environments are configured under …
[source: help.qlik.com/talend/en-US/management-console-user-guide/Cloud/manage-promotion]."

## Versioning gotchas

- Studio R-codes (`R2026-04`, etc.) bump monthly — check `crawled_at` if a
  user is on a newer/older R-code.
- Cloud docs are continuously updated; treat as "as of crawl date".
- 7.x is **not** included. If the user is on 7.x, say so explicitly and do
  not extrapolate.

## Anti-patterns

- Do NOT load all guide files at once — progressive disclosure means one
  group + one guide is enough for almost every answer.
- Do NOT answer "from memory" if the topic disagrees — the skill is the
  source of truth.
- Do NOT cite the topic file's TL;DR alone for safety-relevant answers
  (security, encryption, license, upgrade compatibility) — fetch the source
  URL and verify.
"""


def main() -> int:
    src_topics = ROOT / "skill-output" / "qlik-talend" / "topics"
    if not src_topics.exists():
        print(
            "skill-output/qlik-talend not built — run `make build` first",
            file=sys.stderr,
        )
        return 1

    reset_dir(BUNDLE_DIR)
    (BUNDLE_DIR / "SKILL.md").write_text(CHAT_SKILL_MD, encoding="utf-8")

    by_group, _, n_guide_files = write_consolidated_artefacts(target_dir=BUNDLE_DIR)

    (BUNDLE_DIR / "BUNDLE-INFO.txt").write_text(
        f"qlik-talend Chat-skill bundle\n"
        f"Built at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Source repo: https://github.com/ElRakiti/claude-qlik-docs\n"
        f"Guide files: {n_guide_files}\n"
        f"\n"
        f"In claude.ai: Settings -> Skills -> Upload, pick the .zip alongside\n"
        f"this folder. Then invoke in chat with /qlik-talend.\n",
        encoding="utf-8",
    )

    DIST.mkdir(exist_ok=True)
    if BUNDLE_ZIP.exists():
        BUNDLE_ZIP.unlink()
    with zipfile.ZipFile(BUNDLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(BUNDLE_DIR.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(BUNDLE_DIR.parent))

    n_files = sum(1 for _ in BUNDLE_DIR.rglob("*") if _.is_file())
    print(
        f"[chat-bundle] {n_guide_files} guide files + "
        f"{1 + 1 + len(by_group) + 1} index/SKILL/info = {n_files} files total"
    )
    print(f"[chat-bundle] dir: {BUNDLE_DIR.relative_to(ROOT)}")
    print(
        f"[chat-bundle] zip: {BUNDLE_ZIP.relative_to(ROOT)} "
        f"({BUNDLE_ZIP.stat().st_size // 1024} KB)"
    )
    if n_files > 200:
        print(
            f"[chat-bundle] WARNING: {n_files} files exceeds claude.ai's "
            f"200-file Skill-upload limit",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

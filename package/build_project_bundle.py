"""Build a Project Knowledge bundle for use as a claude.ai Project.

Unlike the Chat-skill bundle (which is invoked explicitly via /qlik-talend),
a Project Knowledge bundle is loaded *implicitly* into every chat in the
Project. So:

- No `SKILL.md` (Project doesn't use that mechanism).
- Instead: `PROJECT-INSTRUCTIONS.md` — copy-paste-ready content for the
  Project's Custom Instructions field. This is the implicit "trigger" for
  Claude in Project chats.
- `README-FOR-USER.md` — short human-facing setup guide.
- Same consolidated guide files + indexes as the Chat skill.
- No ZIP — Project Knowledge accepts file uploads directly. The folder is
  ready to drag-and-drop.

Output:
- dist/qlik-talend-project/

Run: uv run python -m package.build_project_bundle
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from package._consolidate import (
    ROOT,
    reset_dir,
    write_consolidated_artefacts,
)

DIST = ROOT / "dist"
PROJECT_DIR = DIST / "qlik-talend-project"


PROJECT_INSTRUCTIONS = """\
You have access to a curated Qlik Talend documentation reference uploaded
as Project Knowledge. The reference is distilled from help.qlik.com/talend
and covers Talend Studio 8.0, Talend Management Console (Cloud), Remote
Engine (Linux/Windows + Gen2), Dynamic Engine, hybrid installations,
SDLC/CI-CD, and the Talend Cloud platform. Components/connectors reference,
Data Catalog, Data Quality, Data Stewardship, ESB, API Designer, MDM and
all 7.x docs are NOT included — say so explicitly if a user asks about them.

# How to use the knowledge

The reference uses progressive disclosure across these files:

1. `index.md` — top-level navigation across the six product groups.
2. `index/<group>.md` — per-group topic listing (one-line blurb per topic)
   with anchored links to the consolidated guide files.
3. `topics/<group>/<guide>__<version>.md` — one combined file per
   guide+version. Each combined file starts with a Table of Contents and
   contains all topics as anchored sections (`<a id="topic-<id>">`). Some
   files are large (Studio User Guide is ~595 KB) — use search and the
   anchor IDs to navigate.

For a Talend question, work outside-in: pick the product group, find the
relevant topic in the sub-index, jump to the topic anchor in the
consolidated guide file, read the TL;DR + procedure outline + notes. Only
fetch the canonical URL from the topic's Citations table when you need
exact wording, full procedure text, or to verify safety-relevant claims.

# Citation discipline

Always cite:
- The Qlik major version (`Cloud` or `8.0`) and, for Studio, the R-code
  (e.g. `8.0-R2026-04`).
- The source URL from the topic's Citations table.

Example: "In TMC (Cloud), promotion environments are configured under …
[source: help.qlik.com/talend/en-US/management-console-user-guide/Cloud/manage-promotion]."

# Versioning gotchas

- Studio R-codes bump monthly. The bundled R-code is whatever was latest
  at crawl time.
- Cloud docs are continuously updated; treat as "as of crawl date".
- If the user is on 7.x, say so explicitly and do not extrapolate from 8.0.
- Some pages have explicit `version_constraints` in their Citations
  context — honour them.

# Anti-patterns

- Do NOT load all guide files at once — progressive disclosure means one
  group + one guide is enough for almost every answer.
- Do NOT answer "from memory" if the documentation disagrees — the
  Project Knowledge is the source of truth for the topics it covers.
- Do NOT cite a TL;DR alone for safety-relevant answers (security,
  encryption, license, upgrade compatibility) — fetch the source URL and
  verify.
- Do NOT silently extrapolate from in-bundle 8.0 content to user
  scenarios on 7.x — say the version is unsupported by this reference.
"""


README_FOR_USER = """\
# qlik-talend Project bundle

This folder is meant to be uploaded as **Project Knowledge** to a claude.ai
Project, *not* installed as a Skill. Steps:

1. **Create a new Project** in claude.ai.
2. Open `PROJECT-INSTRUCTIONS.md` in this folder, copy its contents, and
   paste them into the Project's **Custom Instructions** field.
3. Upload the rest of this folder's contents (`index.md`, `index/`,
   `topics/`) as Project Knowledge files.
4. From now on, any chat in this Project automatically has the Talend
   reference available — no slash command needed.

If you want a slash-command-triggered experience instead, use
`dist/qlik-talend-chat.zip` and upload it under Settings → Skills.
"""


def main() -> int:
    src_topics = ROOT / "skill-output" / "qlik-talend" / "topics"
    if not src_topics.exists():
        print(
            "skill-output/qlik-talend not built — run `make build` first",
            file=sys.stderr,
        )
        return 1

    reset_dir(PROJECT_DIR)

    (PROJECT_DIR / "PROJECT-INSTRUCTIONS.md").write_text(
        PROJECT_INSTRUCTIONS, encoding="utf-8"
    )
    (PROJECT_DIR / "README-FOR-USER.md").write_text(
        README_FOR_USER, encoding="utf-8"
    )

    by_group, _, n_guide_files = write_consolidated_artefacts(target_dir=PROJECT_DIR)

    (PROJECT_DIR / "BUNDLE-INFO.txt").write_text(
        f"qlik-talend Project-Knowledge bundle\n"
        f"Built at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Source repo: https://github.com/mkcimt/claude-qlik-docs\n"
        f"Guide files: {n_guide_files}\n"
        f"\n"
        f"This folder is meant for claude.ai Projects, not Skills.\n"
        f"See README-FOR-USER.md for upload instructions.\n",
        encoding="utf-8",
    )

    n_files = sum(1 for _ in PROJECT_DIR.rglob("*") if _.is_file())
    total_kb = sum(p.stat().st_size for p in PROJECT_DIR.rglob("*") if p.is_file()) // 1024
    print(
        f"[project-bundle] {n_guide_files} guide files + "
        f"{2 + 1 + len(by_group) + 1} instructions/index/info = {n_files} files total"
    )
    print(f"[project-bundle] dir: {PROJECT_DIR.relative_to(ROOT)} ({total_kb} KB total)")
    print()
    print(f"Next steps:")
    print(f"  1. Open {PROJECT_DIR / 'PROJECT-INSTRUCTIONS.md'} and copy its contents.")
    print(f"  2. In claude.ai: New Project -> paste into Custom Instructions.")
    print(f"  3. Upload everything else from {PROJECT_DIR} as Project Knowledge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

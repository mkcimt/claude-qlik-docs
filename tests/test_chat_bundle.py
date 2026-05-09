"""Chat-bundle topic transformer: drop Raw column, strip frontmatter, demote headings."""
from __future__ import annotations

from package.build_chat_bundle import transform_topic_body


SOURCE = """\
---
topic_id: foo
product_group: g
guide: g
---

# Foo

Some intro [^P-1].

## Pages
- a
- b

### Per-page summaries

Body content.

## Citations

| Anchor | Raw file | Source URL |
|--------|----------|-----------|
| `[^P-1]` | `skill-output/qlik-talend/raw/g/h.md` | https://help.qlik.com/talend/en-US/g/Cloud/h |
| `[^P-2]` | `skill-output/qlik-talend/raw/g/i.md` | https://help.qlik.com/talend/en-US/g/Cloud/i |
"""


def test_drops_raw_column():
    out = transform_topic_body(SOURCE)
    assert "Raw file" not in out
    assert "skill-output/qlik-talend/raw" not in out


def test_keeps_anchor_and_url():
    out = transform_topic_body(SOURCE)
    assert "`[^P-1]`" in out
    assert "https://help.qlik.com/talend/en-US/g/Cloud/h" in out
    assert "https://help.qlik.com/talend/en-US/g/Cloud/i" in out


def test_strips_frontmatter():
    out = transform_topic_body(SOURCE)
    assert "topic_id: foo" not in out
    assert not out.startswith("---")


def test_demotes_headings():
    # H1 → H2, H2 → H3, H3 → H4 — so the topic body fits under guide-level
    # H1 + topic-level H2 in the consolidated file.
    out = transform_topic_body(SOURCE)
    # Original "# Foo" becomes "## Foo"
    assert "## Foo" in out
    # Original "## Pages" becomes "### Pages"
    assert "### Pages" in out
    # Original "### Per-page summaries" becomes "#### Per-page summaries"
    assert "#### Per-page summaries" in out
    # No leftover top-level H1
    assert not any(
        line.startswith("# ") and not line.startswith("## ")
        for line in out.splitlines()
    )


def test_two_columns_in_output_table():
    out = transform_topic_body(SOURCE)
    out_citations = out.split("Citations", 1)[1]
    header_line = next(line for line in out_citations.splitlines() if "Anchor" in line)
    assert header_line.count("|") == 3

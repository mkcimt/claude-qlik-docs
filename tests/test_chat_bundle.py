"""Chat-bundle topic transform drops the local Raw-file column."""
from __future__ import annotations

from package.build_chat_bundle import transform_topic


SOURCE = """\
# Foo

Some intro [^P-1].

Lists:
- item one
- item two

## Citations

| Anchor | Raw file | Source URL |
|--------|----------|-----------|
| `[^P-1]` | `skill-output/qlik-talend/raw/g/h.md` | https://help.qlik.com/talend/en-US/g/Cloud/h |
| `[^P-2]` | `skill-output/qlik-talend/raw/g/i.md` | https://help.qlik.com/talend/en-US/g/Cloud/i |
"""


def test_drops_raw_column():
    out = transform_topic(SOURCE)
    assert "Raw file" not in out
    assert "skill-output/qlik-talend/raw" not in out


def test_keeps_anchor_and_url():
    out = transform_topic(SOURCE)
    assert "`[^P-1]`" in out
    assert "https://help.qlik.com/talend/en-US/g/Cloud/h" in out
    assert "https://help.qlik.com/talend/en-US/g/Cloud/i" in out


def test_body_unchanged():
    out = transform_topic(SOURCE)
    # Pre-Citations content must be preserved verbatim.
    body_pre, _, _ = SOURCE.partition("## Citations")
    out_pre, _, _ = out.partition("## Citations")
    assert out_pre == body_pre


def test_two_columns_in_output_table():
    out = transform_topic(SOURCE)
    out_citations = out.split("## Citations", 1)[1]
    # Header + separator should each have exactly two pipes between content
    header_line = next(line for line in out_citations.splitlines() if "Anchor" in line)
    assert header_line.count("|") == 3  # | a | b |

"""Mechanical extraction helpers for distilled topic files."""
from __future__ import annotations

from distill.build_topics import (
    extract_notes,
    extract_outline,
    extract_tldr,
    split_frontmatter,
)


class TestExtractTLDR:
    def test_first_paragraph_after_h1(self):
        body = """# Title

This is the first paragraph that should become the TL;DR.

## Section
Other content.
"""
        tldr = extract_tldr(body)
        assert tldr.startswith("This is the first paragraph")
        assert "Section" not in tldr

    def test_caps_long_paragraphs(self):
        body = "# Title\n\n" + ("A long sentence. " * 30)
        tldr = extract_tldr(body)
        assert len(tldr) <= 281

    def test_handles_missing_body(self):
        assert extract_tldr("# Title\n\n") == ""


class TestExtractOutline:
    def test_returns_h2_h3_in_order(self):
        body = """# Title

## First
text
### Sub-A
text
## Second
text"""
        outline = extract_outline(body)
        assert any("First" in line for line in outline)
        assert any("Sub-A" in line for line in outline)
        assert any("Second" in line for line in outline)
        # H3 should be more deeply indented than H2
        h3_line = next(line for line in outline if "Sub-A" in line)
        h2_line = next(line for line in outline if "First" in line)
        assert h3_line.startswith(" ") or h3_line.count("  ") > h2_line.count("  ")

    def test_max_12_entries(self):
        body = "# Title\n\n" + "\n".join(f"## H{i}" for i in range(20))
        outline = extract_outline(body)
        assert len(outline) <= 12

    def test_dedupes_repeats(self):
        body = "# Title\n\n## Procedure\n## Procedure\n## Result"
        outline = extract_outline(body)
        # "Procedure" should appear only once
        proc_count = sum(1 for line in outline if "Procedure" in line)
        assert proc_count == 1


class TestExtractNotes:
    def test_finds_note_block(self):
        body = "Some prose.\nInformation note Note: Studio 8.0.1 is required for X."
        notes = extract_notes(body)
        assert any("Note:" in n for n in notes)
        assert any("8.0.1" in n for n in notes)

    def test_finds_restriction_block(self):
        body = "Information note Restriction: Not available in Europe (Paris) region."
        notes = extract_notes(body)
        assert any("Restriction:" in n for n in notes)

    def test_caps_at_six(self):
        body = "\n".join(f"Information note Note: item {i}." for i in range(20))
        assert len(extract_notes(body)) <= 6


class TestSplitFrontmatter:
    def test_extracts_yaml_frontmatter(self):
        text = "---\ntitle: Foo\nproduct_group: studio\n---\n\nbody text\n"
        fm, body = split_frontmatter(text)
        assert fm["title"] == "Foo"
        assert fm["product_group"] == "studio"
        assert body.strip() == "body text"

    def test_no_frontmatter_returns_empty_dict(self):
        text = "just body\nno frontmatter"
        fm, body = split_frontmatter(text)
        assert fm == {}
        assert body == text

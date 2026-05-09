"""HTML → markdown extraction (the title-bug regression test lives here)."""
from __future__ import annotations

from pathlib import Path

import pytest

from crawler.extract import extract, render_with_frontmatter

FIXTURE = Path(__file__).parent / "fixtures" / "sample_studio.html"
SAMPLE_URL = (
    "https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-04/what-is-talend-studio"
)


@pytest.fixture
def page():
    html = FIXTURE.read_text(encoding="utf-8")
    return extract(html, SAMPLE_URL)


class TestExtract:
    def test_title_no_isTalend_regression(self, page):
        # Pre-fix output was "What isTalend Studio?" (missing space due to <svg> icon).
        # After fix, separator=" " plus whitespace collapse should yield correct title.
        assert page.title == "What is Talend Studio?"

    def test_markdown_starts_with_h1(self, page):
        assert page.content_markdown.lstrip().startswith("# ")

    def test_junk_stripped(self, page):
        body = page.content_markdown
        assert "junk" not in body.lower()
        assert "feedback widget" not in body
        assert "Was this helpful?" not in body
        assert "copyright stuff" not in body

    def test_content_sha_is_stable(self, page):
        # SHA should be deterministic given identical input — re-run yields same hash.
        html = FIXTURE.read_text(encoding="utf-8")
        again = extract(html, SAMPLE_URL)
        assert again.content_sha == page.content_sha

    def test_version_constraints_extracted(self, page):
        # Fixture contains "Talend Studio 8.0.1 R2024-05 or higher" — regex should catch it.
        joined = " ".join(page.version_constraints).lower()
        assert "8.0.1" in joined or "r2024-05" in joined.replace(" ", "")

    def test_compression_meaningful(self, page):
        # markdown should be substantially smaller than raw HTML
        assert page.markdown_bytes < page.raw_html_bytes
        assert page.markdown_bytes > 0


class TestFrontmatter:
    def test_frontmatter_has_required_fields(self, page):
        rendered = render_with_frontmatter(page, product_group="studio")
        assert rendered.startswith("---\n")
        # essential fields
        for field in (
            "source_url:",
            "title:",
            "product_group: studio",
            "major_version:",
            "r_code:",
            "content_sha:",
            "crawled_at:",
        ):
            assert field in rendered, f"missing field: {field}"

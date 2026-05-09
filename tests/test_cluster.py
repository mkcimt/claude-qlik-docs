"""Topic clustering heuristics."""
from __future__ import annotations

from distill.cluster import (
    MAX_PAGES_PER_TOPIC,
    PageRef,
    _fallback_topic_id,
    _topic_prefix_for,
    cluster_guide,
)


def make_page(slug: str, idx: int = 0, version: str = "Cloud") -> PageRef:
    return PageRef(
        url=f"https://help.qlik.com/talend/en-US/g/{version}/{slug}",
        title=slug.replace("-", " ").title(),
        slug=slug,
        product_group="g",
        product_slug="g",
        version=version,
        out_path=f"raw/g/g/{version}/{slug}.md",
        sitemap_index=idx,
    )


class TestPrefixMatcher:
    def test_curated_prefix_match(self):
        assert _topic_prefix_for("logging-in-to-tmc") == "logging-in"

    def test_longest_prefix_wins(self):
        # "logging-" and "logging-in" both match "logging-in-..." → longer wins
        assert _topic_prefix_for("logging-in-failure") == "logging-in"

    def test_no_match_returns_none(self):
        assert _topic_prefix_for("xyz-foo-bar") is None


class TestFallbackTopicID:
    def test_uses_first_word(self):
        assert _fallback_topic_id("centralizing-mongodb-metadata") == "centralizing"

    def test_short_prefix_fallback_misc(self):
        # Slugs starting with very short tokens (<3 chars) fall through to "misc".
        assert _fallback_topic_id("ab") == "misc"


class TestClusterGuide:
    def test_groups_by_curated_prefix(self):
        pages = [
            make_page("logging-in-foo", 1),
            make_page("logging-in-bar", 2),
            make_page("creating-foo", 3),
            make_page("creating-bar", 4),
        ]
        topics = cluster_guide(pages)
        ids = [t["id"] for t in topics]
        # Two distinct topics, one per prefix
        assert "logging-in" in ids
        assert "creating" in ids

    def test_uses_first_word_fallback_for_unknown_prefix(self):
        pages = [
            make_page("centralizing-foo", 1),
            make_page("centralizing-bar", 2),
        ]
        topics = cluster_guide(pages)
        assert topics[0]["id"] == "centralizing"

    def test_max_pages_per_topic_enforced(self):
        pages = [make_page(f"creating-thing-{i}", i) for i in range(MAX_PAGES_PER_TOPIC + 5)]
        topics = cluster_guide(pages)
        # Should split into >= 2 buckets, none exceeding MAX
        assert len(topics) >= 2
        assert all(len(t["pages"]) <= MAX_PAGES_PER_TOPIC for t in topics)

    def test_unique_ids_within_guide(self):
        pages = [make_page(f"creating-a-{i}", i) for i in range(MAX_PAGES_PER_TOPIC * 2 + 3)]
        topics = cluster_guide(pages)
        ids = [t["id"] for t in topics]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"

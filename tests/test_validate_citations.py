"""Citation-validator finds missing anchors and broken raw-file/URL refs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import distill.validate_citations as vc


VALID_TOPIC = """\
# Foo Topic

Some text [^P-1].

More text [^P-2].

## Citations

| Anchor | Raw file | Source URL |
|--------|----------|-----------|
| `[^P-1]` | `raw/g/h.md` | https://help.qlik.com/talend/en-US/g/Cloud/h |
| `[^P-2]` | `raw/g/i.md` | https://help.qlik.com/talend/en-US/g/Cloud/i |
"""


@pytest.fixture
def fixture_workspace(tmp_path: Path, monkeypatch):
    """Set up a fake skill-output tree in a tmp dir and point the validator at it."""
    raw_dir = tmp_path / "raw" / "g"
    raw_dir.mkdir(parents=True)
    (raw_dir / "h.md").write_text("page h", encoding="utf-8")
    (raw_dir / "i.md").write_text("page i", encoding="utf-8")

    topics_dir = tmp_path / "topics"
    topics_dir.mkdir()
    manifest = tmp_path / "manifest.json"

    pages = {
        "https://help.qlik.com/talend/en-US/g/Cloud/h": {},
        "https://help.qlik.com/talend/en-US/g/Cloud/i": {},
    }
    manifest.write_text(json.dumps({"pages": pages}), encoding="utf-8")

    monkeypatch.setattr(vc, "ROOT", tmp_path)
    monkeypatch.setattr(vc, "TOPICS_DIR", topics_dir)
    monkeypatch.setattr(vc, "MANIFEST", manifest)

    return tmp_path, topics_dir


def test_valid_topic_returns_zero(fixture_workspace, capsys):
    _, topics_dir = fixture_workspace
    (topics_dir / "ok.md").write_text(VALID_TOPIC, encoding="utf-8")
    rc = vc.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "all citations valid" in out


def test_anchor_used_but_not_in_table_flagged(fixture_workspace, capsys):
    _, topics_dir = fixture_workspace
    bad = VALID_TOPIC.replace("[^P-2].", "[^P-3].")  # P-3 used, only P-1/P-2 in table
    (topics_dir / "bad.md").write_text(bad, encoding="utf-8")
    rc = vc.main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "anchors used in body but not in table" in out
    assert "P-3" in out


def test_missing_raw_file_flagged(fixture_workspace, capsys):
    tmp_path, topics_dir = fixture_workspace
    (tmp_path / "raw" / "g" / "i.md").unlink()
    (topics_dir / "ok.md").write_text(VALID_TOPIC, encoding="utf-8")
    rc = vc.main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "raw file missing" in out


def test_url_not_in_manifest_flagged(fixture_workspace, capsys):
    tmp_path, topics_dir = fixture_workspace
    bad = VALID_TOPIC.replace(
        "https://help.qlik.com/talend/en-US/g/Cloud/i",
        "https://help.qlik.com/talend/en-US/g/Cloud/MISSING",
    )
    (topics_dir / "bad.md").write_text(bad, encoding="utf-8")
    rc = vc.main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "URL not in manifest" in out

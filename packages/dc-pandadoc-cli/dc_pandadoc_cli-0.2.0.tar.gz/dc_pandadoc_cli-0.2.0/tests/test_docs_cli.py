from __future__ import annotations

from pathlib import Path


def test_cli_docs_mentions_persisted_links() -> None:
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "CLI.md"
    content = doc_path.read_text(encoding="utf-8")

    assert "persisted" in content.lower()
    assert "link" in content.lower()


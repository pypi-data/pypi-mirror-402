from __future__ import annotations

from pathlib import Path

import pytest

from pandadoc_cli.commands import copper as copper_cmd
from pandadoc_cli.config import Config, reset_config


def _use_temp_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(
        Config,
        "user_config_path",
        classmethod(lambda cls: config_path),
    )
    # Also patch _config_paths so load() finds the temp config
    monkeypatch.setattr(
        Config,
        "_config_paths",
        classmethod(lambda cls: [config_path]),
    )
    reset_config()
    return config_path


def test_set_link_persists_to_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _use_temp_config(monkeypatch, tmp_path)

    copper_cmd._set_doc_link("doc_123", 456)

    # Simulate a new process by clearing memory + config cache.
    copper_cmd._doc_links.clear()
    reset_config()

    assert copper_cmd._get_doc_link("doc_123") == 456


def test_clear_link_removes_from_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _use_temp_config(monkeypatch, tmp_path)

    copper_cmd._set_doc_link("doc_456", 789)
    copper_cmd._clear_doc_link("doc_456")

    copper_cmd._doc_links.clear()
    reset_config()

    assert copper_cmd._get_doc_link("doc_456") is None


def test_invalid_link_value_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _use_temp_config(monkeypatch, tmp_path)

    config = Config.load()
    config.mapping["_link_doc_bad"] = "not-a-number"
    config.save()

    reset_config()

    assert copper_cmd._get_doc_link("doc_bad") is None

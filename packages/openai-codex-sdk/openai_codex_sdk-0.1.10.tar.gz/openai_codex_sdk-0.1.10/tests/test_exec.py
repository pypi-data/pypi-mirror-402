from __future__ import annotations

from pathlib import Path

import pytest

from openai_codex_sdk.errors import CodexExecError
from openai_codex_sdk.exec import find_codex_path


def test_find_codex_path_uses_system_path_when_packaged_binary_missing(monkeypatch):
    fake_binary = "/usr/local/bin/codex"

    def fake_exists(self: Path) -> bool:
        return False

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr("openai_codex_sdk.exec.shutil.which", lambda _: fake_binary)

    assert find_codex_path() == fake_binary


def test_find_codex_path_raises_with_helpful_message_when_missing(monkeypatch):
    def fake_exists(self: Path) -> bool:
        return False

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr("openai_codex_sdk.exec.shutil.which", lambda _: None)

    with pytest.raises(CodexExecError, match="Codex CLI not found"):
        find_codex_path()

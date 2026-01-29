from __future__ import annotations

import json
from pathlib import Path

import pytest

from openai_codex_sdk.auth import login_with_auth_json
from openai_codex_sdk.errors import CodexAuthError


def test_login_with_auth_json_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CODEX_AUTH_JSON", json.dumps({"api_key": "x"}))
    dst = tmp_path / "auth.json"
    out = login_with_auth_json(path=str(dst))
    assert out == str(dst)
    assert json.loads(dst.read_text())["api_key"] == "x"


def test_login_with_auth_json_invalid_json_raises(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CODEX_AUTH_JSON", "{not json}")
    with pytest.raises(CodexAuthError, match="Invalid JSON"):
        login_with_auth_json(path=str(tmp_path / "auth.json"))


def test_login_with_auth_json_no_overwrite(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CODEX_AUTH_JSON", raising=False)
    dst = tmp_path / "auth.json"
    dst.write_text(json.dumps({"api_key": "existing"}))
    out = login_with_auth_json(
        auth_json=json.dumps({"api_key": "new"}), path=str(dst), overwrite=False
    )
    assert out == str(dst)
    assert json.loads(dst.read_text())["api_key"] == "existing"


def test_login_with_auth_json_expands_user_path(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    dst = tmp_path / "auth.json"
    out = login_with_auth_json(
        auth_json=json.dumps({"api_key": "x"}),
        path="~/auth.json",
        overwrite=True,
    )
    assert out == str(dst)
    assert json.loads(dst.read_text())["api_key"] == "x"

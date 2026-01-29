from __future__ import annotations

from typing import Dict, Iterator, List

import pytest

from openai_codex_sdk import Codex
from openai_codex_sdk.errors import CodexAuthError


class _ProcStub:
    def __init__(self, lines: List[str]) -> None:
        self._lines = lines
        self.stdout = _LineStream(lines)

    def wait(self) -> int:
        return 0


class _LineStream:
    def __init__(self, lines: List[str]) -> None:
        self._lines = lines

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)


def test_login_with_device_code_streams_output(monkeypatch, capsys) -> None:
    captured: Dict[str, List[str] | None] = {"args": None}

    def fake_popen(
        args: List[str],
        stdout: object,
        stderr: object,
        env: Dict[str, str] | None,
        text: bool,
        bufsize: int,
    ) -> _ProcStub:
        captured["args"] = list(args)
        return _ProcStub(["code: ABC\n", "done\n"])

    monkeypatch.setattr("openai_codex_sdk.auth.subprocess.Popen", fake_popen)

    codex = Codex({"codex_path_override": "/bin/codex"})
    status = codex.login_with_device_code()

    assert status == 0
    assert captured["args"] == ["/bin/codex", "login", "--device-auth"]
    assert "code: ABC" in capsys.readouterr().out


def test_login_with_device_code_missing_binary(monkeypatch) -> None:
    def fake_popen(*_args: object, **_kwargs: object) -> _ProcStub:
        raise FileNotFoundError("missing")

    monkeypatch.setattr("openai_codex_sdk.auth.subprocess.Popen", fake_popen)

    codex = Codex({"codex_path_override": "/missing/codex"})
    with pytest.raises(CodexAuthError, match="Codex CLI not found"):
        codex.login_with_device_code()

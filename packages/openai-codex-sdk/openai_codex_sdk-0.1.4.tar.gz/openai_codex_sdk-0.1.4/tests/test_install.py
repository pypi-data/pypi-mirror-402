from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from openai_codex_sdk.errors import CodexInstallError
from openai_codex_sdk.install import install_codex


def _make_tar_gz_with_codex(path_in_tar: str, content: bytes = b"#!/bin/sh\necho hi\n") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        ti = tarfile.TarInfo(name=path_in_tar)
        ti.size = len(content)
        ti.mode = 0o755
        tf.addfile(ti, io.BytesIO(content))
    return buf.getvalue()


def test_install_codex_installs_to_vendor_dir(monkeypatch, tmp_path: Path):
    data = _make_tar_gz_with_codex("codex/codex")

    monkeypatch.setattr("openai_codex_sdk.install._download", lambda url, dst: dst.write_bytes(data))
    monkeypatch.setattr("openai_codex_sdk.install.sys_platform", lambda: "linux")
    monkeypatch.setattr("openai_codex_sdk.install._target_triple", lambda: "x86_64-unknown-linux-musl")

    install_dir = tmp_path / "vendor" / "x86_64-unknown-linux-musl" / "codex"
    res = install_codex(version="v0.0.0", install_dir=str(install_dir))

    assert res.installed is True
    assert Path(res.codex_path).exists()
    assert Path(res.codex_path).name == "codex"


def test_install_codex_accepts_triple_named_binary(monkeypatch, tmp_path: Path):
    data = _make_tar_gz_with_codex("codex-x86_64-unknown-linux-musl")

    monkeypatch.setattr("openai_codex_sdk.install._download", lambda url, dst: dst.write_bytes(data))
    monkeypatch.setattr("openai_codex_sdk.install.sys_platform", lambda: "linux")
    monkeypatch.setattr("openai_codex_sdk.install._target_triple", lambda: "x86_64-unknown-linux-musl")

    install_dir = tmp_path / "vendor" / "x86_64-unknown-linux-musl" / "codex"
    res = install_codex(version="v0.0.0", install_dir=str(install_dir))

    assert res.installed is True
    assert Path(res.codex_path).exists()
    assert Path(res.codex_path).name == "codex"


def test_install_codex_no_overwrite_returns_installed_false(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("openai_codex_sdk.install.sys_platform", lambda: "linux")
    monkeypatch.setattr("openai_codex_sdk.install._target_triple", lambda: "x86_64-unknown-linux-musl")

    install_dir = tmp_path / "vendor" / "x86_64-unknown-linux-musl" / "codex"
    install_dir.mkdir(parents=True)
    existing = install_dir / "codex"
    existing.write_text("already here")

    res = install_codex(version="v0.0.0", install_dir=str(install_dir), overwrite=False)

    assert res.installed is False
    assert res.codex_path == str(existing)


def test_install_codex_bad_sha256_raises(monkeypatch, tmp_path: Path):
    data = _make_tar_gz_with_codex("codex/codex")

    monkeypatch.setattr("openai_codex_sdk.install._download", lambda url, dst: dst.write_bytes(data))
    monkeypatch.setattr("openai_codex_sdk.install.sys_platform", lambda: "linux")
    monkeypatch.setattr("openai_codex_sdk.install._target_triple", lambda: "x86_64-unknown-linux-musl")

    with pytest.raises(CodexInstallError, match="SHA256 mismatch"):
        install_codex(
            version="v0.0.0",
            install_dir=str(tmp_path / "vendor"),
            sha256="0" * 64,
        )

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import tarfile
import tempfile
import ssl
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .errors import CodexInstallError


@dataclass(frozen=True)
class CodexInstallResult:
    codex_path: str
    installed: bool


def _target_triple() -> str:
    system = sys_platform()
    machine = platform.machine().lower()

    if system in ("linux", "android"):
        if machine in ("x86_64", "amd64"):
            return "x86_64-unknown-linux-musl"
        if machine in ("aarch64", "arm64"):
            return "aarch64-unknown-linux-musl"
    elif system == "darwin":
        if machine in ("x86_64", "amd64"):
            return "x86_64-apple-darwin"
        if machine in ("aarch64", "arm64"):
            return "aarch64-apple-darwin"
    elif system == "win32":
        if machine in ("x86_64", "amd64"):
            return "x86_64-pc-windows-msvc"
        if machine in ("aarch64", "arm64"):
            return "aarch64-pc-windows-msvc"

    raise CodexInstallError(f"Unsupported platform: {system} ({machine})")


def sys_platform() -> str:
    import sys

    return sys.platform


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dst: Path) -> None:
    try:
        context = ssl.create_default_context()
        # Some Python distributions (notably certain macOS framework installs) may not
        # have system certs wired up. Respect user-provided SSL_CERT_FILE/SSL_CERT_DIR.
        cafile = os.environ.get("SSL_CERT_FILE")
        capath = os.environ.get("SSL_CERT_DIR")
        if cafile or capath:
            context.load_verify_locations(cafile=cafile, capath=capath)

        with urllib.request.urlopen(url, context=context) as resp:  # noqa: S310 (url is user/SDK provided)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("wb") as f:
                shutil.copyfileobj(resp, f)
    except Exception as e:
        raise CodexInstallError(f"Failed to download {url}: {e}") from e


def _safe_extract_tar_gz(archive_path: Path, extract_dir: Path) -> None:
    try:
        with tarfile.open(archive_path, mode="r:gz") as tf:
            for member in tf.getmembers():
                member_path = (extract_dir / member.name).resolve()
                if not str(member_path).startswith(str(extract_dir.resolve())):
                    raise CodexInstallError(f"Unsafe tar entry: {member.name}")
            tf.extractall(extract_dir, filter="data")  # noqa: S202 (validated paths above)
    except CodexInstallError:
        raise
    except Exception as e:
        raise CodexInstallError(f"Failed to extract {archive_path}: {e}") from e


def _ensure_executable(path: Path) -> None:
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception as e:
        raise CodexInstallError(f"Failed to mark executable: {path}: {e}") from e


def install_codex(
    *,
    version: str,
    install_dir: Optional[str] = None,
    base_url: str = "https://github.com/openai/codex/releases/download",
    filename: Optional[str] = None,
    sha256: Optional[str] = None,
    overwrite: bool = False,
) -> CodexInstallResult:
    """Download and install the Codex CLI into this package's vendor directory.

    This is intended for notebook/container environments where `pip install` cannot
    ship native binaries. Users explicitly opt in by calling `Codex.install(...)`.

    Args:
      version: The Codex CLI release tag (e.g. "v0.1.0").
      install_dir: Destination directory. Defaults to
        `<pkg>/vendor/<target-triple>/codex/`.
      base_url: Base URL hosting release assets.
      filename: Release asset filename to download. Defaults to
        `codex-<target-triple>.tar.gz`.
      sha256: Optional SHA256 checksum for the downloaded archive.
      overwrite: Replace an existing codex binary if present.
    """

    if not version:
        raise CodexInstallError("version is required")

    triple = _target_triple()
    system = sys_platform()
    codex_binary = "codex.exe" if system == "win32" else "codex"

    pkg_dir = Path(__file__).resolve().parent
    if install_dir is None:
        install_root = pkg_dir / "vendor" / triple / "codex"
    else:
        install_root = Path(install_dir).expanduser().resolve()

    dest_path = install_root / codex_binary
    if dest_path.exists() and not overwrite:
        return CodexInstallResult(codex_path=str(dest_path), installed=False)

    # Default asset name matches current GitHub release assets, e.g.:
    #   codex-x86_64-unknown-linux-musl.tar.gz
    asset_name = filename or f"codex-{triple}.tar.gz"
    url = f"{base_url}/{version}/{asset_name}"

    with tempfile.TemporaryDirectory(prefix="openai-codex-sdk-install-") as td:
        td_path = Path(td)
        archive_path = td_path / asset_name
        _download(url, archive_path)

        if sha256 is not None:
            got = _sha256_file(archive_path)
            if got.lower() != sha256.lower():
                raise CodexInstallError(
                    f"SHA256 mismatch for {asset_name}: expected {sha256}, got {got}"
                )

        extract_dir = td_path / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        _safe_extract_tar_gz(archive_path, extract_dir)

        # Release assets vary; accept common layouts:
        # - <codex|codex.exe> at archive root
        # - codex/<codex|codex.exe>
        # - codex-<target-triple>[.exe] at archive root (GitHub release naming)
        candidates = [
            extract_dir / codex_binary,
            extract_dir / "codex" / codex_binary,
            extract_dir / f"codex-{triple}{'.exe' if system == 'win32' else ''}",
        ]
        src = next((c for c in candidates if c.is_file()), None)
        if src is None:
            raise CodexInstallError(
                f"Downloaded archive did not contain expected binary: {codex_binary}"
            )

        install_root.mkdir(parents=True, exist_ok=True)

        tmp_dest = install_root / (codex_binary + ".tmp")
        try:
            shutil.copy2(src, tmp_dest)
            _ensure_executable(tmp_dest)
            os.replace(tmp_dest, dest_path)
        finally:
            try:
                if tmp_dest.exists():
                    tmp_dest.unlink()
            except Exception:
                pass

    return CodexInstallResult(codex_path=str(dest_path), installed=True)

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, IO, Iterator, Optional

from .errors import CodexAuthError


def login_with_auth_json(
    *,
    auth_json: Optional[str] = None,
    env_var: str = "CODEX_AUTH_JSON",
    path: Optional[str] = None,
    overwrite: bool = False,
    mode: int = 0o600,
) -> str:
    """Write Codex CLI `auth.json` to disk.

    Defaults to `~/.codex/auth.json` unless `path` is provided.
    Validates that the payload is JSON before writing.
    """

    payload = auth_json
    if payload is None:
        payload = os.environ.get(env_var)
    if not payload:
        raise CodexAuthError(f"Missing auth JSON (provide auth_json or set {env_var})")

    try:
        parsed = json.loads(payload)
    except Exception as e:
        raise CodexAuthError(f"Invalid JSON for auth file: {e}") from e

    expanded_path = os.path.expanduser(path) if path else None
    dst = (
        Path(expanded_path).resolve()
        if expanded_path
        else (Path.home() / ".codex" / "auth.json")
    )
    if dst.exists() and not overwrite:
        return str(dst)

    dst.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = dst.with_name(dst.name + ".tmp")
    tmp_path.write_text(
        json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    try:
        os.chmod(tmp_path, mode)
    except Exception:
        pass
    os.replace(tmp_path, dst)
    return str(dst)


def login_with_device_code(
    *,
    executable_path: str,
    env: Optional[Dict[str, str]] = None,
) -> int:
    """Run `codex login --device-auth` and stream output to stdout."""
    try:
        proc = subprocess.Popen(
            [executable_path, "login", "--device-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            bufsize=1,
        )
        proc_stdout = proc.stdout
    except FileNotFoundError as exc:
        raise CodexAuthError(f"Codex CLI not found at {executable_path}") from exc

    if proc_stdout is None:
        raise CodexAuthError("Codex login did not expose stdout")

    _stream_process_output(proc_stdout)
    return proc.wait()


def _stream_process_output(stream: IO[str]) -> None:
    for line in _iter_lines(stream):
        sys.stdout.write(line)
        sys.stdout.flush()


def _iter_lines(stream: IO[str]) -> Iterator[str]:
    for line in stream:
        yield line

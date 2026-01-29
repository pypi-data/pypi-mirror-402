from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .errors import CodexAuthError


def write_auth_json(
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

    dst = Path(path).expanduser().resolve() if path else (Path.home() / ".codex" / "auth.json")
    if dst.exists() and not overwrite:
        return str(dst)

    dst.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = dst.with_name(dst.name + ".tmp")
    tmp_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp_path, mode)
    except Exception:
        pass
    os.replace(tmp_path, dst)
    return str(dst)

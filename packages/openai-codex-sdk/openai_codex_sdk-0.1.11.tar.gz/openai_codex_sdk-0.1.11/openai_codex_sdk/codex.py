from __future__ import annotations

from typing import Any, Optional, Union

from .exec import CodexExec, CodexExecArgs
from .auth import login_with_auth_json, login_with_device_code
from .install import CodexInstallResult, install_codex
from .thread import Thread
from .types import CodexOptions, ThreadOptions


class Codex:
    """Main entry-point for interacting with the Codex agent."""

    def __init__(
        self, options: Union[CodexOptions, dict[str, Any], None] = None
    ) -> None:
        self._options = CodexOptions.model_validate(options or {})
        self._exec = CodexExec(self._options.codex_path_override, self._options.env)

    def start_thread(
        self, options: Union[ThreadOptions, dict[str, Any], None] = None
    ) -> Thread:
        """Start a new conversation (thread) with an agent."""
        thread_options = ThreadOptions.model_validate(options or {})
        return Thread(self._exec, self._options, thread_options, thread_id=None)

    def resume_thread(
        self,
        thread_id: str,
        options: Union[ThreadOptions, dict[str, Any], None] = None,
    ) -> Thread:
        """Resume a previously started thread by id."""
        thread_options = ThreadOptions.model_validate(options or {})
        return Thread(self._exec, self._options, thread_options, thread_id=thread_id)

    # Aliases for TypeScript parity
    def startThread(
        self, options: Union[ThreadOptions, dict[str, Any], None] = None
    ) -> Thread:
        return self.start_thread(options)

    def resumeThread(
        self,
        thread_id: str,
        options: Union[ThreadOptions, dict[str, Any], None] = None,
    ) -> Thread:
        return self.resume_thread(thread_id, options)

    @staticmethod
    def install(
        *,
        version: str,
        install_dir: Optional[str] = None,
        base_url: str = "https://github.com/openai/codex/releases/download",
        filename: Optional[str] = None,
        sha256: Optional[str] = None,
        overwrite: bool = False,
    ) -> CodexInstallResult:
        """Download and install the Codex CLI binary for the current platform."""

        return install_codex(
            version=version,
            install_dir=install_dir,
            base_url=base_url,
            filename=filename,
            sha256=sha256,
            overwrite=overwrite,
        )

    @staticmethod
    def login_with_auth_json(
        *,
        auth_json: Optional[str] = None,
        env_var: str = "CODEX_AUTH_JSON",
        path: Optional[str] = None,
        overwrite: bool = False,
        mode: int = 0o600,
    ) -> str:
        """Write the Codex CLI auth.json file.

        Intended for notebook/container environments where you store an auth JSON
        blob in a secret (for example Modal's secrets).
        """

        return login_with_auth_json(
            auth_json=auth_json,
            env_var=env_var,
            path=path,
            overwrite=overwrite,
            mode=mode,
        )

    def login_with_device_code(self) -> int:
        """Start Codex device auth login flow and stream output to stdout."""
        return login_with_device_code(
            executable_path=self._exec.executable_path,
            env=self._exec._build_env(self._exec_args_for_login()),
        )

    def _exec_args_for_login(self) -> CodexExecArgs:
        return CodexExecArgs(
            input="",
            base_url=self._options.base_url,
            api_key=self._options.api_key,
        )

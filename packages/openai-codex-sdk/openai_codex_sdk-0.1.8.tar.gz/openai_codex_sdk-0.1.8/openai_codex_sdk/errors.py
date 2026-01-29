from __future__ import annotations


class CodexSdkError(Exception):
    """Base error for the SDK."""


class ThreadRunError(CodexSdkError):
    """Raised when the Codex CLI reports a `turn.failed` event."""


class EventParseError(CodexSdkError):
    """Raised when a JSONL line cannot be parsed into a ThreadEvent."""


class CodexExecError(CodexSdkError):
    """Raised when the codex CLI process exits unsuccessfully."""


class CodexInstallError(CodexSdkError):
    """Raised when installing the codex CLI binary fails."""


class CodexAuthError(CodexSdkError):
    """Raised when installing or reading Codex auth.json fails."""

# OpenAI Codex SDK (Python)

Embed the Codex agent in your workflows and apps.

This SDK wraps the bundled `codex` binary. It spawns the CLI and exchanges JSONL events over stdin/stdout.

## Installation

```bash
pip install openai-codex-sdk
```

Requires Python 3.10+.

## Installing the Codex CLI binary (notebooks/containers)

This package does **not** ship the `codex` binary by default. In environments like notebooks or containers,
install it explicitly:

```python
from openai_codex_sdk import Codex

# Downloads a Codex CLI release asset and installs into:
#   openai_codex_sdk/vendor/<target-triple>/codex/<codex|codex.exe>
Codex.install(version="rust-v0.88.0-alpha.3")

# If you hit glibc compatibility issues in containers, prefer the musl build:
# Codex.install(
#   version="rust-v0.88.0-alpha.3",
#   filename="codex-x86_64-unknown-linux-musl.tar.gz",
#   overwrite=True,
# )
```

## Writing auth.json (notebooks/containers)

If your environment provides the Codex CLI credentials as a secret (for example an env var containing the JSON
string), write the auth file the Codex CLI expects at `~/.codex/auth.json`:

```python
from openai_codex_sdk import Codex

# Reads from CODEX_AUTH_JSON by default
Codex.write_auth_json(overwrite=True)
```

Alternatively, install `codex` separately and ensure it is on `PATH`, or set `codex_path_override`:

```python
from openai_codex_sdk import Codex

codex = Codex({"codex_path_override": "/path/to/codex"})
```

## Quickstart

```python
import asyncio
from openai_codex_sdk import Codex

async def main():
    codex = Codex()
    thread = codex.start_thread()
    turn = await thread.run("Diagnose the test failure and propose a fix")

    print(turn.final_response)
    print(turn.items)

    next_turn = await thread.run("Implement the fix")
    print(next_turn.final_response)

asyncio.run(main())
```

## Streaming responses

`run()` buffers events until the turn finishes. To react to intermediate progress—tool calls, streaming responses,
and file change notifications—use `run_streamed()` instead.

```python
import asyncio
from openai_codex_sdk import Codex

async def main():
    codex = Codex()
    thread = codex.start_thread()

    streamed = await thread.run_streamed("Diagnose the test failure and propose a fix")
    async for event in streamed.events:
        if event.type == "item.completed":
            print("item", event.item)
        elif event.type == "turn.completed":
            print("usage", event.usage)

asyncio.run(main())
```

## Structured output

Provide `output_schema` on each turn as a JSON schema (a plain JSON object / Python `dict`):

```python
import asyncio
from openai_codex_sdk import Codex

schema = {
    "type": "object",
    "properties": {
        "summary": { "type": "string" },
        "status": { "type": "string", "enum": ["ok", "action_required"] }
    },
    "required": ["summary", "status"],
    "additionalProperties": False
}

async def main():
    codex = Codex()
    thread = codex.start_thread()
    turn = await thread.run("Summarize repository status", {"output_schema": schema})
    print(turn.final_response)

asyncio.run(main())
```

## Attaching images

Provide structured input entries when you need to include images alongside text. Text entries are concatenated into
the final prompt while image entries are passed to the Codex CLI via `--image`.

```python
turn = await thread.run([
    {"type": "text", "text": "Describe these screenshots"},
    {"type": "local_image", "path": "./ui.png"},
    {"type": "local_image", "path": "./diagram.jpg"},
])
```

## Resuming an existing thread

Threads are persisted in `~/.codex/sessions`. If you lose the in-memory `Thread` object, reconstruct it with
`resume_thread()` and keep going.

```python
saved_thread_id = os.environ["CODEX_THREAD_ID"]
thread = codex.resume_thread(saved_thread_id)
await thread.run("Implement the fix")
```

## Working directory controls

Codex runs in the current working directory by default. To avoid unrecoverable errors, Codex requires the working
directory to be a Git repository. You can skip the Git repository check by passing `skip_git_repo_check=True`.

```python
thread = codex.start_thread({
    "working_directory": "/path/to/project",
    "skip_git_repo_check": True,
})
```

## Controlling the Codex CLI environment

By default, the Codex CLI inherits the Python process environment. Provide `env` when instantiating `Codex` to fully
control which variables the CLI receives.

```python
codex = Codex({
    "env": {
        "PATH": "/usr/local/bin",
    },
})
```

The SDK still injects required variables (such as `OPENAI_BASE_URL` and `CODEX_API_KEY`) on top of the environment
you provide.

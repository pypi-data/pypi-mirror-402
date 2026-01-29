# ollama-serve

Keep your local Ollama server warm and your favorite models ready. This package
offers small, composable helpers to check server health, start it when needed,
and pull models on demand.

## Install

```bash
uv add ollama-serve
```

## Quick start

```python
from ollama_serve import ensure_model_and_server_ready

if ensure_model_and_server_ready("llama3:latest"):
    print("Ready to chat.")
```

## Common flows

```python
from ollama_serve import (
    is_ollama_running,
    run_ollama_server,
    is_model_installed,
    install_model,
)

is_ollama_running()
run_ollama_server()
is_model_installed("llama3:latest")
install_model("llama3:latest")
```

## Tips

- If Ollama is not on your PATH, install it from https://ollama.com/download.
- Use smaller timeout values for snappier "is it up?" checks in dev loops.

## Compatibility

- macOS, Linux, and Windows (where Ollama runs locally).
- Requires the `ollama` CLI on your PATH.

## Logging and config

- Uses standard Python logging via `logging.getLogger("ollama_serve")`.
- Default settings can be overridden with env vars:
  - `OLLAMA_SERVE_TIMEOUT` (seconds, default `0.2`)
  - `OLLAMA_SERVE_RETRIES` (default `1`)
  - `OLLAMA_SERVE_RETRY_DELAY` (seconds, default `0.2`)

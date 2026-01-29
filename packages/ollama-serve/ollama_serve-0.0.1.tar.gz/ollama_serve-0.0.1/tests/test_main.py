"""
Tests for the main module.
"""

import contextlib
import http.client
import os
import shutil
import subprocess
import time

import pytest

from ollama_serve.main import (
    ensure_model_and_server_ready,
    install_model,
    is_model_installed,
    is_ollama_running,
    run_ollama_server,
)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("ok", True),
        ("error", False),
    ],
)
def test_is_ollama_running(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    expected: bool,
) -> None:
    """
    Return the expected result for healthy and failing connections.
    """

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return b'{"models": []}'

    class FakeConnection:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout

        def request(self, method: str, path: str) -> None:
            assert method == "GET"
            assert path == "/api/tags"
            if mode == "error":
                raise OSError("connection failed")

        def getresponse(self) -> FakeResponse:
            return FakeResponse()

        def close(self) -> None:
            return None

    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    assert is_ollama_running() is expected


@pytest.mark.parametrize(
    ("payload", "model", "expected"),
    [
        (b'{"models":[{"name":"llama3:latest"}]}', "llama3:latest", True),
        (b'{"models":[{"name":"llama3:latest"}]}', "phi4:latest", False),
        (b'{"models":[]}', "llama3:latest", False),
        (b'{"models":[{"name":"llama3:latest"}]}', "llama3", False),
    ],
)
def test_is_model_installed(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    model: str,
    expected: bool,
) -> None:
    """
    Return expected results based on the tags response payload.
    """

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return payload

    class FakeConnection:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout

        def request(self, method: str, path: str) -> None:
            assert method == "GET"
            assert path == "/api/tags"

        def getresponse(self) -> FakeResponse:
            return FakeResponse()

        def close(self) -> None:
            return None

    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    assert is_model_installed(model) is expected


@pytest.mark.parametrize(
    ("mode", "payload", "expected"),
    [
        ("oserror", b'{"models":[{"name":"llama3:latest"}]}', False),
        ("badjson", b"not-json", False),
    ],
)
def test_is_model_installed_errors(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    payload: bytes,
    expected: bool,
) -> None:
    """
    Return False when the request fails or the response is invalid.
    """

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return payload

    class FakeConnection:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout

        def request(self, method: str, path: str) -> None:
            if mode == "oserror":
                raise OSError("connection failed")

        def getresponse(self) -> FakeResponse:
            return FakeResponse()

        def close(self) -> None:
            return None

    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    assert is_model_installed("llama3:latest") is expected


@pytest.mark.parametrize(
    (
        "installed_states",
        "server_running",
        "pull_error",
        "expected",
        "pull_calls",
    ),
    [
        ([True], True, None, True, 0),
        ([False], False, None, False, 0),
        ([False, True], True, None, True, 1),
        ([False, False], True, None, False, 1),
        ([False], True, subprocess.CalledProcessError(1, ["ollama"]), False, 1),
    ],
)
def test_install_model(
    monkeypatch: pytest.MonkeyPatch,
    installed_states: list[bool],
    server_running: bool,
    pull_error: Exception | None,
    expected: bool,
    pull_calls: int,
) -> None:
    """
    Return expected results for already installed, install, and failure cases.
    """

    model = "llama3:latest"
    states = iter(installed_states)
    calls: list[list[str]] = []

    def fake_is_installed(*_: object, **__: object) -> bool:
        return next(states)

    def fake_run(args: list[str], **_: object) -> None:
        calls.append(args)
        if pull_error is not None:
            raise pull_error

    monkeypatch.setattr("ollama_serve.main.is_model_installed", fake_is_installed)
    monkeypatch.setattr(
        "ollama_serve.main.run_ollama_server", lambda **_: server_running
    )
    monkeypatch.setattr("ollama_serve.main.subprocess.run", fake_run)

    assert install_model(model) is expected
    assert len(calls) == pull_calls


@pytest.mark.parametrize(
    (
        "server_running",
        "installed",
        "install_result",
        "expected",
        "install_calls",
    ),
    [
        (False, False, False, False, 0),
        (True, True, False, True, 0),
        (True, False, True, True, 1),
        (True, False, False, False, 1),
    ],
)
def test_ensure_model_and_server_ready(
    monkeypatch: pytest.MonkeyPatch,
    server_running: bool,
    installed: bool,
    install_result: bool,
    expected: bool,
    install_calls: int,
) -> None:
    """
    Return expected results for server and model readiness combinations.
    """

    calls: list[str] = []
    model = "llama3:latest"

    monkeypatch.setattr(
        "ollama_serve.main.run_ollama_server", lambda **_: server_running
    )
    monkeypatch.setattr(
        "ollama_serve.main.is_model_installed", lambda *_args, **_kwargs: installed
    )

    def fake_install(*_: object, **__: object) -> bool:
        calls.append("install")
        return install_result

    monkeypatch.setattr("ollama_serve.main.install_model", fake_install)

    assert ensure_model_and_server_ready(model) is expected
    assert len(calls) == install_calls


@pytest.mark.parametrize(
    ("is_running_states", "which_result", "expected", "warns", "popen_calls"),
    [
        ([False], None, False, True, []),
        ([True], "/usr/local/bin/ollama", True, False, []),
        ([False, True], "/usr/local/bin/ollama", True, False, [["ollama", "serve"]]),
    ],
)
def test_run_ollama_server(
    monkeypatch: pytest.MonkeyPatch,
    is_running_states: list[bool],
    which_result: str | None,
    expected: bool,
    warns: bool,
    popen_calls: list[list[str]],
) -> None:
    """
    Return expected results for missing or start-required cases.
    """

    calls: list[list[str]] = []
    running_states = iter(is_running_states)

    def fake_is_running(**_: float) -> bool:
        return next(running_states)

    def fake_popen(args: list[str], **_: object) -> None:
        calls.append(args)

    monkeypatch.setattr("ollama_serve.main.is_ollama_running", fake_is_running)
    monkeypatch.setattr("ollama_serve.main.shutil.which", lambda _: which_result)
    monkeypatch.setattr("ollama_serve.main.subprocess.Popen", fake_popen)

    warn_ctx: contextlib.AbstractContextManager[object]
    if warns:
        warn_ctx = pytest.warns(
            UserWarning, match="Ollama does not appear to be installed"
        )
    else:
        warn_ctx = contextlib.nullcontext()

    with warn_ctx:
        assert run_ollama_server() is expected

    assert calls == popen_calls


@pytest.mark.integration
def test_run_ollama_server_integration() -> None:
    """
    Exercise run_ollama_server against a real Ollama installation.
    """

    if shutil.which("ollama") is None:
        pytest.skip("ollama is not installed on PATH")

    already_running = is_ollama_running()
    if not already_running and os.getenv("OLLAMA_TEST_START_SERVER") != "1":
        pytest.skip("set OLLAMA_TEST_START_SERVER=1 to allow starting ollama")

    assert run_ollama_server() is True

    if not already_running:
        deadline = time.time() + 5.0
        while time.time() < deadline and not is_ollama_running():
            time.sleep(0.2)
        assert is_ollama_running() is True

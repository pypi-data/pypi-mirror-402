"""Shared utilities and cross-cutting tests for CLI testing.

This module provides:
- DummyClient, DummyResponse, DummyResult: Mock objects for testing without real API calls
- _patch_dummy_client(): Helper to patch the CLI to use DummyClient
- Cross-cutting tests (system, generic API) that don't fit in domain-specific test files

Domain-specific tests are organized in separate files:
- test_cli_species.py: Species endpoints
- test_cli_genomes.py: Genome endpoints
- test_cli_genes.py: Gene endpoints
- test_cli_experimental.py: Experimental APIs (drugs, PPI, orthologs, operons, fitness, etc.)
"""

from __future__ import annotations

import json
from typing import Any, Callable

from click.testing import CliRunner
from typer.main import get_command

from mett_dataportal.cli.main import app as cli_app


class DummyResponse:
    """Minimal HTTP-like response object for handle_raw_response."""

    def __init__(self, payload: Any | None = None) -> None:
        if payload is None:
            payload = {"ok": True}
        self._payload = payload
        self.headers = {"Content-Type": "application/json"}
        self.text = json.dumps(self._payload)

    def json(self) -> Any:  # pragma: no cover - trivial
        return self._payload


class DummyResult:
    """Result object for high-level client methods (with items/raw)."""

    def __init__(self, payload: Any | None = None) -> None:
        if payload is None:
            payload = [{"ok": True}]
        self.items = payload
        self.raw = {"data": payload}


class DummyClient:
    """Generic stand‑in for DataPortalClient.

    - raw_request(...) -> DummyResponse
    - Any other attribute call (e.g., list_genomes, search_genomes, etc.)
      returns a DummyResult so CLI pagination/printing logic works.
    """

    def raw_request(self, *args: Any, **kwargs: Any) -> DummyResponse:
        return DummyResponse()

    def __getattr__(self, _name: str) -> Callable[..., DummyResult]:
        def _method(*_args: Any, **_kwargs: Any) -> DummyResult:
            return DummyResult()

        return _method


runner = CliRunner()
cli_cmd = get_command(cli_app)


def _patch_dummy_client(monkeypatch) -> None:
    """Patch CLI to always use DummyClient instead of real HTTP client."""

    from mett_dataportal import cli as cli_pkg
    from mett_dataportal.cli import main as main_module
    from mett_dataportal.cli import utils as cli_utils

    dummy = DummyClient()

    # Callback in main.py uses _build_client → patch it
    monkeypatch.setattr(main_module, "_build_client", lambda **_: dummy)

    # Safety: ensure_client(ctx) should also fall back to DummyClient
    def _ensure_client(ctx):
        if ctx.obj is None:
            ctx.obj = dummy
        return ctx.obj

    monkeypatch.setattr(cli_utils, "ensure_client", _ensure_client)

    # Also make the package-level default (if ever used) point to DummyClient
    if hasattr(cli_pkg, "DEFAULT_CLIENT"):
        monkeypatch.setattr(cli_pkg, "DEFAULT_CLIENT", dummy)


# Cross-cutting tests (system, generic API, etc.)
# Domain-specific tests are in test_cli_*.py files


def test_system_health(monkeypatch) -> None:
    """Friendly CLI: mett system health --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["system", "health", "--format", "json"])
    assert result.exit_code == 0


def test_api_request_generic(monkeypatch) -> None:
    """Generic CLI: mett api request GET /api/species/ --format json"""
    _patch_dummy_client(monkeypatch)
    args = ["api", "request", "GET", "/api/species/", "--format", "json"]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0

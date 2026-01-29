from __future__ import annotations

from click.testing import CliRunner
from typer.main import get_command

from mett_dataportal.cli.main import app as cli_app
from .test_cli import _patch_dummy_client


runner = CliRunner()
cli_cmd = get_command(cli_app)


def test_genomes_list(monkeypatch) -> None:
    """Friendly CLI: mett genomes list --page 1 --per-page 5 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        ["genomes", "list", "--page", "1", "--per-page", "5", "--format", "json"],
    )
    assert result.exit_code == 0


def test_genomes_search_query(monkeypatch) -> None:
    """Friendly CLI: mett genomes search --query PV_H4 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd, ["genomes", "search", "--query", "PV_H4", "--format", "json"]
    )
    assert result.exit_code == 0


def test_genomes_search_iso_species_query(monkeypatch) -> None:
    """Friendly CLI: mett genomes search --query 909 --species BU --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        ["genomes", "search", "--query", "909", "--species", "BU", "--format", "json"],
    )
    assert result.exit_code == 0


def test_genomes_type_strains(monkeypatch) -> None:
    """Friendly CLI: mett genomes type-strains --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["genomes", "type-strains", "--format", "json"])
    assert result.exit_code == 0


def test_genomes_autocomplete(monkeypatch) -> None:
    """Friendly CLI: mett genomes autocomplete --query cc --limit 5 --format json"""
    _patch_dummy_client(monkeypatch)
    args = [
        "genomes",
        "autocomplete",
        "--query",
        "cc",
        "--limit",
        "5",
        "--format",
        "json",
    ]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0


def test_genomes_by_isolates(monkeypatch) -> None:
    """Friendly CLI: mett genomes by-isolates --isolate BU_ATCC8492 --isolate PV_ATCC8482 --format json"""
    _patch_dummy_client(monkeypatch)
    args = [
        "genomes",
        "by-isolates",
        "--isolate",
        "BU_ATCC8492",
        "--isolate",
        "PV_ATCC8482",
        "--format",
        "json",
    ]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0

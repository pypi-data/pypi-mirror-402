from __future__ import annotations

from click.testing import CliRunner
from typer.main import get_command

from mett_dataportal.cli.main import app as cli_app
from .test_cli import _patch_dummy_client


runner = CliRunner()
cli_cmd = get_command(cli_app)


def test_species_list(monkeypatch) -> None:
    """Friendly CLI: mett species list --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["species", "list", "--format", "json"])
    assert result.exit_code == 0


def test_species_genomes_basic(monkeypatch) -> None:
    """Friendly CLI: mett species genomes bu --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["species", "genomes", "bu", "--format", "json"])
    assert result.exit_code == 0


def test_species_genomes_with_query(monkeypatch) -> None:
    """Friendly CLI: mett species genomes bu --query BU_ATCC --page 1 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "species",
            "genomes",
            "bu",
            "--query",
            "BU_ATCC",
            "--page",
            "1",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0

from __future__ import annotations

from click.testing import CliRunner
from typer.main import get_command

from mett_dataportal.cli.main import app as cli_app
from .test_cli import _patch_dummy_client


runner = CliRunner()
cli_cmd = get_command(cli_app)


def test_genes_list(monkeypatch) -> None:
    """Friendly CLI: mett genes list --page 1 --per-page 10 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        ["genes", "list", "--page", "1", "--per-page", "10", "--format", "json"],
    )
    assert result.exit_code == 0


def test_genes_search_basic(monkeypatch) -> None:
    """Friendly CLI: mett genes search --query dnaA --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd, ["genes", "search", "--query", "dnaA", "--format", "json"]
    )
    assert result.exit_code == 0


def test_genes_faceted_search_species_pfam(monkeypatch) -> None:
    """Friendly CLI: mett genes faceted-search --species BU --limit 10 --pfam PF07660,PF07715 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "genes",
            "faceted-search",
            "--species",
            "BU",
            "--limit",
            "10",
            "--pfam",
            "PF07660,PF07715",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_genes_autocomplete_species_query(monkeypatch) -> None:
    """Friendly CLI: mett genes autocomplete --species BU --query dnaA --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "genes",
            "autocomplete",
            "--species",
            "BU",
            "--query",
            "dnaA",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_genes_search_advanced_locus_tag(monkeypatch) -> None:
    """Friendly CLI: mett genes search-advanced --locus-tag BU_ATCC8492_00001 --per-page 1 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "genes",
            "search-advanced",
            "--locus-tag",
            "BU_ATCC8492_00001",
            "--per-page",
            "1",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0

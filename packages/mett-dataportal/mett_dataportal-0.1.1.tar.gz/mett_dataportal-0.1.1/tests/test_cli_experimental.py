from __future__ import annotations

from click.testing import CliRunner
from typer.main import get_command

from mett_dataportal.cli.main import app as cli_app
from .test_cli import _patch_dummy_client


runner = CliRunner()
cli_cmd = get_command(cli_app)


def test_drugs_mic_by_drug(monkeypatch) -> None:
    """Friendly CLI: mett drugs mic-by-drug azithromycin --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd, ["drugs", "mic-by-drug", "azithromycin", "--format", "json"]
    )
    assert result.exit_code == 0


def test_drugs_metabolism_search_query(monkeypatch) -> None:
    """Friendly CLI: mett drugs metabolism-search --query amoxapine --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        ["drugs", "metabolism-search", "--query", "amoxapine", "--format", "json"],
    )
    assert result.exit_code == 0


def test_ppi_scores_available(monkeypatch) -> None:
    """Friendly CLI: mett ppi scores --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["ppi", "scores", "--format", "json"])
    assert result.exit_code == 0


def test_ppi_network_properties_ds_score(monkeypatch) -> None:
    """Friendly CLI: mett ppi network-properties --score-type ds_score --score-threshold 0.8 --species PV --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "ppi",
            "network-properties",
            "--score-type",
            "ds_score",
            "--score-threshold",
            "0.8",
            "--species",
            "PV",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_orthologs_pair(monkeypatch) -> None:
    """Friendly CLI: mett orthologs pair --gene-a BU_ATCC8492_00001 --gene-b PV_ATCC8482_00001 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "orthologs",
            "pair",
            "--gene-a",
            "BU_ATCC8492_00001",
            "--gene-b",
            "PV_ATCC8482_00001",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_operons_search_min_genes(monkeypatch) -> None:
    """Friendly CLI: mett operons search --min-genes 2 --format json

    Note: we intentionally omit the boolean flags here (--has-tss/--has-terminator)
    to avoid depending on Click's boolean parsing details. The goal of this test
    is to exercise the command wiring and parameter plumbing, not every flag combo.
    """
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "operons",
            "search",
            "--min-genes",
            "2",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_operons_statistics_species(monkeypatch) -> None:
    """Friendly CLI: mett operons statistics --species BU --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd, ["operons", "statistics", "--species", "BU", "--format", "json"]
    )
    assert result.exit_code == 0


def test_fitness_search_locus_tag(monkeypatch) -> None:
    """Friendly CLI: mett fitness search --locus-tag BU_ATCC8492_00002 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        ["fitness", "search", "--locus-tag", "BU_ATCC8492_00002", "--format", "json"],
    )
    assert result.exit_code == 0


def test_fitness_correlations_search(monkeypatch) -> None:
    """Friendly CLI: mett fitness-correlations search --query \"Vitamin B12\" --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "fitness-correlations",
            "search",
            "--query",
            "Vitamin B12",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_fitness_correlations_pair(monkeypatch) -> None:
    """Friendly CLI: mett fitness-correlations correlation --locus-tag-a BU_ATCC8492_02530 --locus-tag-b BU_ATCC8492_02762 --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(
        cli_cmd,
        [
            "fitness-correlations",
            "pair",
            "--gene-a",
            "BU_ATCC8492_02530",
            "--gene-b",
            "BU_ATCC8492_02762",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0


def test_drugs_mic_filters(monkeypatch) -> None:
    """Friendly CLI: mett drugs mic --drug-name amoxicillin --species BU --min-mic-value 35.0 --max-mic-value 45.0 --format json"""
    _patch_dummy_client(monkeypatch)
    args = [
        "drugs",
        "mic",
        "--drug-name",
        "amoxicillin",
        "--species",
        "BU",
        "--min-mic-value",
        "35.0",
        "--max-mic-value",
        "45.0",
        "--format",
        "json",
    ]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0


def test_ppi_interactions(monkeypatch) -> None:
    """Friendly CLI: mett ppi interactions --locus-tag BU_ATCC8492_01788 --species BU --per-page 3 --format json"""
    _patch_dummy_client(monkeypatch)
    args = [
        "ppi",
        "interactions",
        "--locus-tag",
        "BU_ATCC8492_01788",
        "--species",
        "BU",
        "--per-page",
        "3",
        "--format",
        "json",
    ]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0


def test_ttp_hits(monkeypatch) -> None:
    """Friendly CLI: mett ttp hits --max-fdr 0.05 --min-ttp-score 1.0 --format json"""
    _patch_dummy_client(monkeypatch)
    args = [
        "ttp",
        "hits",
        "--max-fdr",
        "0.05",
        "--min-ttp-score",
        "1.0",
        "--format",
        "json",
    ]
    result = runner.invoke(cli_cmd, args)
    assert result.exit_code == 0


def test_pyhmmer_databases(monkeypatch) -> None:
    """Friendly CLI: mett pyhmmer databases --format json"""
    _patch_dummy_client(monkeypatch)
    result = runner.invoke(cli_cmd, ["pyhmmer", "databases", "--format", "json"])
    assert result.exit_code == 0

from __future__ import annotations

import os
from pathlib import Path

import typer

from tracetree.core import (
    aggregate_reports,
    init_traceability,
    link_test_ids,
    load_config,
    validate_repo,
    write_aggregate_report,
    write_iec62304_report,
    write_link_report,
    write_validate_report,
)


def coverage_default() -> float:
    return float(
        os.environ.get("TRACEABILITY_REQ_COVERAGE")
        or os.environ.get("DATA_BRIDGE_REQ_COVERAGE")
        or "1.0"
    )


app = typer.Typer(help="Universal traceability tooling (validate/link/aggregate).")


@app.command("validate")
def run_validate(
    repo: str = typer.Option(
        ".", "--repo", help="Repository root (defaults to current working directory)."
    ),
    coverage_threshold: float = typer.Option(
        coverage_default(),
        "--coverage-threshold",
        help="Minimum requirements coverage ratio (0-1).",
    ),
) -> None:
    repo_root = Path(repo).resolve()
    config = load_config(repo_root)
    report = validate_repo(config, coverage_threshold)
    write_validate_report(config, report)
    write_iec62304_report(config)
    if report["errors"]:
        typer.echo("Traceability validation failed.")
        for err in report["errors"]:
            typer.echo(f"- {err}")
        raise typer.Exit(code=1)
    typer.echo("Traceability validation passed.")
    if report["warnings"]:
        for warn in report["warnings"]:
            typer.echo(f"- {warn}")


@app.command("link")
def run_link(
    repo: str = typer.Option(
        ".", "--repo", help="Repository root (defaults to current working directory)."
    ),
) -> None:
    repo_root = Path(repo).resolve()
    config = load_config(repo_root)
    report = link_test_ids(config)
    write_link_report(config, report)
    typer.echo("TestID linking complete.")


@app.command("aggregate")
def run_aggregate(
    repo: str = typer.Option(
        ".", "--repo", help="Repository root (defaults to current working directory)."
    ),
    coverage_threshold: float = typer.Option(
        coverage_default(),
        "--coverage-threshold",
        help="Minimum requirements coverage ratio (0-1).",
    ),
) -> None:
    repo_root = Path(repo).resolve()
    aggregate = aggregate_reports(repo_root, coverage_threshold)
    config = load_config(repo_root)
    write_aggregate_report(config.output_dir, aggregate)
    failed = any(entry.get("status") == "failed" for entry in aggregate["results"])
    if failed:
        typer.echo("Traceability rollup failed.")
        raise typer.Exit(code=1)
    typer.echo("Traceability rollup complete.")


@app.command("init")
def run_init(
    repo: str = typer.Option(
        ".", "--repo", help="Repository root (defaults to current working directory)."
    ),
) -> None:
    repo_root = Path(repo).resolve()
    config = load_config(repo_root)
    report = init_traceability(config)
    created = report["created"]
    skipped = report["skipped"]
    typer.echo(f"Initialized traceability in {report['trace_dir']}.")
    typer.echo(f"Generated reports will be written to {report['output_dir']}.")
    if created:
        typer.echo("Created:")
        for path in created:
            typer.echo(f"- {path}")
    if skipped:
        typer.echo("Skipped existing:")
        for path in skipped:
            typer.echo(f"- {path}")


def main() -> int:
    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .core import (
    aggregate_reports,
    init_traceability,
    link_test_ids,
    load_config,
    validate_repo,
    write_aggregate_report,
    write_link_report,
    write_validate_report,
)


def run_validate(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    config = load_config(repo_root)
    report = validate_repo(config, args.coverage_threshold)
    write_validate_report(config, report)
    if report["errors"]:
        print("Traceability validation failed.")
        for err in report["errors"]:
            print(f"- {err}")
        return 1
    print("Traceability validation passed.")
    if report["warnings"]:
        for warn in report["warnings"]:
            print(f"- {warn}")
    return 0


def run_link(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    config = load_config(repo_root)
    report = link_test_ids(config)
    write_link_report(config, report)
    print("TestID linking complete.")
    return 0


def run_aggregate(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    aggregate = aggregate_reports(repo_root, args.coverage_threshold)
    config = load_config(repo_root)
    write_aggregate_report(config.trace_dir, aggregate)
    failed = any(entry.get("status") == "failed" for entry in aggregate["results"])
    if failed:
        print("Traceability rollup failed.")
        return 1
    print("Traceability rollup complete.")
    return 0


def run_init(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    config = load_config(repo_root)
    report = init_traceability(config)
    created = report["created"]
    skipped = report["skipped"]
    print(f"Initialized traceability in {report['trace_dir']}.")
    if created:
        print("Created:")
        for path in created:
            print(f"- {path}")
    if skipped:
        print("Skipped existing:")
        for path in skipped:
            print(f"- {path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Universal traceability tooling (validate/link/aggregate)."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository root (defaults to current working directory).",
    )
    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=float(
            os.environ.get("TRACEABILITY_REQ_COVERAGE")
            or os.environ.get("DATA_BRIDGE_REQ_COVERAGE")
            or "1.0"
        ),
        help="Minimum requirements coverage ratio (0-1).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Validate requirements/matrix coverage.")
    subparsers.add_parser("link", help="Link TestIDs to test definitions.")
    subparsers.add_parser("aggregate", help="Aggregate across submodules.")
    subparsers.add_parser("init", help="Create starter traceability files.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "validate":
        return run_validate(args)
    if args.command == "link":
        return run_link(args)
    if args.command == "aggregate":
        return run_aggregate(args)
    if args.command == "init":
        return run_init(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

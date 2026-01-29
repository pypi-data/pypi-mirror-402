from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REQ_RE = re.compile(r"^(REQ-[A-Z0-9-]+):")
RC_RE = re.compile(r"^(RC-[A-Z0-9-]+):")
GTEST_RE = re.compile(r"TEST(?:_F)?\s*\(\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s*\)")
PYTEST_RE = re.compile(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(")
JS_TEST_RE = re.compile(r"\b(?:test|it)\s*(?:\.\w+)?\s*\(\s*([\"'`])(.+?)\1")
RUST_TEST_ATTR_RE = re.compile(r"^\s*#\[\s*([A-Za-z0-9_:]+::)?test")
RUST_FN_RE = re.compile(r"^\s*(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\(")


@dataclass
class TraceConfig:
    repo_root: Path
    trace_dir: Path
    requirements: Path
    risk_controls: Path
    matrix: Path
    gtest_roots: list[Path]
    pytest_roots: list[Path]
    js_roots: list[Path]
    rust_roots: list[Path]


def load_config(repo_root: Path) -> TraceConfig:
    config_path = os.environ.get("TRACEABILITY_CONFIG")
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = repo_root / ".traceability" / "config.json"

    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))

    trace_dir = repo_root / config.get("traceability_dir", "docs/traceability")

    def resolve_trace_path(key: str, default_name: str) -> Path:
        value = config.get(key, default_name)
        path = Path(value)
        if path.is_absolute():
            return path
        return trace_dir / value

    requirements = resolve_trace_path("requirements_file", "requirements.md")
    risk_controls = resolve_trace_path("risk_controls_file", "risk_controls.md")
    matrix = resolve_trace_path("matrix_file", "traceability_matrix.csv")

    gtest_roots = [repo_root / p for p in config.get("gtest_roots", ["tests", "test"])]
    pytest_roots = [
        repo_root / p for p in config.get("pytest_roots", ["tests", "test"])
    ]
    js_roots = [
        repo_root / p
        for p in config.get("js_roots", ["tests", "test", "__tests__", "spec"])
    ]
    rust_roots = [
        repo_root / p for p in config.get("rust_roots", ["tests", "test", "src"])
    ]

    return TraceConfig(
        repo_root=repo_root,
        trace_dir=trace_dir,
        requirements=requirements,
        risk_controls=risk_controls,
        matrix=matrix,
        gtest_roots=gtest_roots,
        pytest_roots=pytest_roots,
        js_roots=js_roots,
        rust_roots=rust_roots,
    )


def load_ids(path: Path, pattern: re.Pattern[str]) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            ids.add(match.group(1))
    return ids


def parse_matrix(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def read_text_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def validate_repo(config: TraceConfig, coverage_threshold: float) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if (
        not config.requirements.exists()
        and not config.risk_controls.exists()
        and not config.matrix.exists()
    ):
        errors.append(
            "Traceability not initialized. Run `tracetree init` or create files in "
            f"{config.trace_dir}."
        )

    requirements = load_ids(config.requirements, REQ_RE)
    risk_controls = load_ids(config.risk_controls, RC_RE)
    matrix_rows = parse_matrix(config.matrix)

    if not requirements:
        errors.append(f"No requirements found in {config.requirements}")
    if not risk_controls:
        errors.append(f"No risk controls found in {config.risk_controls}")
    if not config.matrix.exists():
        errors.append(f"Missing {config.matrix}")
    if not matrix_rows:
        errors.append("Traceability matrix is empty")

    referenced_reqs: set[str] = set()
    referenced_controls: set[str] = set()

    for idx, row in enumerate(matrix_rows, start=1):
        req_id = row.get("RequirementID", "")
        rc_id = row.get("RiskControlID", "")
        test_location = row.get("TestLocation", "")

        if not req_id:
            errors.append(f"Row {idx}: RequirementID is empty")
        elif req_id not in requirements:
            errors.append(f"Row {idx}: RequirementID {req_id} not in requirements")
        else:
            referenced_reqs.add(req_id)

        if rc_id:
            if rc_id not in risk_controls:
                errors.append(f"Row {idx}: RiskControlID {rc_id} not in risk controls")
            else:
                referenced_controls.add(rc_id)
        else:
            warnings.append(f"Row {idx}: RiskControlID is empty")

        if test_location:
            test_path = config.repo_root / test_location
            if not test_path.exists():
                errors.append(f"Row {idx}: TestLocation not found: {test_location}")
        else:
            warnings.append(f"Row {idx}: TestLocation is empty")

    missing_reqs = sorted(requirements - referenced_reqs)
    if missing_reqs:
        errors.append("Requirements missing from matrix: " + ", ".join(missing_reqs))

    coverage_ratio = len(referenced_reqs) / len(requirements) if requirements else 0.0
    if coverage_ratio < coverage_threshold:
        errors.append(
            f"Requirements coverage {coverage_ratio:.2%} below threshold "
            f"{coverage_threshold:.2%}"
        )

    report = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "requirements_total": len(requirements),
        "risk_controls_total": len(risk_controls),
        "matrix_rows": len(matrix_rows),
        "requirements_covered": len(referenced_reqs),
        "coverage_ratio": coverage_ratio,
        "coverage_threshold": coverage_threshold,
        "errors": errors,
        "warnings": warnings,
    }
    return report


def index_gtest_tests(config: TraceConfig) -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    exts = (".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".h")
    for root in config.gtest_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in exts:
                continue
            for idx, line in enumerate(read_text_lines(path), 1):
                match = GTEST_RE.search(line)
                if match:
                    name = f"{match.group(1)}.{match.group(2)}"
                    rel = str(path.relative_to(config.repo_root))
                    index.setdefault(name, (rel, idx))
    return index


def index_pytest_tests(config: TraceConfig) -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    for root in config.pytest_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            for idx, line in enumerate(read_text_lines(path), 1):
                match = PYTEST_RE.match(line)
                if match:
                    name = match.group(1)
                    rel = str(path.relative_to(config.repo_root))
                    index.setdefault(name, (rel, idx))
    return index


def index_js_tests(config: TraceConfig) -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    exts = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
    for root in config.js_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in exts:
                continue
            rel = str(path.relative_to(config.repo_root))
            for idx, line in enumerate(read_text_lines(path), 1):
                match = JS_TEST_RE.search(line) or DENO_TEST_RE.search(line)
                if match:
                    name = match.group(2)
                    index.setdefault(name, (rel, idx))
    return index


def index_rust_tests(config: TraceConfig) -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    for root in config.rust_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.rs"):
            rel = str(path.relative_to(config.repo_root))
            pending_test = False
            for idx, line in enumerate(read_text_lines(path), 1):
                if RUST_TEST_ATTR_RE.match(line):
                    pending_test = True
                    continue
                if pending_test:
                    match = RUST_FN_RE.match(line)
                    if match:
                        name = match.group(1)
                        index.setdefault(name, (rel, idx))
                        pending_test = False
                    elif line.strip() and not line.strip().startswith("#"):
                        pending_test = False
    return index


def link_test_ids(config: TraceConfig) -> dict:
    rows = parse_matrix(config.matrix)
    gtest_index = index_gtest_tests(config)
    pytest_index = index_pytest_tests(config)
    js_index = index_js_tests(config)
    rust_index = index_rust_tests(config)

    links = []
    unresolved = 0

    for row in rows:
        test_id = row.get("TestID", "")
        location = row.get("TestLocation", "")
        link = {
            "test_id": test_id,
            "matrix_location": location,
            "resolved": False,
            "resolved_location": "",
            "resolved_line": 0,
        }

        if test_id in gtest_index:
            resolved_path, line = gtest_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )
        elif test_id in pytest_index:
            resolved_path, line = pytest_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )
        elif test_id in js_index:
            resolved_path, line = js_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )
        elif test_id in rust_index:
            resolved_path, line = rust_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )

        if not link["resolved"]:
            unresolved += 1

        links.append(link)

    report = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "total": len(links),
        "resolved": len(links) - unresolved,
        "unresolved": unresolved,
        "links": links,
    }
    return report


def write_validate_report(config: TraceConfig, report: dict) -> None:
    config.trace_dir.mkdir(parents=True, exist_ok=True)
    md_path = config.trace_dir / "traceability_report.md"
    json_path = config.trace_dir / "traceability_report.json"

    md_path.write_text(
        "\n".join(
            [
                "# Traceability Validation Report",
                f"**Timestamp (UTC):** {report['timestamp_utc']}",
                "",
                "## Summary",
                f"- Requirements: {report['requirements_total']}",
                f"- Risk controls: {report['risk_controls_total']}",
                f"- Matrix rows: {report['matrix_rows']}",
                f"- Requirements covered: {report['requirements_covered']}",
                f"- Coverage ratio: {report['coverage_ratio']:.2%}",
                f"- Coverage threshold: {report['coverage_threshold']:.2%}",
                "",
                "## Errors",
                (
                    "\n".join(f"- {err}" for err in report["errors"])
                    if report["errors"]
                    else "- None"
                ),
                "",
                "## Warnings",
                (
                    "\n".join(f"- {warn}" for warn in report["warnings"])
                    if report["warnings"]
                    else "- None"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_link_report(config: TraceConfig, report: dict) -> None:
    config.trace_dir.mkdir(parents=True, exist_ok=True)
    md_path = config.trace_dir / "testid_links.md"
    json_path = config.trace_dir / "testid_links.json"

    lines = [
        "# TestID Link Report",
        f"**Timestamp (UTC):** {report['timestamp_utc']}",
        "",
        "## Summary",
        f"- Total TestIDs: {report['total']}",
        f"- Resolved: {report['resolved']}",
        f"- Unresolved: {report['unresolved']}",
        "",
        "## Links",
        "| TestID | Matrix Location | Resolved Location | Line | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for link in report["links"]:
        status = "RESOLVED" if link["resolved"] else "UNRESOLVED"
        resolved_loc = link["resolved_location"] or "-"
        resolved_line = str(link["resolved_line"]) if link["resolved_line"] else "-"
        lines.append(
            f"| {link['test_id']} | {link['matrix_location'] or '-'} | "
            f"{resolved_loc} | {resolved_line} | {status} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def find_submodules(repo_root: Path) -> list[Path]:
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.exists():
        return []
    paths = []
    for line in gitmodules.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("path ="):
            _, value = line.split("=", 1)
            path = repo_root / value.strip()
            paths.append(path)
    return paths


def repo_has_traceability(config: TraceConfig) -> bool:
    return config.matrix.exists() or config.trace_dir.exists()


def aggregate_reports(repo_root: Path, coverage_threshold: float) -> dict:
    repos = [repo_root] + find_submodules(repo_root)
    results = []

    for repo in repos:
        config = load_config(repo)
        if not repo.exists():
            results.append(
                {"repo": str(repo), "status": "missing", "errors": ["path missing"]}
            )
            continue
        if not repo_has_traceability(config):
            results.append({"repo": str(repo), "status": "skipped"})
            continue

        validate_report = validate_repo(config, coverage_threshold)
        link_report = link_test_ids(config)
        write_validate_report(config, validate_report)
        write_link_report(config, link_report)

        status = "ok" if not validate_report["errors"] else "failed"
        results.append(
            {
                "repo": str(repo),
                "status": status,
                "validate": validate_report,
                "link": {
                    "total": link_report["total"],
                    "resolved": link_report["resolved"],
                    "unresolved": link_report["unresolved"],
                },
            }
        )

    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "repo_root": str(repo_root),
        "coverage_threshold": coverage_threshold,
        "results": results,
    }


def write_aggregate_report(trace_dir: Path, aggregate: dict) -> None:
    out_dir = trace_dir / "aggregate"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "traceability_rollup.md"
    json_path = out_dir / "traceability_rollup.json"

    lines = [
        "# Traceability Rollup",
        f"**Timestamp (UTC):** {aggregate['timestamp_utc']}",
        f"**Coverage Threshold:** {aggregate['coverage_threshold']:.2%}",
        "",
        "## Summary",
        "| Repo | Status | Requirements | Covered | Coverage | Errors | Unresolved TestIDs |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for entry in aggregate["results"]:
        if entry.get("status") in ("skipped", "missing"):
            lines.append(f"| {entry['repo']} | {entry['status']} | - | - | - | - | - |")
            continue
        validate = entry["validate"]
        coverage = f"{validate['coverage_ratio']:.2%}"
        errors = len(validate["errors"])
        unresolved = entry["link"]["unresolved"]
        lines.append(
            f"| {entry['repo']} | {entry['status']} | "
            f"{validate['requirements_total']} | {validate['requirements_covered']} | "
            f"{coverage} | {errors} | {unresolved} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")


def init_traceability(config: TraceConfig) -> dict:
    created: list[Path] = []
    skipped: list[Path] = []

    config.trace_dir.mkdir(parents=True, exist_ok=True)

    def ensure_file(path: Path, content: str) -> None:
        if path.exists():
            skipped.append(path)
            return
        path.write_text(content, encoding="utf-8")
        created.append(path)

    ensure_file(
        config.requirements,
        "\n".join(
            [
                "# Requirements",
                "",
                "REQ-EXAMPLE-1: Example requirement description.",
                "",
            ]
        ),
    )
    ensure_file(
        config.risk_controls,
        "\n".join(
            [
                "# Risk Controls",
                "",
                "RC-EXAMPLE-1: Example risk control description.",
                "",
            ]
        ),
    )
    ensure_file(
        config.matrix,
        "\n".join(
            [
                "RequirementID,RiskControlID,TestID,TestLocation,Notes",
                "REQ-EXAMPLE-1,RC-EXAMPLE-1,example_test,,TODO: add test coverage",
                "",
            ]
        ),
    )

    return {
        "trace_dir": str(config.trace_dir),
        "created": [str(path) for path in created],
        "skipped": [str(path) for path in skipped],
    }

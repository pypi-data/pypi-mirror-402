import argparse
import sys
from pathlib import Path

from privscan.rules.loader import RuleLoader
from privscan.detectors.secrets import SecretDetector
from privscan.engine.engine import ScanEngine
from privscan.reporter.json_reporter import JSONReporter
from privscan.reporter.summary import SummaryReporter
from privscan.reporter.table import TableReporter


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="privscan",
        description="Local-first privacy & secret scanner",
    )

    # ---------- Core ----------
    parser.add_argument("path", help="Path to scan")

    parser.add_argument(
        "--rules",
        default=None,
        help="Optional custom rules directory",
    )

    parser.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default="high",
        help="Minimum severity threshold (default: high)",
    )

    # ---------- Output ----------
    parser.add_argument(
        "--format",
        choices=["summary", "table", "json"],
        default="table",
        help="Output format",
    )

    parser.add_argument(
        "--output",
        help="Output file (required for json format)",
    )

    # ---------- CI / Automation ----------
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit with code 1 if findings are detected (CI/CD use)",
    )

    args = parser.parse_args()

    # ---------- Scan ----------
    rules = RuleLoader(args.rules).load()
    detector = SecretDetector(rules)
    engine = ScanEngine(detector)

    findings = engine.scan_path(
        Path(args.path),
        min_severity=args.severity,
    )

    # ---------- Reporting ----------
    if args.format == "json":
        if not args.output:
            print("Error: --output is required for json format", file=sys.stderr)
            sys.exit(2)
        JSONReporter().write(findings, args.output)

    elif args.format == "summary":
        print(SummaryReporter().render(findings))

    else:
        TableReporter().render(findings)

    # ---------- Exit Codes (FINAL) ----------
    # CI mindset:
    # 0 = clean
    # 1 = findings detected (when flag enabled)
    if args.fail_on_findings and findings:
        sys.exit(1)

    sys.exit(0)

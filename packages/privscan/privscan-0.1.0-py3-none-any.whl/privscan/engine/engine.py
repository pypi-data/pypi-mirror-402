from pathlib import Path
from typing import List, Dict, Iterable

from privscan.scanner.filesystem import FileScanner
from privscan.scanner.reader import read_file
from privscan.detectors.secrets import SecretDetector
from privscan.engine.location import offset_to_line_col


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}


class ScanEngine:
    def __init__(self, detector: SecretDetector) -> None:
        self.detector = detector

    def scan_path(
        self,
        path: str | Path,
        min_severity: str | None = None,
    ) -> List[Dict]:
        scanner = FileScanner(path)
        findings: List[Dict] = []

        for file_path in scanner.scan():
            content = read_file(file_path)
            if not content:
                continue

            results = self.detector.detect(content)
            for result in results:
                line, col = offset_to_line_col(content, result["start"])
                line_text = content.splitlines()[line - 1] if line - 1 < len(content.splitlines()) else ""

                enriched = {
                    **result,
                    "file": str(file_path),
                    "line": line,
                    "column": col,
                    "line_text": line_text.strip(),
                }
                findings.append(enriched)

        if min_severity:
            findings = self._filter_by_severity(findings, min_severity)

        return findings

    def _filter_by_severity(self, findings: Iterable[Dict], min_severity: str) -> List[Dict]:
        threshold = SEVERITY_ORDER[min_severity.lower()]
        return [
            f for f in findings
            if SEVERITY_ORDER.get(f["severity"].lower(), 0) >= threshold
        ]

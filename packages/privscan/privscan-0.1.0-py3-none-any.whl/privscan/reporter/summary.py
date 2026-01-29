from typing import List, Dict
from collections import Counter


class SummaryReporter:
    """
    Prints CLI-friendly summary.
    """

    def render(self, findings: List[Dict]) -> str:
        severity_counts = Counter(f["severity"] for f in findings)

        lines = [
            f"Total Findings: {len(findings)}",
        ]

        for severity, count in severity_counts.items():
            lines.append(f"{severity.upper():<8} : {count}")

        return "\n".join(lines)

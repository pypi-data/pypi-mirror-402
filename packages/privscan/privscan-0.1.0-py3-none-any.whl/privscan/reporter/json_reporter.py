import json
from typing import List, Dict
from pathlib import Path


class JSONReporter:
    """
    Writes machine-readable JSON scan reports.
    """

    def write(self, findings: List[Dict], output: str | Path) -> None:
        path = Path(output)
        path.write_text(
            json.dumps(
                {
                    "total_findings": len(findings),
                    "findings": findings,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

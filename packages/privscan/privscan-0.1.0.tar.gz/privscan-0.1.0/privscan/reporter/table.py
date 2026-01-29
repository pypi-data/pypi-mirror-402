from typing import List, Dict
from rich.table import Table
from rich.console import Console


class TableReporter:
    """
    Renders detailed CLI table for findings.
    """

    def render(self, findings: List[Dict]) -> None:
        table = Table(title="PrivScan Findings")

        table.add_column("Severity", style="red")
        table.add_column("Rule ID")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Match")
        table.add_column("Description")

        for f in findings:
            table.add_row(
                f["severity"].upper(),
                f["rule_id"],
                f["file"],
                str(f["line"]),
                f["match"],
                f["description"],
            )

        Console().print(table)

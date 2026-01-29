from typing import List, Dict
from privscan.rules.models import Rule


class SecretDetector:
    """
    Applies secret-detection rules against file content.
    """

    def __init__(self, rules: List[Rule]) -> None:
        self.rules = [r for r in rules if r.category == "secrets"]

    def detect(self, content: str) -> List[Dict]:
        findings: List[Dict] = []

        for rule in self.rules:
            for match in rule.regex.finditer(content):
                findings.append(
                    {
                        "rule_id": rule.id,
                        "category": rule.category,
                        "severity": rule.severity,
                        "description": rule.description,
                        "match": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        return findings

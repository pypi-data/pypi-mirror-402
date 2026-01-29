from dataclasses import dataclass
from typing import Pattern
import re


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    regex: Pattern[str]
    severity: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        return cls(
            id=data["id"],
            category=data["category"],
            regex=re.compile(data["regex"]),
            severity=data["severity"],
            description=data["description"],
        )

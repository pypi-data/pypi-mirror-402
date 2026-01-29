from typing import List
from pathlib import Path
import yaml
import importlib.resources as pkg_resources

from .models import Rule


class RuleLoader:
    def __init__(self, rules_path: str | None = None) -> None:
        self.rules_path = rules_path

    def load(self) -> List[Rule]:
        rules: List[Rule] = []

        if self.rules_path is not None:
            path = Path(self.rules_path)
            if not path.exists():
                raise FileNotFoundError(f"Rules path not found: {path}")
            files = path.glob("*.yml")
        else:
            files = pkg_resources.files("privscan.rules").glob("*.yml")

        for file in files:
            with pkg_resources.as_file(file) as f:
                data = yaml.safe_load(f.read_text()) or []

            for item in data:
                rules.append(Rule.from_dict(item))

        return rules

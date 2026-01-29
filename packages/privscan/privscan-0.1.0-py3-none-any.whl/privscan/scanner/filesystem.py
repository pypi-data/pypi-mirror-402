from pathlib import Path
from typing import Iterator, List


class FileScanner:
    """
    Walks a directory tree and yields scannable text files.
    """

    DEFAULT_IGNORE_DIRS = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
        "site-packages",
    }

    DEFAULT_IGNORE_FILES = {
        "report.json",
    }

    DEFAULT_EXTENSIONS = {
        ".py",
        ".env",
        ".txt",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
    }

    def __init__(
        self,
        root: str | Path,
        ignore_dirs: List[str] | None = None,
        ignore_files: List[str] | None = None,
        extensions: List[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.ignore_dirs = set(ignore_dirs) if ignore_dirs else self.DEFAULT_IGNORE_DIRS
        self.ignore_files = set(ignore_files) if ignore_files else self.DEFAULT_IGNORE_FILES
        self.extensions = set(extensions) if extensions else self.DEFAULT_EXTENSIONS

        if not self.root.exists():
            raise FileNotFoundError(f"Path does not exist: {self.root}")

    def scan(self) -> Iterator[Path]:
        for path in self.root.rglob("*"):
            if self._should_skip(path):
                continue
            yield path

    def _should_skip(self, path: Path) -> bool:
        if path.is_dir():
            return True

        if any(part in self.ignore_dirs for part in path.parts):
            return True

        if path.name in self.ignore_files:
            return True

        if path.suffix.lower() not in self.extensions:
            return True

        return False

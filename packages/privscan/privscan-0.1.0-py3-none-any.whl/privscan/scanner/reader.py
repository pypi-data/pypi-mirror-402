from pathlib import Path


def read_file(path: Path) -> str:
    """
    Safely read text files only.
    """
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

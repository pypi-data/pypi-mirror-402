from typing import Tuple


def offset_to_line_col(text: str, offset: int) -> Tuple[int, int]:
    """
    Convert string offset to 1-based (line, column).
    """
    line = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    col = offset + 1 if last_nl == -1 else offset - last_nl
    return line, col

"""Read and write the one-line board files used by every program."""

from __future__ import annotations

from pathlib import Path

from morris.board import validate_board


def read_board(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    token = text.split()
    if not token:
        raise ValueError(f"{path} is empty")
    try:
        return validate_board(token[0])
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc


def write_board(path: str, board: str) -> None:
    Path(path).write_text(validate_board(board) + "\n", encoding="utf-8")

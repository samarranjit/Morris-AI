"""Strict board files and atomic writes: a failed write cannot leave half a board."""
from pathlib import Path
import os
import tempfile
from morris.board import validate_board


def read_board(path: str) -> str:
    text = Path(path).read_text(encoding='utf-8')
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f'{path}: expected exactly one board string')
    return validate_board(tokens[0])


def write_text_atomic(path: str, text: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         prefix='.morris-', delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, destination)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def write_board(path: str, board: str) -> None:
    write_text_atomic(path, validate_board(board) + '\n')

"""White move generators from the Morris handout.

Black moves are produced by swapping colors, generating White moves,
and swapping the results back. Generated positions keep the handout's
scan order: locations from 0 through 22, and neighbors in the order
stored on the board. That order is the tie-break used by search.
"""

from __future__ import annotations

from morris.board import BLACK, BOARD_SIZE, EMPTY, WHITE, close_mill, neighbors, swap_colors


def generate_moves_opening(board: str) -> list[str]:
    """Positions reached by White placing one piece."""
    return generate_add(board)


def generate_moves_midgame_endgame(board: str) -> list[str]:
    """White midgame moves, or hops when White has exactly three pieces."""
    if board.count(WHITE) == 3:
        return generate_hopping(board)
    return generate_move(board)


def generate_add(board: str) -> list[str]:
    """Place a White piece on each empty square. Remove a Black piece if that closes a mill."""
    cells = list(board)
    positions: list[str] = []
    for location in range(BOARD_SIZE):
        if cells[location] != EMPTY:
            continue
        nxt = cells.copy()
        nxt[location] = WHITE
        if close_mill(location, nxt):
            generate_remove(nxt, positions)
        else:
            positions.append("".join(nxt))
    return positions


def generate_move(board: str) -> list[str]:
    """Slide each White piece to an adjacent empty square."""
    cells = list(board)
    positions: list[str] = []
    for location in range(BOARD_SIZE):
        if cells[location] != WHITE:
            continue
        for dest in neighbors(location):
            if cells[dest] != EMPTY:
                continue
            nxt = cells.copy()
            nxt[location] = EMPTY
            nxt[dest] = WHITE
            if close_mill(dest, nxt):
                generate_remove(nxt, positions)
            else:
                positions.append("".join(nxt))
    return positions


def generate_hopping(board: str) -> list[str]:
    """Move each White piece to any empty square."""
    cells = list(board)
    positions: list[str] = []
    for origin in range(BOARD_SIZE):
        if cells[origin] != WHITE:
            continue
        for dest in range(BOARD_SIZE):
            if cells[dest] != EMPTY:
                continue
            nxt = cells.copy()
            nxt[origin] = EMPTY
            nxt[dest] = WHITE
            if close_mill(dest, nxt):
                generate_remove(nxt, positions)
            else:
                positions.append("".join(nxt))
    return positions


def generate_remove(board: list[str], positions: list[str]) -> None:
    """Append positions that remove one Black piece.

    An isolated piece (one that is not in a mill) is removed. When every
    Black piece is in a mill, any Black piece may be removed. That is the
    usual Morris rule, and it is what the handout's last line of
    GenerateRemove is describing: if nothing was added because every
    Black piece is in a mill, still produce a position with a removal.
    """
    start = len(positions)
    for location in range(BOARD_SIZE):
        if board[location] == BLACK and not close_mill(location, board):
            nxt = board.copy()
            nxt[location] = EMPTY
            positions.append("".join(nxt))
    if len(positions) > start:
        return
    for location in range(BOARD_SIZE):
        if board[location] == BLACK:
            nxt = board.copy()
            nxt[location] = EMPTY
            positions.append("".join(nxt))


def generate_moves_opening_black(board: str) -> list[str]:
    return _black_moves(board, generate_moves_opening)


def generate_moves_midgame_endgame_black(board: str) -> list[str]:
    return _black_moves(board, generate_moves_midgame_endgame)


def _black_moves(board: str, white_generator) -> list[str]:
    swapped = white_generator(swap_colors(board))
    return [swap_colors(position) for position in swapped]

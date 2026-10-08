"""Board geometry for the Morris Game, Variant.

A position is a 23-character string. Index 0 is a0 at the bottom-left.
Characters are W, B, and x (empty). The index table is the one printed
in the Morris handout.

Neighbor lists are the squares a piece may move to in the midgame.
They are stored in ascending index order. The handout's two explicit
cases are the same sets: a0 -> {d0, b1, a3} and d0 -> {a0, g0, d1}.

There is no d2 and no d3. The inner bottom edge is the single link
c2-e2, and the middle of the board is open.
"""

from __future__ import annotations

BOARD_SIZE = 23
EMPTY = "x"
WHITE = "W"
BLACK = "B"
PIECES = frozenset({WHITE, BLACK, EMPTY})

# Index, file-rank name. Row 0 is the bottom of the diagram.
LOCATIONS: tuple[str, ...] = (
    "a0",  # 0
    "d0",  # 1
    "g0",  # 2
    "b1",  # 3
    "d1",  # 4
    "f1",  # 5
    "c2",  # 6
    "e2",  # 7
    "a3",  # 8
    "b3",  # 9
    "c3",  # 10
    "e3",  # 11
    "f3",  # 12
    "g3",  # 13
    "c4",  # 14
    "d4",  # 15
    "e4",  # 16
    "b5",  # 17
    "d5",  # 18
    "f5",  # 19
    "a6",  # 20
    "d6",  # 21
    "g6",  # 22
)

LOCATION_INDEX = {name: index for index, name in enumerate(LOCATIONS)}

# Midgame adjacency. Each tuple is sorted by location index.
NEIGHBORS: tuple[tuple[int, ...], ...] = (
    (1, 3, 8),          # a0: d0, b1, a3
    (0, 2, 4),          # d0: a0, g0, d1
    (1, 5, 13),         # g0: d0, f1, g3
    (0, 4, 6, 9),       # b1: a0, d1, c2, b3
    (1, 3, 5),          # d1: d0, b1, f1
    (2, 4, 7, 12),      # f1: g0, d1, e2, f3
    (3, 7, 10),         # c2: b1, e2, c3
    (5, 6, 11),         # e2: f1, c2, e3
    (0, 9, 20),         # a3: a0, b3, a6
    (3, 8, 10, 17),     # b3: b1, a3, c3, b5
    (6, 9, 14),         # c3: c2, b3, c4
    (7, 12, 16),        # e3: e2, f3, e4
    (5, 11, 13, 19),    # f3: f1, e3, g3, f5
    (2, 12, 22),        # g3: g0, f3, g6
    (10, 15, 17),       # c4: c3, d4, b5
    (14, 16, 18),       # d4: c4, e4, d5
    (11, 15, 19),       # e4: e3, d4, f5
    (9, 14, 18, 20),    # b5: b3, c4, d5, a6
    (15, 17, 19, 21),   # d5: d4, b5, f5, d6
    (12, 16, 18, 22),   # f5: f3, e4, d5, g6
    (8, 17, 21),        # a6: a3, b5, d6
    (18, 20, 22),       # d6: d5, a6, g6
    (13, 19, 21),       # g6: g3, f5, d6
)

# Other two squares that complete a mill with this location.
# Straight lines only: three squares, the outer ring, the middle ring,
# the split row-3 lines, d4-d5-d6, c2-c3-c4, e2-e3-e4, and the four
# corner diagonals (a0-b1-c2, g0-f1-e2, a6-b5-c4, g6-f5-e4).
# c2-e2 and d0-d1 are edges, not mills. The handout's closeMill case
# labeled "d3" is index 1, which is d0.
MILLS: tuple[tuple[tuple[int, int], ...], ...] = (
    ((1, 2), (3, 6), (8, 20)),          # a0
    ((0, 2),),                          # d0
    ((0, 1), (5, 7), (13, 22)),         # g0
    ((4, 5), (9, 17), (0, 6)),          # b1
    ((3, 5),),                          # d1
    ((3, 4), (12, 19), (2, 7)),         # f1
    ((10, 14), (0, 3)),                 # c2
    ((11, 16), (2, 5)),                 # e2
    ((9, 10), (0, 20)),                 # a3
    ((8, 10), (3, 17)),                 # b3
    ((8, 9), (6, 14)),                  # c3
    ((12, 13), (7, 16)),                # e3
    ((11, 13), (5, 19)),                # f3
    ((11, 12), (2, 22)),                # g3
    ((15, 16), (6, 10), (17, 20)),      # c4
    ((14, 16), (18, 21)),               # d4
    ((14, 15), (7, 11), (19, 22)),      # e4
    ((18, 19), (3, 9), (14, 20)),       # b5
    ((17, 19), (15, 21)),               # d5
    ((17, 18), (5, 12), (16, 22)),      # f5
    ((21, 22), (0, 8), (14, 17)),       # a6
    ((20, 22), (15, 18)),               # d6
    ((20, 21), (2, 13), (16, 19)),      # g6
)


def neighbors(location: int) -> tuple[int, ...]:
    """Locations adjacent to location along a board line."""
    return NEIGHBORS[location]


def close_mill(location: int, board: str | list[str]) -> bool:
    """True when the piece at location is part of a mill.

    Matches the handout: the color is the piece already on location,
    and at least one line through that square is filled with that color.
    An empty square does not close a mill.
    """
    color = board[location]
    if color not in (WHITE, BLACK):
        return False
    return any(board[a] == color and board[b] == color for a, b in MILLS[location])


def swap_colors(board: str) -> str:
    """Swap White and Black. Empty squares stay empty.

    This is the handout's method for generating Black moves and for
    playing Black with a White search.
    """
    return board.translate(str.maketrans("WB", "BW"))


def count_pieces(board: str, color: str) -> int:
    return board.count(color)


def validate_board(board: str) -> str:
    """Return board with surrounding whitespace removed, or raise ValueError."""
    text = board.strip()
    if len(text) != BOARD_SIZE or any(char not in PIECES for char in text):
        raise ValueError(
            f"a board must be {BOARD_SIZE} characters, each one of W, B, x"
        )
    return text


def format_board(board: str) -> str:
    """Return a readable diagram with one character per intersection."""
    board = validate_board(board)
    cell = {index: board[index] for index in range(BOARD_SIZE)}

    def at(index: int) -> str:
        return cell[index]

    return "\n".join(
        [
            f"6  {at(20)}--------{at(21)}--------{at(22)}",
            "   | \\      |      / |",
            f"5  |  {at(17)}-----{at(18)}-----{at(19)}  |",
            "   |  | \\   |   / |  |",
            f"4  |  |  {at(14)}--{at(15)}--{at(16)}  |  |",
            "   |  |  |     |  |  |",
            f"3  {at(8)}--{at(9)}--{at(10)}     {at(11)}--{at(12)}--{at(13)}",
            "   |  |  |     |  |  |",
            f"2  |  |  {at(6)}-----{at(7)}  |  |",
            "   |  | /   |   \\ |  |",
            f"1  |  {at(3)}-----{at(4)}-----{at(5)}  |",
            "   | /      |      \\ |",
            f"0  {at(0)}--------{at(1)}--------{at(2)}",
        ]
    )

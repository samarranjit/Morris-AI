"""Part IV: inexpensive, phase-specific positional evaluation.

Weights are transparent starting choices, not claimed optimal. Terminal
scores are +/-10000; ordinary scores are clamped inside that range.
"""
from morris.board import MILLS, NEIGHBORS

# Each mill appears at three endpoints in MILLS. Count each line only once.
LINES = tuple(sorted({tuple(sorted((index, *pair)))
                      for index, pairs in enumerate(MILLS) for pair in pairs}))


def features(board: str, color: str) -> dict[str, int]:
    """Count interpretable features without generating capture-result boards."""
    pieces = [i for i, piece in enumerate(board) if piece == color]
    empty = [i for i, piece in enumerate(board) if piece == 'x']
    mills = 0
    open_mills = 0
    for line in LINES:
        own = sum(board[i] == color for i in line)
        vacant = sum(board[i] == 'x' for i in line)
        if own == 3:
            mills += 1
        elif own == 2 and vacant == 1:
            open_mills += 1

    mobility = 0
    blocked = 0
    threats = 0
    for origin in pieces:
        if len(pieces) == 3:
            destinations = empty  # A three-piece player can hop.
        else:
            destinations = [i for i in NEIGHBORS[origin] if board[i] == 'x']
        mobility += len(destinations)
        if not destinations:
            blocked += 1
        for destination in destinations:
            # The moving piece must not be one of the two pieces left in
            # the mill. This avoids counting impossible sliding threats.
            closes_mill = any(origin not in (a, b) and board[a] == color and board[b] == color
                              for a, b in MILLS[destination])
            if closes_mill:
                threats += 1

    return {
        'pieces': len(pieces),
        'mills': mills,
        'open_mills': open_mills,
        'mobility': mobility,
        'blocked': blocked,
        'threats': threats,
        'connections': sum(len(MILLS[i]) for i in pieces),
    }


def differences(board: str) -> dict[str, int]:
    white = features(board, 'W')
    black = features(board, 'B')
    return {name: white[name] - black[name] for name in white}


def bounded(score: int) -> int:
    return max(-9000, min(9000, score))


def static_estimate_opening_improved(board: str) -> int:
    """Prefer material, future mills, and participation in useful lines."""
    delta = differences(board)
    return bounded(100 * delta['pieces'] + 20 * delta['open_mills']
                   + 10 * delta['mills'] + 3 * delta['connections'])


def static_estimate_midgame_endgame_improved(board: str) -> int:
    """Material plus actionable threats and movement freedom.

    Side-to-move blockade wins are checked by search, which knows whose
    turn it is. A board-only evaluator cannot correctly determine that.
    """
    if board.count('B') <= 2:
        return 10000
    if board.count('W') <= 2:
        return -10000
    delta = differences(board)
    return bounded(1000 * delta['pieces'] + 60 * delta['threats']
                   + 25 * delta['mills'] + 5 * delta['mobility']
                   - 20 * delta['blocked'])

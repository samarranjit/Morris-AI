"""Timed alpha-beta and a validated, local match history (no network posting)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from time import monotonic

from morris.board import swap_colors, validate_board
from morris.improved import static_estimate_opening_improved, static_estimate_midgame_endgame_improved
from morris.io import write_text_atomic
from morris.search import alphabeta, legal_moves, SearchTimeout


@dataclass
class Decision:
    board: str
    evaluated: int
    value: int
    completed_depth: int
    elapsed: float
    timed_out: bool


def initial_state():
    return {'board': 'x' * 23, 'side': 'white', 'placements': 0}


def phase_for(placements):
    return 'opening' if placements < 18 else 'midgame'


def next_state(state, board):
    return {
        'board': board,
        'side': 'black' if state['side'] == 'white' else 'white',
        'placements': min(18, state['placements'] + 1),
    }


def game_result(history):
    """Return white/black/draw, or None if the game can continue."""
    state = history[-1]
    position = state['board']
    if state['placements'] == 18:
        if position.count('B') <= 2:
            return 'white'
        if position.count('W') <= 2:
            return 'black'
        moves = legal_moves(position, 'midgame', state['side'] == 'white')
        if not moves:
            return 'black' if state['side'] == 'white' else 'white'
    occurrences = sum(item['board'] == position and item['side'] == state['side'] for item in history)
    if occurrences >= 3:
        return 'draw'
    return None


def validate_history(history):
    if not isinstance(history, list) or not history or history[0] != initial_state():
        raise ValueError('history must start with the empty board, White to move, placements 0')
    for index, state in enumerate(history):
        if not isinstance(state, dict) or set(state) != {'board', 'side', 'placements'}:
            raise ValueError('invalid history entry')
        if not isinstance(state['board'], str):
            raise ValueError('history board must be a string')
        validate_board(state['board'])
        if state['side'] not in ('white', 'black') or type(state['placements']) is not int:
            raise ValueError('invalid side or placement count in history')
        if index == 0:
            continue
        previous = history[index - 1]
        if game_result(history[:index]) is not None:
            raise ValueError('history contains a move after the game ended')
        successors = legal_moves(previous['board'], phase_for(previous['placements']), previous['side'] == 'white')
        if state['board'] not in successors or state != next_state(previous, state['board']):
            raise ValueError(f'history move {index} is illegal or has incorrect turn information')
    return history


def load_history(path, board, color):
    """Accept the current opponent post only if it follows the saved position.

    Both teams can maintain their own history file. After our move the last
    entry is the opponent's turn; on our next run their posted move is added.
    Re-running the same input is allowed, and does not append our move twice.
    """
    location = Path(path)
    history = json.loads(location.read_text()) if location.exists() else [initial_state()]
    validate_history(history)
    # Permit a retry using the same pre-move input after a prior successful run.
    if len(history) >= 2 and history[-2]['board'] == board and history[-2]['side'] == color:
        history = history[:-1]
    last = history[-1]
    if last['board'] == board and last['side'] == color:
        return history
    if last['side'] == color:
        raise ValueError('input does not match the saved position for your turn')
    if game_result(history) is not None:
        raise ValueError('saved game has already ended')
    if board not in legal_moves(last['board'], phase_for(last['placements']), last['side'] == 'white'):
        raise ValueError('opponent board is not a legal successor of the saved board')
    history.append(next_state(last, board))
    return history


def save_history(path, history):
    write_text_atomic(path, json.dumps(history, indent=2) + '\n')


def choose_move(board, color, placements, max_depth, seconds=180.0, history=None):
    """Iteratively deepen ordinary alpha-beta, retaining completed searches.

    Search uses the player's color as White internally. Match histories keep
    the real colors. No caching or alternate game-playing algorithm is used.
    """
    board = validate_board(board)
    if color not in ('white', 'black'):
        raise ValueError('color must be white or black')
    if max_depth < 1 or not 0 <= placements <= 18 or seconds < 0:
        raise ValueError('require depth >= 1, placements 0..18, and nonnegative time')
    if any(board.count(piece) > 9 for piece in ('W', 'B')):
        raise ValueError('a player cannot have more than nine pieces')
    if placements < 18:
        expected_side = 'white' if placements % 2 == 0 else 'black'
        if color != expected_side:
            raise ValueError('side disagrees with opening placement count')
        if board.count('W') > (placements + 1)//2 or board.count('B') > placements//2:
            raise ValueError('board contains more pieces than have been placed')
    state = {'board': board, 'side': color, 'placements': placements}
    if history is not None and (not history or history[-1] != state):
        raise ValueError('history must end at the input board and turn')
    if game_result(history if history is not None else [state]) is not None:
        raise ValueError('game is over; no move should be posted')

    start = monotonic()
    deadline = start + seconds
    query = swap_colors(board) if color == 'black' else board
    phase = phase_for(placements)
    moves = legal_moves(query, phase, True)
    if not moves:
        raise ValueError('no legal move')
    repetitions = None
    if history is not None:
        repetitions = Counter()
        for item in history:
            position = swap_colors(item['board']) if color == 'black' else item['board']
            repetitions[(position, item['side'] == color)] += 1

    evaluated = 0
    def opening(position):
        nonlocal evaluated
        evaluated += 1
        return static_estimate_opening_improved(position)

    def midgame(position):
        nonlocal evaluated
        evaluated += 1
        return static_estimate_midgame_endgame_improved(position)

    # Always have a legal fallback, even if an extremely small budget expires.
    chosen = moves[0]
    value = opening(chosen) if placements < 17 else midgame(chosen)
    completed = 0
    timed_out = False
    for depth in range(1, max_depth + 1):
        try:
            result = alphabeta(query, depth, phase=phase,
                               estimate=opening if phase == 'opening' else midgame,
                               game_estimate=midgame, placements=placements,
                               deadline=deadline, repetitions=repetitions)
        except SearchTimeout:
            timed_out = True
            break
        chosen, _, value = result
        completed = depth
        if value == 10000:
            break  # A forced win is already proven within this search horizon.
    if color == 'black':
        chosen = swap_colors(chosen)
    if chosen not in legal_moves(board, phase, color == 'white'):
        raise RuntimeError('search returned an illegal successor')
    return Decision(chosen, evaluated, value, completed, monotonic() - start, timed_out)

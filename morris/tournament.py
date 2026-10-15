"""Timed alpha-beta, a validated match history, and the interactive match console.

Nothing here posts online. The designated communicator copies each move into Teams.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sys
from time import monotonic
from uuid import uuid4

from morris.board import format_board, swap_colors, validate_board
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


# Interactive match console. One session JSON per game holds the color,
# search settings, and full history, so a game can be resumed.

SESSION_DIR = Path(__file__).resolve().parents[1] / 'out' / 'tournament-console'
HEADER = re.compile(r'Move\s+(\d+)\s*[-–—]\s*(White|Black)', re.IGNORECASE)


def check_settings(seconds, depth):
    if not math.isfinite(seconds) or not 0.01 <= seconds <= 210:
        raise ValueError('Search time must be between 0.01 and 210 seconds.')
    if not 1 <= depth <= 100:
        raise ValueError('Depth ceiling must be between 1 and 100.')


def save_session(path, session):
    """Save before printing a move so it can be recovered after interruption."""
    write_text_atomic(str(path), json.dumps(session, indent=2) + '\n')


def load_session(path):
    session = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(session, dict) or session.get('version') != 1:
        raise ValueError('Choose a session JSON created by this console.')
    if session.get('color') not in ('white', 'black'):
        raise ValueError('Saved session has an invalid player color.')
    if type(session.get('depth')) is not int or type(session.get('seconds')) not in (int, float):
        raise ValueError('Saved session has invalid search settings.')
    check_settings(session['seconds'], session['depth'])
    validate_history(session.get('history'))
    return session


def teams_message(history):
    """The last state's side is the NEXT player, so invert it for the post."""
    state = history[-1]
    mover = 'Black' if state['side'] == 'white' else 'White'
    return f"Move {len(history) - 1} - {mover}\n{state['board']}"


def parse_opponent(text, history):
    """Accept a board alone, a Teams header alone, or a one-line Teams post."""
    text = text.strip()
    header = HEADER.match(text)
    if header:
        number, side = header.groups()
        if int(number) != len(history) or side.lower() != history[-1]['side']:
            raise ValueError(f"Expected Move {len(history)} - {history[-1]['side'].title()}.")
        text = text[header.end():].strip()
        if not text:
            return None  # A multiline paste sends its board on the next input line.
    return validate_board(text)


def play_session(session, path, read=input, write=print, chooser=choose_move):
    """One loop: calculate our turn, otherwise wait for a validated opponent turn."""
    color = session['color']
    write(f"\nYou are {color.title()}. Saved session: {path}")
    write('Paste the opponent board and press Enter. Commands: show, time N, quit.')
    write('Copy the Teams message yourself; this console never posts online.')
    write('The Teams clock starts at their post. Use time N to reduce the next search budget.')

    # On resume, show the already chosen move; do not silently choose another.
    history = session['history']
    if len(history) > 1 and history[-1]['side'] != color:
        write('\nLast saved move from your team (do not post twice):\n' + teams_message(history))

    while True:
        history = session['history']
        state = history[-1]
        result = game_result(history)
        if result is not None:
            if result == 'draw':
                write('\nGame over: draw by threefold repetition.')
            else:
                write(f'\nGame over: {result.title()} wins under the board rules.')
            write(f'Full game saved: {path}')
            return

        if state['side'] == color:
            phase = phase_for(state['placements'])
            write(f"\nCalculating Move {len(history)} - {color.title()} ({phase})... "
                  f"Budget {session['seconds']:g}s, depth ceiling {session['depth']}.")
            decision = chooser(state['board'], color, state['placements'], session['depth'],
                               session['seconds'], history)
            if decision.board not in legal_moves(state['board'], phase, color == 'white'):
                raise ValueError('Agent returned an illegal move; nothing was recorded or posted.')
            updated = dict(session, history=history + [next_state(state, decision.board)])
            save_session(path, updated)
            session.update(updated)
            write(f'Completed depth: {decision.completed_depth}; elapsed: {decision.elapsed:.3f}s; '
                  f'estimator calls: {decision.evaluated}; score: {decision.value}')
            if decision.completed_depth == 0:
                write('Time expired before depth 1 completed; using the saved legal fallback.')
            write('\nCOPY THESE TWO LINES INTO TEAMS:\n' + teams_message(session['history']) + '\n')
            continue

        text = read(f"Opponent Move {len(history)} - {state['side'].title()}> ").strip()
        if text.lower() in ('quit', 'exit', 'q'):
            write(f'Session saved. Resume using: {path}')
            return
        if text.lower() == 'show':
            write(format_board(state['board']))
            if len(history) > 1:
                write('Last recorded move:\n' + teams_message(history))
            continue
        if text.lower().startswith('time '):
            try:
                seconds = float(text.split(maxsplit=1)[1])
                check_settings(seconds, session['depth'])
                updated = dict(session, seconds=seconds)
                save_session(path, updated)
                session.update(updated)
                write(f'Next searches get up to {seconds:g} seconds.')
            except ValueError as exc:
                write(str(exc))
            continue
        if not text:
            continue
        try:
            board = parse_opponent(text, history)
            if board is None:
                continue
            successors = legal_moves(state['board'], phase_for(state['placements']), state['side'] == 'white')
            if board not in successors:
                raise ValueError('This board is not a legal move from the last saved board. Check the pasted string.')
        except ValueError as exc:
            write(f'Invalid input: {exc} Game unchanged; paste again.')
            continue
        # Save the accepted opponent turn BEFORE searching. If interrupted,
        # resuming the console will calculate from this exact position.
        updated = dict(session, history=history + [next_state(state, board)])
        save_session(path, updated)
        session.update(updated)
        write('Opponent move is valid.')


def ask(prompt, convert, valid, default=None):
    while True:
        text = input(prompt).strip()
        if not text and default is not None:
            return default
        try:
            value = convert(text)
            if valid(value):
                return value
        except ValueError:
            pass
        print('Please enter one of the allowed values.')


def run_console(resume=None, seconds=None, depth=None):
    """Start or resume an interactive game. Returns a process exit code."""
    path = None
    try:
        print('MORRIS TOURNAMENT CONSOLE')
        if resume is None:
            mode = ask('New game or resume? [new/resume, Enter=new]: ', str.lower,
                       lambda s: s in ('new', 'resume'), 'new')
            if mode == 'resume':
                resume = Path(input('Paste the saved session JSON path: ').strip().strip('"\'')).expanduser()
        if resume is not None:
            path = Path(resume).expanduser().resolve()
            session = load_session(path)
            if seconds is not None:
                session['seconds'] = seconds
            if depth is not None:
                session['depth'] = depth
            check_settings(session['seconds'], session['depth'])
        else:
            color = ask('Your color [white/black]: ', str.lower, lambda s: s in ('white', 'black'))
            if seconds is None:
                seconds = ask('Search seconds [0.01..210, Enter=180; use 2 for practice]: ', float,
                              lambda n: math.isfinite(n) and 0.01 <= n <= 210, 180.0)
            if depth is None:
                depth = ask('Maximum depth [1..100, Enter=12]: ', int, lambda n: 1 <= n <= 100, 12)
            check_settings(seconds, depth)
            name = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:6]
            path = SESSION_DIR / f'{name}-{color}.json'
            session = {'version': 1, 'color': color, 'seconds': seconds, 'depth': depth,
                       'history': [initial_state()]}
        save_session(path, session)
        play_session(session, path)
        return 0
    except (KeyboardInterrupt, EOFError):
        print('\nStopped. Accepted moves are already saved; an unfinished search does not record a move.')
        if path is not None:
            print(f'Resume session: {path}')
        return 0
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        if path is not None:
            print(f'Session path: {path}', file=sys.stderr)
        return 2

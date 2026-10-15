#!/usr/bin/env python3
"""Interactive tournament-only UI. The submission builder excludes this folder."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from morris.board import format_board, validate_board
from morris.io import write_text_atomic
from morris.search import legal_moves
from morris.tournament import (
    choose_move, game_result, initial_state, next_state, phase_for, validate_history,
)

HEADER = re.compile(r'Move\s+(\d+)\s*[-–—]\s*(White|Black)', re.IGNORECASE)


def save_session(path, session):
    """Save before printing a move so it can be recovered after interruption."""
    write_text_atomic(str(path), json.dumps(session, indent=2) + '\n')


def check_settings(seconds, depth):
    if not math.isfinite(seconds) or not 0.01 <= seconds <= 210:
        raise ValueError('Search time must be between 0.01 and 210 seconds.')
    if not 1 <= depth <= 100:
        raise ValueError('Depth ceiling must be between 1 and 100.')


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', type=Path, help='resume a console session JSON')
    parser.add_argument('--seconds', type=float, help='skip the search-budget question')
    parser.add_argument('--depth', type=int, help='skip the depth-ceiling question')
    args = parser.parse_args(argv)
    path = None
    try:
        print('MORRIS TOURNAMENT CONSOLE')
        resume = args.resume
        if resume is None:
            mode = ask('New game or resume? [new/resume, Enter=new]: ', str.lower,
                       lambda s: s in ('new', 'resume'), 'new')
            if mode == 'resume':
                resume = Path(input('Paste the saved session JSON path: ').strip().strip('"\'' )).expanduser()
        if resume is not None:
            path = resume.expanduser().resolve()
            session = load_session(path)
            if args.seconds is not None:
                session['seconds'] = args.seconds
            if args.depth is not None:
                session['depth'] = args.depth
            check_settings(session['seconds'], session['depth'])
        else:
            color = ask('Your color [white/black]: ', str.lower, lambda s: s in ('white', 'black'))
            seconds = args.seconds
            if seconds is None:
                seconds = ask('Search seconds [0.01..210, Enter=180; use 2 for practice]: ', float,
                              lambda n: math.isfinite(n) and 0.01 <= n <= 210, 180.0)
            depth = args.depth
            if depth is None:
                depth = ask('Maximum depth [1..100, Enter=12]: ', int, lambda n: 1 <= n <= 100, 12)
            check_settings(seconds, depth)
            name = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:6]
            path = ROOT / 'out' / 'tournament-console' / f'{name}-{color}.json'
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


if __name__ == '__main__':
    sys.exit(main())

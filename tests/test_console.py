"""Interactive match console in morris.tournament and its TournamentAgent entry."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from morris import tournament as console

ROOT = Path(__file__).resolve().parents[1]


def new_session(color):
    return {'version': 1, 'color': color, 'seconds': 2.0, 'depth': 1,
            'history': [console.initial_state()]}


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / 'game.json'
        self.output = []

    def tearDown(self):
        self.folder.cleanup()

    def test_white_calculates_first_move_and_saves(self):
        session = new_session('white')
        console.play_session(session, self.path, read=lambda prompt: 'quit', write=self.output.append)
        saved = console.load_session(self.path)
        self.assertEqual(len(saved['history']), 2)
        self.assertEqual(saved['history'][-1]['side'], 'black')
        self.assertIn('Move 1 - White', '\n'.join(self.output))

    def test_black_waits_then_replies(self):
        session = new_session('black')
        answers = iter(['Move 1 - White', 'W' + 'x'*22, 'quit'])
        console.play_session(session, self.path, read=lambda prompt: next(answers), write=self.output.append)
        self.assertEqual(len(console.load_session(self.path)['history']), 3)
        self.assertIn('Move 2 - Black', '\n'.join(self.output))

    def test_illegal_opponent_move_does_not_advance_game(self):
        session = new_session('black')
        answers = iter(['bad', 'B'+'x'*22, 'W'+'x'*22, 'quit'])
        console.play_session(session, self.path, read=lambda prompt: next(answers), write=self.output.append)
        self.assertEqual(len(session['history']), 3)
        self.assertEqual(sum('Invalid input:' in line for line in self.output), 2)

    def test_white_second_turn_uses_same_history(self):
        session = new_session('white')
        count = 0
        def reply(prompt):
            nonlocal count
            count += 1
            if count == 1:
                state = session['history'][-1]
                return console.legal_moves(state['board'], 'opening', False)[0]
            return 'quit'
        console.play_session(session, self.path, read=reply, write=self.output.append)
        self.assertEqual(len(session['history']), 4)
        self.assertIn('Move 3 - White', '\n'.join(self.output))

    def test_resume_does_not_recalculate_last_own_move(self):
        session = new_session('white')
        console.play_session(session, self.path, read=lambda prompt: 'quit', write=self.output.append)
        saved = self.path.read_text()
        def forbidden(*args):
            self.fail('Must not recalculate an already saved move')
        console.play_session(console.load_session(self.path), self.path,
                             read=lambda prompt: 'quit', write=self.output.append, chooser=forbidden)
        self.assertEqual(self.path.read_text(), saved)

    def test_interrupt_after_opponent_move_can_resume(self):
        session = new_session('black')
        def interrupted(*args):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            console.play_session(session, self.path, read=lambda prompt: 'W'+'x'*22,
                                 write=self.output.append, chooser=interrupted)
        loaded = console.load_session(self.path)
        self.assertEqual(len(loaded['history']), 2)
        self.assertEqual(loaded['history'][-1]['side'], 'black')
        console.play_session(loaded, self.path, read=lambda prompt: 'quit', write=self.output.append)
        self.assertEqual(len(loaded['history']), 3)

    def test_header_checks_and_single_line_post(self):
        history = [console.initial_state()]
        self.assertEqual(console.parse_opponent('Move 1 - White ' + 'W'+'x'*22, history), 'W'+'x'*22)
        with self.assertRaises(ValueError):
            console.parse_opponent('Move 2 - Black', history)

    def test_time_command_is_saved_without_changing_board(self):
        session = new_session('black')
        answers = iter(['time nan', 'time 1', 'show', 'quit'])
        console.play_session(session, self.path, read=lambda prompt: next(answers), write=self.output.append)
        loaded = console.load_session(self.path)
        self.assertEqual(loaded['seconds'], 1)
        self.assertEqual(loaded['history'], [console.initial_state()])

    def test_game_over_does_not_ask_for_input(self):
        logs = json.loads((ROOT/'deliverables/validation.json').read_text())
        history = next(g['history'] for g in logs['games'] if g['result'] == 'draw')
        session = dict(new_session('white'), history=history)
        def forbidden(prompt):
            self.fail('A finished game must not request another move')
        console.play_session(session, self.path, read=forbidden, write=self.output.append)
        self.assertIn('Game over: draw', '\n'.join(self.output))

    def test_console_settings_reject_nonfinite_budgets(self):
        for seconds in (float('nan'), float('inf'), 0):
            with self.assertRaises(ValueError):
                console.check_settings(seconds, 12)
        for seconds in (240, 600):
            console.check_settings(seconds, 12)
            self.assertIn('Warning', console.time_warning(seconds))
        self.assertIsNone(console.time_warning(180))

    def test_agent_without_board_arguments_opens_console(self):
        self.path.write_text(json.dumps(new_session('black')))
        run = subprocess.run(
            [sys.executable, str(ROOT/'programs/TournamentAgent.py'), '--resume', str(self.path)],
            input='quit\n', capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('MORRIS TOURNAMENT CONSOLE', run.stdout)
        self.assertIn('Session saved', run.stdout)


if __name__ == '__main__':
    unittest.main()

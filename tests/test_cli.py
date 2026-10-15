"""Run real entry scripts; verify the exact output protocol and Black swaps."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from morris.board import swap_colors
from morris.search import minimax, legal_moves
from morris.estimation import static_estimate_opening, static_estimate_midgame_endgame

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def test_six_baseline_programs(self):
        cases = [
            ('MiniMaxOpening', 'opening', True), ('MiniMaxGame', 'midgame', True),
            ('ABOpening', 'opening', True), ('ABGame', 'midgame', True),
            ('MiniMaxOpeningBlack', 'opening', False), ('MiniMaxGameBlack', 'midgame', False),
        ]
        position = 'xxxxxBxWWWWWBBBBxxxxxxx'
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'input.txt'
            output = Path(folder)/'nested'/'output.txt'
            source.write_text(position)
            for name, phase, white in cases:
                run = subprocess.run([sys.executable,str(ROOT/'programs'/f'{name}.py'),str(source),str(output),'2'], capture_output=True,text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                lines = run.stdout.splitlines()
                self.assertEqual(len(lines), 3)
                chosen = output.read_text().strip()
                self.assertEqual(lines[0], f'Board Position: {chosen}')
                self.assertRegex(lines[1], r'^Positions evaluated by static estimation: \d+$')
                self.assertRegex(lines[2], r'^MINIMAX estimate: -?\d+$')
                self.assertIn(chosen, legal_moves(position,phase,white))
                estimate = static_estimate_opening if phase == 'opening' else static_estimate_midgame_endgame
                query = position if white else swap_colors(position)
                expected, _, value = minimax(query,2,phase=phase,estimate=estimate)
                self.assertEqual(chosen, expected if white else swap_colors(expected))
                self.assertEqual(lines[2],f'MINIMAX estimate: {value}')

    def test_bad_input_has_no_traceback_or_new_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'input.txt'
            output = Path(folder)/'output.txt'
            for content,depth in [('bad','2'), ('x'*23+' extra','2'), ('x'*23,'-1'), ('x'*23,'abc')]:
                source.write_text(content)
                run=subprocess.run([sys.executable,str(ROOT/'programs/MiniMaxOpening.py'),str(source),str(output),depth],capture_output=True,text=True)
                self.assertNotEqual(run.returncode,0)
                self.assertNotIn('Traceback',run.stderr)
                self.assertFalse(output.exists())

    def test_improved_and_tournament_entry_points(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.txt'
            output=Path(folder)/'output.txt'
            position='xxxxxBxWWWWWBBBBxxxxxxx'
            source.write_text(position)
            for name,phase in [('MiniMaxOpeningImproved','opening'),('MiniMaxGameImproved','midgame'),('TournamentAgent','midgame')]:
                command=[sys.executable,str(ROOT/'programs'/f'{name}.py'),str(source),str(output),'2']
                if name=='TournamentAgent':
                    command+=['black',phase,'--seconds','1']
                run=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertEqual(len(run.stdout.splitlines()),3)
                self.assertIn(output.read_text().strip(),legal_moves(position,phase,name!='TournamentAgent'))

#!/usr/bin/env python3
"""Build the requested layout and smoke-test all entry points after extraction."""
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    destination=ROOT/'dist/Morris-AI-submission.zip'
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for script in sorted((ROOT/'programs').glob('*.py')):
            archive.write(script,script.name)
        for module in sorted((ROOT/'morris').glob('*.py')):
            archive.write(module,'morris/'+module.name)
        for name in ('Examples.txt','MyStaticEstimation.txt'):
            archive.write(ROOT/'deliverables'/name,name)
        archive.writestr('SUBMISSION_NOTES.txt',
            'Python 3.10+, standard library only. Keep morris/ beside the scripts.\n'
            'Run: python3 MiniMaxOpening.py input.txt output.txt 2\n'
            'Tournament console: python3 TournamentAgent.py   (no arguments; interactive)\n'
            'Tournament single move: python3 TournamentAgent.py input.txt output.txt 12 white opening --history game.json --seconds 180\n'
            'Use a new history file per game; opening without history requires --placements N.\n'
            'Capture exception: Variant p. 4 is interpreted as retaining the move without capture when no opponent is outside a mill.\n'
            'This interpretation is not an instructor-confirmed clarification.\n'
            'Depth 0 evaluates without making a move in assignment programs; tournament requires depth >= 1.\n'
            'Tournament diagnostics use stderr; the required three lines use stdout.\n')
    with tempfile.TemporaryDirectory() as folder:
        clean=Path(folder)
        with zipfile.ZipFile(destination) as archive:
            archive.extractall(clean)
        source=clean/'input.txt'
        source.write_text('xxxxxBxWWWWWBBBBxxxxxxx\n')
        for script in sorted(clean.glob('*.py')):
            output=clean/'output.txt'
            command=[sys.executable,script.name,'input.txt','output.txt','2']
            if script.stem=='TournamentAgent':
                command+=['white','midgame','--seconds','1']
            result=subprocess.run(command,cwd=clean,capture_output=True,text=True,timeout=10)
            if result.returncode:
                raise RuntimeError(f'{script.name}: {result.stderr}')
            lines=result.stdout.splitlines()
            board=output.read_text().strip()
            assert len(lines)==3 and len(board)==23
            assert lines[0]=='Board Position: '+board
            assert lines[1].startswith('Positions evaluated by static estimation: ')
            assert lines[2].startswith('MINIMAX estimate: ')
            print('PASS',script.name)
    print('Created and verified:',destination)


if __name__=='__main__':
    main()

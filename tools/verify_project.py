#!/usr/bin/env python3
"""Reproduce examples, timings, and complete local games. Standard library only."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from morris.board import swap_colors, LOCATIONS
from morris.estimation import static_estimate_opening, static_estimate_midgame_endgame
from morris.improved import static_estimate_opening_improved, static_estimate_midgame_endgame_improved, differences
from morris.search import minimax, alphabeta, legal_moves
from morris.tournament import choose_move, initial_state, next_state, game_result, validate_history, phase_for

P1='xxxxxBxWWWWWBBBBxxxxxxx'
P2='WxWWxWWWWWBBBBBBBBxxxxx'
BOARD_FILES={P1:'handout_position_1.txt',P2:'handout_position_2.txt'}


def move_description(before,after):
    """Describe a White move: placement or slide, then any capture."""
    changed=lambda old,new: [LOCATIONS[i] for i,(a,b) in enumerate(zip(before,after)) if (a,b)==(old,new)]
    left,arrived,removed=changed('W','x'),changed('x','W'),changed('B','x')
    text=f'White moves {left[0]} to {arrived[0]}' if left else f'White places a piece at {arrived[0]}'
    if removed:
        text+=f' and removes the Black piece at {removed[0]}'
    return text


def program_output(script,position,depth,expected):
    """Run a submitted program and return its command and stdout lines."""
    name=BOARD_FILES[position]
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'board2.txt'
        run=subprocess.run([sys.executable,str(ROOT/'programs'/script),str(ROOT/'examples'/name),str(output),str(depth)],
                           capture_output=True,text=True,check=True)
        assert output.read_text().strip()==expected[0]
    lines=run.stdout.splitlines()
    assert lines==[f'Board Position: {expected[0]}',
                   f'Positions evaluated by static estimation: {expected[1]}',
                   f'MINIMAX estimate: {expected[2]}']
    return [f'  $ python3 {script} {name} board2.txt {depth}']+['  '+line for line in lines]


def write_examples():
    lines=['CS4346 Morris AI - Examples.txt',
           '',
           'This file answers two requirements of the project handout:',
           '  Part II: at least two cases where ALPHA-BETA evaluates fewer positions than MINIMAX,',
           '           with the same MINIMAX estimate and the same move.',
           '  Part IV: at least two board positions where the improved static estimation selects',
           '           a different move than the original one, with a reason for preferring it.',
           '',
           'Each case shows the exact command and the three lines the submitted program printed.',
           'Input files are the two positions drawn in the Morris Variant handout:',
           f'  handout_position_1.txt = {P1}',
           f'  handout_position_2.txt = {P2}',
           'Depth counts individual turns (plies). "Positions evaluated" counts calls to the static estimator.',
           'Capture rule used: when every opposing piece is in a mill, the mill-closing move is kept',
           'without a capture (last line of GenerateRemove, Variant p. 4).',
           'Regenerate: python3 tools/verify_project.py --examples-only',
           '','',
           'PART II: ALPHA-BETA EVALUATES FEWER POSITIONS THAN MINIMAX']
    pruning=[(P1,'opening',static_estimate_opening,'MiniMaxOpening.py','ABOpening.py'),
             (P2,'midgame',static_estimate_midgame_endgame,'MiniMaxGame.py','ABGame.py')]
    for number,(position,phase,estimate,mm_script,ab_script) in enumerate(pruning,1):
        depth=3
        mm=minimax(position,depth,phase=phase,estimate=estimate)
        ab=alphabeta(position,depth,phase=phase,estimate=estimate)
        assert (mm[0],mm[2])==(ab[0],ab[2]) and ab[1]<mm[1]
        saved=100*(mm[1]-ab[1])//mm[1]
        lines += ['',f'Case {number} ({phase}, depth {depth})',f'Input board: {position}','',
                  'MINIMAX:']+program_output(mm_script,position,depth,mm)+['',
                  'ALPHA-BETA:']+program_output(ab_script,position,depth,ab)+['',
                  f'Selected move: {move_description(position,mm[0])}',
                  f'Same move and same MINIMAX estimate ({mm[2]}). Alpha-beta evaluated {ab[1]} positions '
                  f'instead of {mm[1]} ({saved}% fewer).',
                  'Alpha-beta stops exploring a branch once it cannot change the decision above it.',
                  'Both searches try moves in the same order and keep the first move on a tie.']
    lines += ['','','PART IV: IMPROVED STATIC ESTIMATION SELECTS A DIFFERENT MOVE',
              'Scores from the two estimators use different scales. Compare the chosen moves, not the numbers.']
    cases=[(P2,'opening',static_estimate_opening,static_estimate_opening_improved,
            'MiniMaxOpening.py','MiniMaxOpeningImproved.py',
            'Both moves close a mill and remove the same Black piece, so the original function gives them the same '
            'score and keeps the first one, d0. The improved function prefers a6, which lies on three mill lines, '
            'over d0, which lies on one. After the move White\'s connection advantage is 7 instead of 5 and its '
            'mobility advantage is +2 instead of 0, so White has more ways to build its next mill. '
            'The search also checked Black\'s reply at depth 2.'),
           (P1,'midgame',static_estimate_midgame_endgame,static_estimate_midgame_endgame_improved,
            'MiniMaxGame.py','MiniMaxGameImproved.py',
            'The improved move opens White\'s a3-b3-c3 mill by sliding b3 to b5. The piece can slide back next turn '
            'to close the mill again, which is a real capture threat: the threat difference becomes +1 instead of 0. '
            'It also gives White more freedom: mobility +3 instead of +1, and one fewer blocked piece than Black '
            'instead of an equal number. The original move, e3 to e4, keeps the mill closed but leaves White with '
            'fewer moves and no threat. These are positional reasons, not a proof of a forced win.')]
    for number,(position,phase,base,better,base_script,better_script,reason) in enumerate(cases,1):
        old=minimax(position,2,phase=phase,estimate=base)
        new=minimax(position,2,phase=phase,estimate=better)
        assert old[0]!=new[0]
        lines += ['',f'Case {number} ({phase}, depth 2)',f'Input board: {position}','',
                  'ORIGINAL ESTIMATION:']+program_output(base_script,position,2,old)+[
                  f'  Move: {move_description(position,old[0])}','',
                  'IMPROVED ESTIMATION:']+program_output(better_script,position,2,new)+[
                  f'  Move: {move_description(position,new[0])}','',
                  'Feature differences after each move (White minus Black):',
                  f'  original move: {differences(old[0])}',
                  f'  improved move: {differences(new[0])}','',
                  f'Why the improved move is preferred: {reason}']
    (ROOT/'deliverables/Examples.txt').write_text('\n'.join(lines)+'\n')
    estimation=(ROOT/'deliverables/MyStaticEstimation.txt').read_text()
    for position,phase,base,better,*_ in cases:
        for estimate in (base,better):
            assert minimax(position,2,phase=phase,estimate=estimate)[0] in estimation, \
                'MyStaticEstimation.txt quotes a move the programs no longer choose'


def play_game(seed, improved_color=None, depth=2, max_plies=240):
    """Four seeded legal opening moves diversify tests; then agents take over.

    improved_color=None means the timed tournament agent plays both colors.
    Otherwise compare the improved and baseline evaluators at the same depth.
    The test cap is reported as unfinished, never invented as a draw rule.
    """
    rng=random.Random(seed)
    history=[initial_state()]
    times=[]
    for _ in range(4):
        state=history[-1]
        move=rng.choice(legal_moves(state['board'],'opening',state['side']=='white'))
        history.append(next_state(state,move))
    while len(history)-1 < max_plies and game_result(history) is None:
        state=history[-1]
        side=state['side']
        start=perf_counter()
        if improved_color is None:
            decision=choose_move(state['board'],side,state['placements'],depth,2.0,history)
            move=decision.board
        else:
            better=side==improved_color
            opening=static_estimate_opening_improved if better else static_estimate_opening
            game=static_estimate_midgame_endgame_improved if better else static_estimate_midgame_endgame
            query=swap_colors(state['board']) if side=='black' else state['board']
            repeats=Counter()
            for item in history:
                position=swap_colors(item['board']) if side=='black' else item['board']
                repeats[(position,item['side']==side)]+=1
            phase=phase_for(state['placements'])
            move,_,_=alphabeta(query,depth,phase=phase,estimate=opening if phase=='opening' else game,
                               placements=state['placements'],game_estimate=game,repetitions=repeats)
            if side=='black':
                move=swap_colors(move)
        times.append(perf_counter()-start)
        assert move in legal_moves(state['board'],phase_for(state['placements']),side=='white')
        history.append(next_state(state,move))
    validate_history(history)
    result=game_result(history)
    return {'seed':seed,'improved_color':improved_color or 'both','depth':depth,
            'result':result or 'unfinished at test cap','plies':len(history)-1,
            'slowest_move_seconds':round(max(times),6),'history':history}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--examples-only',action='store_true')
    args=parser.parse_args()
    write_examples()
    if args.examples_only:
        return
    benchmarks=[]
    for label,position,color,placements in [('empty opening','x'*23,'white',0),('midgame',P1,'white',18),
                                             ('hopping','WWxxxxxxBBBxxxxxxxBxxWx','white',18)]:
        for depth in (2,3,4):
            result=choose_move(position,color,placements,depth,1.0)
            benchmarks.append({'case':label,'requested_depth':depth,'completed_depth':result.completed_depth,
                               'seconds':round(result.elapsed,6),'evaluations':result.evaluated,'timed_out':result.timed_out})
    matches=[]
    for seed in (7,4346):
        for color in ('white','black'):
            match=play_game(seed,color)
            matches.append(match)
            print({k:v for k,v in match.items() if k!='history'},flush=True)
    for seed in (12,19):
        match=play_game(seed)
        matches.append(match)
        print({k:v for k,v in match.items() if k!='history'},flush=True)
    payload={'benchmarks':benchmarks,'games':matches}
    (ROOT/'deliverables/validation.json').write_text(json.dumps(payload,indent=2)+'\n')
    lines=['LOCAL VALIDATION - not official tournament results',
           'Run: python3 -m unittest discover -s tests -v; python3 tools/verify_project.py',
           'Timings are measurements on this machine, not guarantees on another machine.',
           'Search budget in timing cases: 1 second. No transposition table or move sorting.', '', 'TIMINGS']
    lines += [str(item) for item in benchmarks]
    lines += ['', 'GAMES', 'First four moves are seeded legal placements. Every subsequent move and the full history are validated.',
              'Four games compare evaluators at depth 2, using the same alpha-beta and swapped colors.',
              'Two games use the timed tournament runner for both colors. A test cap is not a game rule.']
    lines += [str({k:v for k,v in item.items() if k!='history'}) for item in matches]
    lines += ['', 'This small deterministic sample is a regression check, not statistical proof of superiority.',
              'Opponent implementations and deeper searches may perform differently. Retune only after measured comparisons.']
    (ROOT/'deliverables/Validation.txt').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Reproduce examples, timings, and complete local games. Standard library only."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import sys
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


def move_description(before,after):
    return ', '.join(f'{LOCATIONS[i]}: {a}->{b}' for i,(a,b) in enumerate(zip(before,after)) if a!=b)


def write_examples():
    lines=['CS4346 Morris AI - reproducible examples',
           'Rule: when every opposing piece is in a mill, retain the move without capture (Variant p. 4).',
           'Depth counts individual turns. Counts are actual static-estimator calls.',
           'Run: python3 tools/verify_project.py --examples-only', '',
           'PART II: ALPHA-BETA PRUNING']
    for number,(position,phase,estimate) in enumerate([(P1,'opening',static_estimate_opening),(P2,'midgame',static_estimate_midgame_endgame)],1):
        depth=3
        mm=minimax(position,depth,phase=phase,estimate=estimate)
        ab=alphabeta(position,depth,phase=phase,estimate=estimate)
        assert (mm[0],mm[2])==(ab[0],ab[2]) and ab[1]<mm[1]
        lines += ['',f'Case {number}',f'Input board: {position}',f'Phase: {phase}',f'Depth: {depth}',
                  f'Both selected: {mm[0]}',f'Move: {move_description(position,mm[0])}',
                  f'Shared MINIMAX estimate: {mm[2]}',f'Minimax evaluations: {mm[1]}',f'Alpha-beta evaluations: {ab[1]}',
                  'Alpha-beta skips branches that cannot change the decision; strict comparisons preserve the first tied move.']
    lines += ['','PART IV: IMPROVED EVALUATION']
    cases=[(P2,'opening',static_estimate_opening,static_estimate_opening_improved,
            'Both choices capture a Black piece. The improved choice places at a6, which participates in three mill lines; '
            'the baseline places at d0, which participates in one. After the selected move the White-minus-Black '
            'mill-incidence count is 7 rather than 5. This gives more future mill connections. '
            'The decision also considers the opponent\'s reply at depth 2.'),
           (P1,'midgame',static_estimate_midgame_endgame,static_estimate_midgame_endgame_improved,
            'The improved move slides b3 to b5, opening the existing a3-b3-c3 mill. It preserves the ability to '
            'slide back and reform that mill while increasing movement options. Its mobility difference is +3 '
            'rather than +1, its blocked-piece difference is -1 rather than 0, and its legal mill-threat difference '
            'is +1 rather than 0. The baseline instead slides e3 to e4. The new evaluator values active threats '
            'and freedom of movement as well as material. These are positional reasons, not a proof of a forced win.')]
    for number,(position,phase,base,better,reason) in enumerate(cases,1):
        old=minimax(position,2,phase=phase,estimate=base)
        new=minimax(position,2,phase=phase,estimate=better)
        assert old[0]!=new[0]
        lines += ['',f'Case {number}',f'Input board: {position}',f'Phase: {phase}','Depth: 2',
                  f'Baseline move: {old[0]}',f'Baseline change: {move_description(position,old[0])}',f'Baseline estimate: {old[2]}',
                  f'Improved move: {new[0]}',f'Improved change: {move_description(position,new[0])}',f'Improved estimate: {new[2]}',
                  'Scores use different scales; compare choices, not their numerical magnitudes.',
                  f'Improved immediate-board feature differences: {differences(new[0])}',f'Why preferred: {reason}']
    (ROOT/'deliverables/Examples.txt').write_text('\n'.join(lines)+'\n')


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

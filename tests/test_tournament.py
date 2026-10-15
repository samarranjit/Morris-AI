import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from morris.board import swap_colors
from morris.search import alphabeta, legal_moves, SearchTimeout
from morris.tournament import (
    choose_move, game_result, initial_state, next_state,
    validate_history, load_history, save_history,
)
from test_moves import board


def opening_history(seed=4346):
    rng=random.Random(seed)
    history=[initial_state()]
    for _ in range(18):
        current=history[-1]
        move=rng.choice(legal_moves(current['board'],'opening',current['side']=='white'))
        history.append(next_state(current,move))
    return history


class TournamentTests(unittest.TestCase):
    def test_timeout_keeps_legal_fallback(self):
        decision=choose_move('x'*23,'white',0,8,0)
        self.assertTrue(decision.timed_out)
        self.assertEqual(decision.completed_depth,0)
        self.assertIn(decision.board,legal_moves('x'*23,'opening',True))

    def test_timeout_keeps_last_completed_iteration(self):
        position='x'*23
        from morris.tournament import alphabeta as real_search
        def controlled(*args,**kwargs):
            if args[1] == 2:
                raise SearchTimeout()
            return real_search(*args,**kwargs)
        expected=choose_move(position,'white',0,1,5)
        with patch('morris.tournament.alphabeta',side_effect=controlled):
            decision=choose_move(position,'white',0,8,5)
        self.assertEqual(decision.completed_depth,1)
        self.assertEqual(decision.board,expected.board)
        self.assertTrue(decision.timed_out)

    def test_phase_transition_uses_midgame_evaluator(self):
        position='WxWWxWWWWWBBBBBBBBxxxxx'
        calls=[]
        def opening(p):
            self.fail('depth 2 from placement 16 must reach midgame')
        def game(p):
            calls.append(p)
            return 123
        _,count,value=alphabeta(position,2,phase='opening',estimate=opening,
                                placements=16,game_estimate=game)
        self.assertEqual(value,123)
        self.assertEqual(count,len(calls))
        self.assertTrue(calls)

    def test_threefold_search_counts_side_to_move(self):
        position='xxxxxBxWWWWWBBBBxxxxxxx'
        result=alphabeta(position,2,phase='midgame',estimate=lambda p:77,
                         repetitions={(position,True):3})
        self.assertEqual(result,(position,1,0))
        result=alphabeta(position,0,phase='midgame',estimate=lambda p:77,
                         repetitions={(position,False):3})
        self.assertEqual(result[2],77)

    def test_history_opponent_validation_and_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'match.json'
            history=load_history(path,'x'*23,'white')
            first=legal_moves('x'*23,'opening',True)[0]
            history.append(next_state(history[-1],first))
            save_history(path,history)
            self.assertEqual(load_history(path,'x'*23,'white'),[initial_state()])
            second=legal_moves(first,'opening',False)[0]
            loaded=load_history(path,second,'white')
            self.assertEqual(loaded[-1]['placements'],2)
            validate_history(loaded)
            with self.assertRaises(ValueError):
                load_history(path,'B'+'x'*22,'white')

    def test_valid_history_through_opening(self):
        history=opening_history()
        self.assertEqual(validate_history(history),history)
        self.assertEqual(history[-1]['placements'],18)
        damaged=json.loads(json.dumps(history))
        damaged[5]['placements']=6
        with self.assertRaises(ValueError):
            validate_history(damaged)

    def test_no_move_after_terminal(self):
        with self.assertRaises(ValueError):
            choose_move(board([0,1,2],[8,9]),'white',18,2,1)

    def test_black_midgame_color_swap(self):
        position='xxxxxBxWWWWWBBBBxxxxxxx'
        black=choose_move(position,'black',18,2,5)
        white=choose_move(swap_colors(position),'white',18,2,5)
        self.assertEqual(black.board,swap_colors(white.board))
        self.assertEqual(black.value,white.value)

    def test_reject_inconsistent_opening_state(self):
        with self.assertRaises(ValueError):
            choose_move('x'*23,'black',0,2,1)
        with self.assertRaises(ValueError):
            choose_move('WW'+'x'*21,'white',0,2,1)

    def test_repetition_result_includes_side(self):
        state={'board':'xxxxxBxWWWWWBBBBxxxxxxx','side':'white','placements':18}
        other=dict(state,side='black')
        self.assertIsNone(game_result([state,other,state]))
        self.assertEqual(game_result([state,other,state,other,state]),'draw')

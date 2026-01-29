import unittest
import os
import random
from lexcel import LExcel, Board, VIOLET, CYAN
from openpyxl.utils import column_index_from_string


class TestLexcel(unittest.TestCase):

    def setUp(self):
        self.EMPTY_EXP = 'tests/exapawn-empty.xlsx'
        self.TMP = 'tests/test-exapawn-tmp.xlsx'
        self.RAND = random.Random(42)
        self.e = LExcel(self.EMPTY_EXP)

    def tearDown(self):
        if os.path.isfile(self.TMP):
            os.remove(self.TMP)

    def test_find_board_column(self):
        cell = self.e.find_board_column(2, '5BB')
        self.assertEqual(cell, column_index_from_string('A'))

        cell = self.e.find_board_column(4, '38B')
        self.assertEqual(cell, column_index_from_string('E'))

        cell = self.e.find_board_column(6, '830')
        self.assertEqual(cell, column_index_from_string('Y'))

    def test_get_moves(self):
        moves, weights = self.e.get_moves(Board('38B'), 4, VIOLET)
        self.assertEqual(len(moves), 6)
        self.assertIn('YY', moves)
        self.assertIn('YX', moves)
        self.assertIn('YZ', moves)
        self.assertIn('ZZ', moves)
        self.assertIn('XX', moves)  # illegal, weight 0
        self.assertIn('XY', moves)  # illegal, weight 0
        self.assertEqual(sum(weights), 4)

    def test_choose_and_remember_move(self):
        match = []
        move = self.e.choose_and_remember_move(Board('895'),
                                               4, match, self.RAND, VIOLET)
        self.assertTrue(move == 'XX' or move == 'XY')
        self.assertEqual(match, [(move, '895', 4)])

    def test_choose_and_remember_move_reproducibile(self):
        match = []
        myrand = random.Random(666)
        old = []
        for j in range(10):
            old.append(self.e.choose_and_remember_move(Board('83B'),
                                                       4,
                                                       match, myrand, VIOLET))

        for i in range(2):
            myrand = random.Random(666)
            for j in range(10):
                move = self.e.choose_and_remember_move(Board('83B'),
                                                       4,
                                                       match, myrand, VIOLET)
                self.assertEqual(move, old[j])

    def test_reward(self):
        match = []
        self.e.choose_and_remember_move(Board('895'),
                                        4, match, self.RAND, VIOLET)
        self.e.reward(self.TMP, match, 1)
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board('895'), 4, VIOLET)
        self.assertIn(2, weights)

    def test_punish(self):
        match = []
        self.e.choose_and_remember_move(Board('895'),
                                        4, match, self.RAND, VIOLET)
        self.e.reward(self.TMP, match, -1)
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board('895'), 4, VIOLET)
        self.assertIn(0, weights)

    def test_get_moves_flipped(self):
        r = self.e.get_moves(Board('B83'), 4, VIOLET)
        self.assertIsNone(r)

    def test_choose_and_remember_move_flipped(self):
        match = []
        move = self.e.choose_and_remember_move(Board('335'),
                                               6, match, self.RAND, VIOLET)
        self.assertEqual(move, 'ZY')
        self.assertEqual(match, [(Board('533').flip_move(move), '533', 6)])
        col = self.e.find_board_column(6, match[0][1])
        self.assertIsNotNone(col)

    def test_reward_flipped(self):
        match = []
        self.e.choose_and_remember_move(Board('55F'), 4, match, self.RAND, VIOLET)
        self.e.reward(self.TMP, match, 1)
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board('F55'), 4, VIOLET)
        self.assertIn(2, weights)

    def test_make_empty_experience(self):
        LExcel.make_empty_experience(len('B38'), self.TMP, [VIOLET, CYAN])
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board('B38'), 4, VIOLET)
        self.assertEqual(len(moves), 4)
        self.assertEqual(sum(weights), 4)

    @unittest.skip("old")
    def test_make_empty_experience4(self):
        LExcel.make_empty_experience(4, self.TMP, [VIOLET, CYAN])
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board(ncols=4), 1, CYAN)
        self.assertEqual(len(moves), 2)
        self.assertEqual(sum(weights), 2)

    @unittest.skip("old")
    def test_make_empty_experience5(self):
        LExcel.make_empty_experience(5, self.TMP, [VIOLET, CYAN])
        self.assertTrue(os.path.isfile(self.TMP))
        t = LExcel(self.TMP)
        moves, weights = t.get_moves(Board(ncols=5), 1, CYAN)
        self.assertEqual(len(moves), 3)
        self.assertEqual(sum(weights), 3)


if __name__ == '__main__':
    unittest.main()

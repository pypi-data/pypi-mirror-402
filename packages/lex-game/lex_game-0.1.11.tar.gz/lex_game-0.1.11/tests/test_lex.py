from lexcel import Board, VIOLET, CYAN, EMPTY, pawns_to_code, other, Base256
import unittest


class TestBase256(unittest.TestCase):
    def setUp(self):
        self.b256 = Base256()

    def test_to_int0(self):
        r = self.b256.to_int('0000000')
        self.assertEqual(r, 0)

    def test_to_intBA7(self):
        r = self.b256.to_int('BA7')
        self.assertEqual(r, 7 + 10*256 + 11*256**2)

    def test_to_code1(self):
        r = self.b256.from_int(10)
        self.assertEqual(r, 'A')

    def test_to_code36(self):
        r = self.b256.from_int(10 + 26)
        self.assertEqual(r, 'a')

    def test_to_code255(self):
        r = self.b256.from_int(255)
        self.assertEqual(r, self.b256.SYMBOLS[-1])

    def test_to_code255_255(self):
        r = self.b256.from_int(256**2 - 1)
        self.assertEqual(r, self.b256.SYMBOLS[-1]*2)


class TestLexCommon(unittest.TestCase):
    basic_case = {
        'X': [VIOLET, CYAN, EMPTY],
        'Y': [EMPTY, CYAN, CYAN],
        'Z': [VIOLET, EMPTY, EMPTY]
    }

    def setUp(self):
        self.board = Board(pawns_to_code(self.basic_case))
        self.b256 = Base256()

    def test_str(self):
        r = str(self.board)
        line_len = 4*len(self.board.COLS) + 1
        n_lines = self.board.NROWS * 2 + 2
        caption_len = len("Board code: ") + len(self.board.COLS)
        self.assertEqual(len(r),
                         line_len * n_lines
                         + 2*(n_lines+1)
                         + caption_len)

    def test_to_code_flip(self):
        r = self.board.flip().get_code()
        self.assertEqual(r, self.board.get_code()[::-1])

    def test_items(self):
        self.assertEqual(self.board['X'], self.basic_case['X'])
        with self.assertRaises(TypeError) as e:
            self.board['X'] = None
        self.assertEqual(str(e.exception), "'Board' objects are immutable!")

    def test_exchange(self):
        r = self.board.exchange()
        self.assertEqual(r['X'], [other(i) for i in self.board['X'][::-1]])
        self.assertNotEqual(r, self.board)
        r = r.exchange()
        self.assertEqual(r, self.board)

    def test_flip(self):
        r = self.board.flip()
        self.assertNotEqual(r, self.board)
        for i, c in enumerate(self.board.COLS):
            x = self.board.COLS[i]
            z = self.board.COLS[-(i+1)]
            self.assertEqual(r[x], self.board[z])

    def test_flip_move_prop(self):
        for m in self.board.WELL_FORMED_MOVES:
            fm = self.board.flip_move(m)
            self.assertEqual(m, self.board.flip_move(fm))


class TestLexFunctions(unittest.TestCase):

    def test_pawns_to_code1(self):
        b = {'X': [EMPTY, EMPTY, EMPTY]}
        self.assertEqual(pawns_to_code(b), "0")
        b = {'X': [CYAN, EMPTY, EMPTY]}
        self.assertEqual(pawns_to_code(b), "1")
        b = {'X': [EMPTY, CYAN, EMPTY]}
        self.assertEqual(pawns_to_code(b), "3")
        b = {'X': [EMPTY, EMPTY, CYAN]}
        self.assertEqual(pawns_to_code(b), "9")
        b = {'X': [VIOLET, EMPTY, EMPTY]}
        self.assertEqual(pawns_to_code(b), "2")
        b = {'X': [EMPTY, VIOLET, EMPTY]}
        self.assertEqual(pawns_to_code(b), "6")
        b = {'X': [EMPTY, EMPTY, VIOLET]}
        self.assertEqual(pawns_to_code(b), "I")

    def test_pawns_to_code2(self):
        w = {
            'X': [EMPTY, VIOLET, EMPTY],
            'Y': [EMPTY, EMPTY, VIOLET],
            'Z': [EMPTY, CYAN, EMPTY]
        }
        self.assertEqual(pawns_to_code(w), "6I3")

    def test_other(self):
        self.assertEqual(other(VIOLET), CYAN)
        self.assertEqual(other(CYAN), VIOLET)
        self.assertEqual(other(EMPTY), EMPTY)


class TestBoard3(TestLexCommon):

    def test_hash(self):
        b1 = Board()
        b2 = Board("5C2")
        self.assertEqual(hash(self.board),
                         self.b256.to_int("5C2"))
        self.assertNotEqual(b1, self.board)
        self.assertEqual(b2, self.board)

    def test_can_move_fwd_violet(self):
        self.assertTrue(self.board.can_move_fwd(VIOLET, 'Z'))
        self.assertFalse(self.board.can_move_fwd(VIOLET, 'X'))

    def test_can_move_fwd_cyan(self):
        self.assertTrue(self.board.can_move_fwd(CYAN, 'Y'))
        self.assertFalse(self.board.can_move_fwd(CYAN, 'X'))

    def test_can_capture_violet(self):
        self.assertTrue(self.board.can_capture(VIOLET, 'X'))
        self.assertTrue(self.board.can_capture(VIOLET, 'Z'))
        self.assertFalse(self.board.can_capture(VIOLET, 'Y'))

    def test_can_capture_cyan(self):
        self.assertFalse(self.board.can_capture(CYAN, 'X'))
        self.assertFalse(self.board.can_capture(CYAN, 'Z'))
        self.assertTrue(self.board.can_capture(CYAN, 'Y'))

    def test_winner1(self):
        w = {
            'X': [EMPTY, VIOLET, EMPTY],
            'Y': [EMPTY, EMPTY, VIOLET],
            'Z': [EMPTY, CYAN, EMPTY]
        }
        vw = Board(pawns_to_code(w))
        self.assertTrue(vw.is_winner(VIOLET))
        self.assertFalse(vw.is_winner(CYAN))

    def test_winner2(self):
        w = {
            'X': [EMPTY, VIOLET, CYAN],
            'Y': [EMPTY, EMPTY, EMPTY],
            'Z': [VIOLET, CYAN, EMPTY]
        }
        cvw = Board(pawns_to_code(w))
        for c in w:
            self.assertFalse(cvw.can_move_fwd(CYAN, c))
            self.assertFalse(cvw.can_capture(CYAN, c))

        self.assertTrue(cvw.is_winner(VIOLET))
        self.assertTrue(cvw.is_winner(CYAN))

    def test_move1(self):
        r = self.board.move(VIOLET, 'Z', 'Z')
        self.assertEqual(r['X'], self.board['X'])
        self.assertEqual(r['Y'], self.board['Y'])
        self.assertEqual(r['Z'], [EMPTY, VIOLET, EMPTY])

    def test_move2(self):
        r = self.board.move(VIOLET, 'X', 'Y')
        self.assertEqual(r['X'], [EMPTY, CYAN, EMPTY])
        self.assertEqual(r['Y'], [EMPTY, VIOLET, CYAN])
        self.assertEqual(r['Z'], self.board['Z'])

    def test_move3(self):
        r = self.board.move(VIOLET, 'Z', 'Y')
        self.assertEqual(r['X'], self.board['X'])
        self.assertEqual(r['Y'], [EMPTY, VIOLET, CYAN])
        self.assertEqual(r['Z'], [EMPTY, EMPTY, EMPTY])

    def test_move4(self):
        b = {
            'X': [EMPTY, CYAN, EMPTY],
            'Y': [VIOLET, VIOLET, EMPTY],
            'Z': [VIOLET, EMPTY, CYAN]
        }
        board = Board(pawns_to_code(b))
        r = board.move(VIOLET, 'Y', 'Y')
        self.assertEqual(r['X'], board['X'])
        self.assertEqual(r['Y'], [VIOLET, EMPTY, VIOLET])
        self.assertEqual(r['Z'], board['Z'])

    def test_move5(self):
        b = {
            'X': [EMPTY, CYAN, EMPTY],
            'Y': [VIOLET, VIOLET, EMPTY],
            'Z': [VIOLET, EMPTY, CYAN]
        }
        board = Board(pawns_to_code(b))
        r = board.move(VIOLET, 'Y', 'X')
        self.assertEqual(r['X'], [EMPTY, VIOLET, EMPTY])
        self.assertEqual(r['Y'], [EMPTY, VIOLET, EMPTY])
        self.assertEqual(r['Z'], board['Z'])

    def test_move6(self):
        b = {
            'X': [EMPTY, CYAN, EMPTY],
            'Y': [VIOLET, VIOLET, EMPTY],
            'Z': [VIOLET, EMPTY, CYAN]
        }
        board = Board(pawns_to_code(b))
        r = board.move(VIOLET, 'Y', 'Z')
        self.assertEqual(r['X'], board['X'])
        self.assertEqual(r['Y'], [VIOLET, EMPTY, EMPTY])
        self.assertEqual(r['Z'], [VIOLET, EMPTY, VIOLET])

    def test_move7(self):
        b = {
            'X': [EMPTY, VIOLET, CYAN],
            'Y': [VIOLET, CYAN, EMPTY],
            'Z': [VIOLET, CYAN, EMPTY]
        }
        board = Board(pawns_to_code(b))
        r = board.move(VIOLET, 'Y', 'Z')
        self.assertEqual(r['X'], board['X'])
        self.assertEqual(r['Y'], [EMPTY, CYAN, EMPTY])
        self.assertEqual(r['Z'], [VIOLET, VIOLET, EMPTY])

    def test_move8(self):
        b = {
            'X': [EMPTY, VIOLET, CYAN],
            'Y': [VIOLET, CYAN, EMPTY],
            'Z': [VIOLET, CYAN, EMPTY]
        }
        board = Board(pawns_to_code(b))
        r = board.move(VIOLET, 'Z', 'Y')
        self.assertEqual(r['X'], board['X'])
        self.assertEqual(r['Y'], [VIOLET, VIOLET, EMPTY])
        self.assertEqual(r['Z'], [EMPTY, CYAN, EMPTY])

    def test_move9(self):
        b = Board()
        r = b.move(CYAN, 'X', 'X')
        self.assertEqual(r['X'], [VIOLET, CYAN, EMPTY])
        self.assertEqual(r['Y'], b['Y'])
        self.assertEqual(r['Z'], b['Z'])

    def test_is_symmetrical(self):
        b = Board('B5B')
        self.assertTrue(b.is_symmetrical())

    def test_prune_sym_moves(self):
        self.assertEqual(len(self.board.prune_sym_moves(['XX', 'ZZ'])), 1)

    def test_prune_sym_moves3(self):
        r = self.board.prune_sym_moves(['XX', 'XY', 'ZY'])
        self.assertEqual(len(r), 2)

    def test_get_legal_moves1(self):
        r = self.board.get_legal_moves(CYAN)
        self.assertEqual(len(r), 3)
        self.assertIn('YX', r)
        self.assertIn('YY', r)
        self.assertIn('YZ', r)

    def test_get_legal_moves2(self):
        r = self.board.get_legal_moves(VIOLET)
        self.assertEqual(len(r), 3)
        self.assertIn('XY', r)
        self.assertIn('ZY', r)
        self.assertIn('ZZ', r)

    def test_flip_move(self):
        r = self.board.flip_move('XX')
        self.assertEqual(r, 'ZZ')
        r = self.board.flip_move('XY')
        self.assertEqual(r, 'ZY')
        r = self.board.flip_move('YZ')
        self.assertEqual(r, 'YX')
        r = self.board.flip_move('YY')
        self.assertEqual(r, 'YY')

    def test_get_forest(self):
        _, b = Board.get_forest(3)
        turn2 = dict([(x, b[x]) for x in b if b[x][0] == 2])
        self.assertEqual(len(turn2), 2)
        self.assertIn('B5B', turn2)
        self.assertEqual(len(turn2['B5B']), 2)


class TestBoard4(TestLexCommon):
    basic_case = {
        'W': [EMPTY, VIOLET, CYAN, EMPTY],
        'X': [VIOLET, EMPTY, EMPTY, EMPTY],
        'Y': [EMPTY, CYAN, EMPTY, CYAN],
        'Z': [EMPTY, VIOLET, CYAN, EMPTY]
    }

    def test_hash(self):
        b1 = Board(ncols=4)
        b2 = Board("F2UF")
        self.assertEqual(hash(self.board), self.b256.to_int('F2UF'))
        self.assertNotEqual(b1, self.board)
        self.assertEqual(b2, self.board)

    def test_can_capture_violet(self):
        self.assertTrue(self.board.can_capture(VIOLET, 'X'))
        self.assertFalse(self.board.can_capture(VIOLET, 'Z'))
        self.assertFalse(self.board.can_capture(VIOLET, 'Y'))
        self.assertFalse(self.board.can_capture(VIOLET, 'W'))

    def test_can_capture_cyan(self):
        self.assertFalse(self.board.can_capture(CYAN, 'X'))
        self.assertFalse(self.board.can_capture(CYAN, 'Z'))
        self.assertTrue(self.board.can_capture(CYAN, 'Y'))
        self.assertFalse(self.board.can_capture(CYAN, 'W'))

    def test_winner1(self):
        w = {
            'W': [EMPTY, VIOLET, EMPTY, CYAN],
            'X': [EMPTY, VIOLET, CYAN, EMPTY],
            'Y': [EMPTY, EMPTY, EMPTY, VIOLET],
            'Z': [EMPTY, CYAN, EMPTY, EMPTY]
        }
        vw = Board(pawns_to_code(w))
        self.assertTrue(vw.is_winner(VIOLET))
        self.assertFalse(vw.is_winner(CYAN))

    def test_winner2(self):
        w = {
            'W': [EMPTY, EMPTY, EMPTY, EMPTY],
            'X': [EMPTY, VIOLET, CYAN, EMPTY],
            'Y': [EMPTY, EMPTY, EMPTY, EMPTY],
            'Z': [VIOLET, CYAN, EMPTY, EMPTY]
        }
        cvw = Board(pawns_to_code(w))
        for c in w:
            self.assertFalse(cvw.can_move_fwd(CYAN, c))
            self.assertFalse(cvw.can_capture(CYAN, c))

        self.assertTrue(cvw.is_winner(VIOLET))
        self.assertTrue(cvw.is_winner(CYAN))

    def test_is_symmetrical(self):
        b = Board('B55B')
        self.assertTrue(b.is_symmetrical())

    @unittest.skip("old")
    def test_get_legal_moves1(self):
        r = self.board.get_legal_moves(CYAN)
        self.assertEqual(len(r), 5)
        self.assertIn('WW', r)
        self.assertIn('WX', r)
        self.assertIn('YX', r)
        self.assertIn('YY', r)
        self.assertIn('YZ', r)

    @unittest.skip("old")
    def test_get_legal_moves2(self):
        r = self.board.get_legal_moves(VIOLET)
        self.assertEqual(len(r), 4)
        self.assertIn('XW', r)
        self.assertIn('XY', r)
        self.assertIn('ZY', r)
        self.assertIn('ZZ', r)

    @unittest.skip("old")
    def test_flip_move(self):
        r = self.board.flip_move('WW')
        self.assertEqual(r, 'ZZ')
        r = self.board.flip_move('WX')
        self.assertEqual(r, 'ZY')
        r = self.board.flip_move('XY')
        self.assertEqual(r, 'YX')
        r = self.board.flip_move('YY')
        self.assertEqual(r, 'XX')

@unittest.skip("old")
class TestBoard5(TestLexCommon):
    basic_case = {'V': (VIOLET, EMPTY, CYAN),
                  'W': (EMPTY, CYAN, EMPTY),
                  'X': (VIOLET, CYAN, EMPTY),
                  'Y': (EMPTY, CYAN, CYAN),
                  'Z': (VIOLET, EMPTY, EMPTY)
    }

    def test_hash(self):
        b1 = Board(ncols=5)
        b2 = Board("B35C2")
        #self.assertEqual(hash(self.board), int("B35C2", len(DIGITS)))
        self.assertNotEqual(b1, self.board)
        self.assertEqual(b2, self.board)

    def test_can_capture_violet(self):
        self.assertTrue(self.board.can_capture(VIOLET, 'V'))
        self.assertFalse(self.board.can_capture(VIOLET, 'W'))
        self.assertTrue(self.board.can_capture(VIOLET, 'X'))
        self.assertFalse(self.board.can_capture(VIOLET, 'Y'))
        self.assertTrue(self.board.can_capture(VIOLET, 'Z'))

    def test_can_capture_cyan(self):
        self.assertFalse(self.board.can_capture(CYAN, 'V'))
        self.assertTrue(self.board.can_capture(CYAN, 'W'))
        self.assertFalse(self.board.can_capture(CYAN, 'X'))
        self.assertTrue(self.board.can_capture(CYAN, 'Y'))
        self.assertFalse(self.board.can_capture(CYAN, 'Z'))

    def test_is_symmetrical(self):
        b = Board('B525B')
        self.assertTrue(b.is_symmetrical())

    def test_get_legal_moves1(self):
        r = self.board.get_legal_moves(CYAN)
        self.assertEqual(len(r), 7)
        self.assertIn('VV', r)
        self.assertIn('WV', r)
        self.assertIn('WW', r)
        self.assertIn('WX', r)
        self.assertIn('YX', r)
        self.assertIn('YY', r)
        self.assertIn('YZ', r)

    def test_get_legal_moves2(self):
        r = self.board.get_legal_moves(VIOLET)
        self.assertEqual(len(r), 6)
        self.assertIn('VV', r)
        self.assertIn('VW', r)
        self.assertIn('XW', r)
        self.assertIn('XY', r)
        self.assertIn('ZY', r)
        self.assertIn('ZZ', r)

    def test_flip_move(self):
        r = self.board.flip_move('VV')
        self.assertEqual(r, 'ZZ')
        r = self.board.flip_move('WX')
        self.assertEqual(r, 'YX')
        r = self.board.flip_move('XY')
        self.assertEqual(r, 'XW')
        r = self.board.flip_move('XX')
        self.assertEqual(r, 'XX')


if __name__ == '__main__':
    testSuite = unittest.TestSuite()
    testSuite.addTest(unittest.makeSuite(TestBase256))
    testSuite.addTests(unittest.makeSuite(TestLexFunctions))
    testSuite.addTests(unittest.makeSuite(TestBoard3))
    testSuite.addTests(unittest.makeSuite(TestBoard4))
    testSuite.addTests(unittest.makeSuite(TestBoard5))
    unittest.TextTestRunner().run(testSuite)

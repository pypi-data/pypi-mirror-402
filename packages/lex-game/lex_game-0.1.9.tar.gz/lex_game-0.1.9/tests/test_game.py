from lexcel.game import main, MARKS
import unittest
from unittest.mock import patch
from io import StringIO
import re
import sys
import os
import hashlib


@patch('sys.stdout', new_callable=StringIO)
class TestGame(unittest.TestCase):
    save_in = None

    def setUp(self):
        self.save_in = sys.stdin

    def tearDown(self):
        sys.stdin = self.save_in

    def assert_main_exits(self, args):
        with self.assertRaises(SystemExit) as cm:
            main(args)
        self.assertEqual(cm.exception.code, 0)

    def assert_file_and_rm(self, file):
        self.assertTrue(os.path.isfile(file))
        os.remove(file)

    def test_match(self, mock_out):
        for n in (3,
                  # 4,
                  # 5
                  ):
            for p in (1, 2):
                with self.subTest("Winner {} {}".format(p, n)):
                    sys.stdin = open('tests/winner{}-{}.txt'.format(p, n), 'r')
                    self.assert_main_exits(['-n{}'.format(n)])
                    for player in (1, 2):
                        self.assertIn('\nPlayer {} ({}), make your move: \n'.format(player, MARKS[player]),
                                      mock_out.getvalue())
                    self.assertIn('\nPlayer {} won!!!\n'.format(p), mock_out.getvalue())
                    sys.stdin.close()

    def test_match_exp(self, mock_out):
        sys.stdin = open('tests/7777.txt', 'r')
        self.assert_main_exits(['-e2',
                                'tests/exapawn-empty.xlsx',
                                'exapawn-7777.xlsx',
                                '-b', 'B89', '-p', '1', '-t', '3', '-s', '7777'])
        self.assertIn('Player 2 won', mock_out.getvalue())
        self.assert_file_and_rm('exapawn-7777.xlsx')
        sys.stdin.close()

    def test_empty(self, mock_out):
        for n in (3,
                  # 4,
                  # 5
                  ):
            with self.subTest("{} pawns".format(n)):
                self.assert_main_exits(['-n{}'.format(n),
                                        '--empty',
                                        'exapawn-empty.xlsx'])
                self.assert_file_and_rm('exapawn-empty.xlsx')

    def test_match_empty_exp_seed(self, mock_out):

        def get_digest(filename):
            with open(filename, 'rb') as f:
                hash = hashlib.sha1()
                hash.update(f.read())
            return hash.hexdigest()

        self.assert_main_exits(['--empty', 'exapawn-empty.xlsx'])
        before = get_digest('exapawn-empty.xlsx')

        sys.stdin = open('tests/0001.txt', 'r')
        self.assert_main_exits(['-e2', 'exapawn-empty.xlsx', 'exapawn-test-001.xlsx',
                                '-s', '0001', '-d', 'test0001.log'])
        self.assertIn('Player 2 won', mock_out.getvalue())
        sys.stdin.close()

        after = get_digest('exapawn-empty.xlsx')
        self.assertEqual(before, after)

        sys.stdin = open('tests/0002.txt', 'r')
        self.assert_main_exits(['-e2', 'exapawn-test-001.xlsx', 'exapawn-test-002.xlsx',
                                '-s', '0102'])
        self.assertIn('Player 2 won', mock_out.getvalue())
        sys.stdin.close()

        self.assert_file_and_rm('exapawn-test-001.xlsx')
        self.assert_file_and_rm('exapawn-test-002.xlsx')
        # self.assert_file_and_rm('test0001.log')
        self.assert_file_and_rm('exapawn-empty.xlsx')

    def test_match_empty_exp_seed2(self, mock_out):
        self.assert_main_exits(['--empty', 'exapawn-empty.xlsx'])

        sys.stdin = open('tests/0002c.txt', 'r')
        self.assert_main_exits(['-e2', 'exapawn-empty.xlsx', 'exapawn-test-001c.xlsx',
                                '-s', '0002'])
        self.assertIn('YY move for player 1 is not allowed.\n', mock_out.getvalue())
        self.assertIn('Input is invalid.\n', mock_out.getvalue())
        self.assertIn('\nPlayer 1 won!!!\n', mock_out.getvalue())
        sys.stdin.close()

        self.assert_file_and_rm('exapawn-test-001c.xlsx')
        self.assert_file_and_rm('exapawn-empty.xlsx')

    def test_tree(self, mock_out):
        WIN = re.compile(r'\[.*winner.*\]')
        for n, winners in [
                (3, 65),
                # (4, 1635),
                # (5, 66835)
        ]:
            with self.subTest("{} pawns".format(n)):
                self.assert_main_exits(['-n', str(n), '--tree'])
                count = 0
                for line in mock_out.getvalue().split('\n'):
                    if WIN.search(line) is not None:
                        count = count + 1
                self.assertEqual(count, winners)
                mock_out.truncate(0)


if __name__ == '__main__':
    unittest.main()

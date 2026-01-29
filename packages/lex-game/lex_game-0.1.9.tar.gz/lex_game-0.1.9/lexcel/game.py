import argparse
import random
import logging
from lexcel import MARKS, CYAN, VIOLET, other, LExcel, Board, Player


def get_move(board: Board,
             player: Player,
             turn: Player,
             rand: random.Random,
             source: str,
             move_memory: list[tuple[str, str, Player]]):
    b = None
    while b is None:
        if source == 'input':
            logging.debug("From input")  # pragma: no mutate
            m = input(f'Player {player} ({MARKS[player]}), make your move: ')
        else:
            logging.debug("Choose %s %s %s %s %s",
                         source, board.get_code(), turn,
                         move_memory, player)  # pragma: no mutate
            logging.debug("Random %s", rand.getstate())  # pragma: no mutate
            m = LExcel(source).choose_and_remember_move(board,
                                                        turn,
                                                        move_memory,
                                                        rand,
                                                        player)
        m = m.upper()
        logging.debug("Move: %s", m)  # pragma: no mutate
        if m in board.WELL_FORMED_MOVES:
            try:
                b = board.move(player, m[0], m[1])
            except Board.IllegalMoveError:
                print(f'{m} move for player {player} is not allowed.')
                print(board)
        else:
            print('Input is invalid.')

    print(b)
    if b.is_winner(player):
        print(f'Player {player} won!!!')
        return b, player
    return b, None


def learn(a_player: Player,
          the_winner: Player,
          mem: list[tuple[str, str, Player]],
          start: str, to: str | None):
    if to is not None:
        start_lex = LExcel(start)
        if the_winner == a_player:
            # reward each move in memory
            start_lex.reward(to, mem, 1)
        else:
            assert the_winner == other(a_player)  # pragma: no mutate
            # punish last move in memory
            start_lex.reward(to, mem[-1:], -1)


def main(test_args=None):
    desc = """
LEX --- Learning EX-a-pawn
A game written by Mattia Monga for a 'Coding for lawyers' course.
© 2020-25 - Free to distribute, use, and modify
according to the terms of GPLv3."""

    rules = """Pawns move and capture as in chess,
but there are neither two-step moves nor en-passant captures.
Players win by reaching the last row or by blocking the opponent.
Moves are given by two letters: the starting column and the ending one.
"""

    parser = argparse.ArgumentParser(description=desc+'\n\n'+rules,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-e1', '--exp-player1', nargs=2,
                        metavar=('start.xlsx', 'save.xlsx'),
                        default=['input', None],
                        help='Spreadsheet files to get and save game experience used by player 1')
    parser.add_argument('-e2', '--exp-player2', nargs=2,
                        metavar=('start.xlsx', 'save.xlsx'),
                        default=['input', None],
                        help='Spreadsheet files to get and save game experience used by player 2')

    parser.add_argument('-s', '--seed', type=int,
                        help="""Set a seed for random number generations
                        (only useful together with -e1 or -e2)""")

    dim_args = parser.add_mutually_exclusive_group()
    dim_args.add_argument('-b', '--board', type=str,
                          help='Set the initial board by giving its code (default "BBB")')
    dim_args.add_argument('-n', '--num', type=int,
                          default=3, choices=range(3, 4),
                          help='Set the number of pawns each player controls (default 3)')

    parser.add_argument('-p', '--player', type=int,
                        default=CYAN, choices=(CYAN, VIOLET),
                        help='Set the first player (default CYAN)')
    parser.add_argument('-t', '--turn', type=int,
                        default=1, choices=range(1, 11),
                        help='Set the turn (default 1)')

    only_args = parser.add_mutually_exclusive_group()
    only_args.add_argument('--tree', action='store_true',
                           help='Print the game tree in LaTeX')

    only_args.add_argument('--empty', type=str, metavar='empty.xlsx',
                           help='Save a spreadsheet with an empty experience')

    parser.add_argument('-d', '--debug', type=str, metavar='move.log',
                        help='Log moves in file')

    args = parser.parse_args(test_args)
    if args.debug:
        logging.basicConfig(filename=args.debug,
                            level=logging.DEBUG)  # pragma: no mutate
        logging.debug("CLI Args: %s", args)  # pragma: no mutate

    if args.board is not None:
        board = Board(args.board)
        args.num = len(board.get_code())
    else:
        board = Board(ncols=args.num)
    if args.tree:
        print(Board.get_forest(len(board.COLS))[0])
        exit(0)
    if args.empty:
        LExcel.make_empty_experience(len(board.COLS),
                                     args.empty,
                                     [VIOLET, CYAN])
        exit(0)

    turn, winner = args.turn, None
    memory = {CYAN: [], VIOLET: []}
    randomizer = random.Random(args.seed)

    print(desc)
    print(board)
    print(rules+f"\nWell formed moves: {board.WELL_FORMED_MOVES}")
    while winner is None:
        board, winner = get_move(board, args.player, turn, randomizer,
                                 args.exp_player1[0], memory[args.player])
        turn += 1
        if winner is None:
            board, winner = get_move(board, other(args.player),
                                     turn, randomizer,
                                     args.exp_player2[0],
                                     memory[other(args.player)])
            turn += 1

    learn(CYAN, winner, memory[CYAN],
          args.exp_player1[0], args.exp_player1[1])
    learn(VIOLET, winner, memory[VIOLET],
          args.exp_player2[0], args.exp_player2[1])

    exit(0)


if __name__ == '__main__':
    main()

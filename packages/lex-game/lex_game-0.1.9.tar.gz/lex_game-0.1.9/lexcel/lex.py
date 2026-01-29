"""LEX board operations."""

from functools import cache

type Player = int
type ColName = str
type PawnColumn = dict[ColName, list[Player]]
type Code = str

EMPTY: Player = 0
CYAN: Player = 1
VIOLET: Player = 2

MARKS = {
    EMPTY: ' ',
    CYAN: '\N{WHITE CHESS PAWN}',
    VIOLET: '\N{BLACK CHESS PAWN}'
}


@cache
class Base256:
    """A singleton to implement Base256.
       See https://github.com/fleschutz/Base256U
    """
    SYMBOLS: str
    BASE = 256

    def __init__(self):
        self.SYMBOLS = ''.join([str(i) for i in range(10)])
        self.SYMBOLS += ''.join([chr(ord('A') + i) for i in range(26)])
        self.SYMBOLS += ''.join([chr(ord('a') + i) for i in range(26)])
        start = ord('\N{LATIN CAPITAL LETTER A WITH GRAVE}')
        # Skip non letters
        self.SYMBOLS += ''.join([chr(i)  # 194 symbols in total
                                 for i in range(
                                         start,
                                         start+196)
                                 if chr(i) != '\N{MULTIPLICATION SIGN}'
                                 and chr(i) != '\N{DIVISION SIGN}'])
        assert len(self.SYMBOLS) == self.BASE

    def to_int(self, code: str) -> int:
        assert all([i in self.SYMBOLS for i in code])
        n = 0
        for i, c in enumerate(code[::-1]):
            n += self.BASE**i * self.SYMBOLS.index(c)
        return n

    def from_int(self, n: int) -> str:
        assert n >= 0
        if n == 0:
            return self.SYMBOLS[0]
        s = ''
        x = n
        while x > 0:
            s += self.SYMBOLS[x % self.BASE]
            x = x // self.BASE
        return s


def other(player: Player) -> Player:
    """Return opposite color. """
    if player == VIOLET:
        return CYAN
    if player == CYAN:
        return VIOLET
    return EMPTY


def pawns_to_code(pawns: PawnColumn) -> str:
    """Return an alphanumeric repr. of a board for ease board matching.

    The code is a string of alphanumeric digits representing columns,
    therefore a flipped board has exactly the reverse code.

    """
    r = ''
    base = len(MARKS)
    b256 = Base256()
    for c in sorted(pawns.keys()):
        n = 0
        for i, p in enumerate(pawns[c]):
            n += p * base**i
        r += b256.from_int(n)
    return r


class Board:
    """Boards in a program must have the same number of columns and rows.
    """

    NROWS: int
    COLS: list[ColName] = []
    WELL_FORMED_MOVES: list[str]

    @classmethod
    def _init_board_params(cls, ncols: int = 3):
        """Init globals used for Board instantiation."""
        col_names = ('V', 'W', 'X', 'Y', 'Z')
        assert 0 < ncols <= len(col_names)
        cls.NROWS = ncols
        cls.COLS = list(col_names[-ncols:])
        cls.WELL_FORMED_MOVES = []
        for i in cls.COLS:
            for j in cls.COLS:
                if abs(ord(i) - ord(j)) <= 1:
                    cls.WELL_FORMED_MOVES.append(i+j)

    def _pawns_from_code(self, h: str) -> PawnColumn:
        """Return a dict corresponding to code digits.
        """
        assert len(self.COLS) == len(h), \
            f"{self.COLS} {h}"  # pragma: no mutate
        r = {}
        base = len(MARKS)
        b256 = Base256()
        for i, c in enumerate(self.COLS):
            col = []
            n = b256.to_int(h[i])
            for _ in range(self.NROWS):
                col.append(n % base)
                n = n // base
            r[c] = col

        return r

    def __init__(self,
                 code: str | None = None,
                 ncols: int = 3):
        assert ncols > 0
        base = len(MARKS)
        b256 = Base256()
        if code is None:
            start = b256.from_int(VIOLET + CYAN*base**(ncols-1))
            code = start*ncols
        else:
            ncols = len(code)

        assert ncols == len(code), f'{ncols} {code}'  # pragma: no mutate
        if self.COLS == [] or len(self.COLS) != len(code):
            self._init_board_params(len(code))

        self.pawns = self._pawns_from_code(code)

    def __str__(self) -> str:
        """Return a string representation for the board.

        It uses Unicode code points
        for \N{WHITE CHESS PAWN} and \N{BLACK CHESS PAWN}.
        """

        def add_hline(line: str) -> str:
            line = line + ' '
            for _ in self.COLS:
                line = line + '+---'
            line = line + '+\n'
            return line

        s = '\n '
        for c in self.COLS:
            s += '  ' + c + ' '
        s = add_hline(s + ' \n')

        for r in range(self.NROWS):
            for c in self.COLS:
                s += f' | {MARKS[self[c][r]]}'
            s += ' |\n'
            s = add_hline(s)
        s += f'Board code: {self.get_code()}\n'
        return s

    def __eq__(self, other_object) -> bool:
        if not isinstance(other_object, Board):
            return NotImplemented
        return hash(self) == hash(other_object)

    def __hash__(self) -> int:
        b256 = Base256()
        code = self.get_code()
        return b256.to_int(code)

    def get_code(self) -> Code:
        """Return the code which identifies this board."""
        return pawns_to_code(self.pawns)

    def __getitem__(self, col: ColName) -> list[Player]:
        return self.pawns[col]

    def __setitem__(self, col: ColName, value: list[Player]):
        raise TypeError("'Board' objects are immutable!")

    def flip(self) -> 'Board':
        """Return a board with the columns flipped.
        """
        return Board(self.get_code()[::-1])

    def flip_move(self, move: str):
        """Return a flipped move,
           i.e. the move according to the board with flipped columns.
        """
        r = ''
        for c in move:
            for i, k in enumerate(self.COLS):
                if c == k:
                    r = r + self.COLS[-(i+1)]
        return r

    def exchange(self) -> 'Board':
        """Return a board with players exchanged
           as if VIOLET played as CYAN and viceversa.
        """
        b = {}
        for c in self.COLS:
            b[c] = [EMPTY] * len(self.COLS)
            for i, p in enumerate(self[c][::-1]):
                b[c][i] = other(p)
            b[c] = b[c]
        return Board(pawns_to_code(b))

    def can_move_fwd(self, player: Player, column: ColName) -> bool:
        """True if player can move forward in column.
        """
        if player == VIOLET:
            for row in range(self.NROWS-1):
                if self[column][row] == VIOLET and self[column][row+1] == EMPTY:
                    return True
            return False
        return self.exchange().can_move_fwd(VIOLET, column)

    def can_capture(self, player: Player, column: ColName) -> bool:
        """True if player can move diagonally from column and capture a pawn.
        """
        if player == VIOLET:
            if column == self.COLS[0]:
                for row in range(Board.NROWS-1):
                    if self[self.COLS[0]][row] == VIOLET \
                       and self[self.COLS[1]][row + 1] == CYAN:
                        return True
            elif column == self.COLS[-1]:
                return self.flip().can_capture(VIOLET, self.COLS[0])
            else:
                c = self.COLS.index(column)
                for row in range(self.NROWS-1):
                    if self[column][row] == VIOLET \
                       and CYAN in (self[self.COLS[c-1]][row + 1],
                                    self[self.COLS[c+1]][row + 1]):
                        return True
            return False
        return self.exchange().can_capture(VIOLET, column)

    def is_winner(self, player: Player) -> bool:
        """True if player is winning. """
        if player == VIOLET:
            opponent_moves = 0
            for c in self.COLS:
                if self[c][-1] == VIOLET:
                    return True
                if self.can_move_fwd(CYAN, c) or self.can_capture(CYAN, c):
                    opponent_moves += 1
            return opponent_moves == 0
        return self.exchange().is_winner(VIOLET)

    class IllegalMoveError(Exception):
        """An illegal move was tried."""

    def move(self, player: Player,
             start: ColName,
             end: ColName):
        """Return a board in which player has moved from column start to end.

        Raise an exception if the move is not legal.
        """
        assert start+end in self.WELL_FORMED_MOVES  # pragma: no mutate

        b = {}
        for c in self.COLS:
            b[c] = self[c]

        if player == VIOLET:
            if start == end and not self.can_move_fwd(VIOLET, start):
                raise Board.IllegalMoveError(
                    f"{VIOLET} cannot move forward on column {start}")
            if start == end:
                if not self.can_move_fwd(VIOLET, start):
                    raise Board.IllegalMoveError('Invalid forward move.')
                col = list(self[start])
                i = len(col) - 1 - col[::-1].index(VIOLET)
                col[i] = EMPTY
                col[i + 1] = VIOLET
                b[start] = col
                return Board(pawns_to_code(b))

            if not self.can_capture(VIOLET, start):
                raise Board.IllegalMoveError('Invalid capture move.')

            def capture(bdict: PawnColumn,
                        from_row: int, to_row: int) -> Board | None:
                if self[start][from_row] == VIOLET \
                   and self[end][to_row] == CYAN:
                    bdict[start] = list(self[start])
                    bdict[end] = list(self[end])
                    bdict[start][from_row] = EMPTY
                    bdict[end][to_row] = VIOLET
                    bdict[start] = bdict[start]
                    bdict[end] = bdict[end]
                    return Board(pawns_to_code(bdict))
                return None

            for row in range(self.NROWS-1):
                r = capture(b, row, row + 1)
                if r is not None:
                    return r

            raise Board.IllegalMoveError("No move is possible!")

        return self.exchange().move(VIOLET, start, end).exchange()

    def is_symmetrical(self) -> bool:
        """True if board is symmetric."""
        return self == self.flip()

    def get_legal_moves(self, player: Player) -> list[str]:
        """Return a list of all legal moves for player in a given position."""
        r = []
        for m in self.WELL_FORMED_MOVES:
            try:
                self.move(player, m[0], m[1])
                r.append(m)
            except Board.IllegalMoveError:
                pass
        return r

    def prune_sym_moves(self, moves: list[str]) -> list[str]:
        """Return a list of moves filtered for symmetrical ones."""
        if len(moves) <= 1:
            return moves
        if self.flip_move(moves[0]) in moves[1:]:
            return self.prune_sym_moves(moves[1:])
        return self.prune_sym_moves(moves[1:]) + [moves[0]]

    @classmethod
    def get_forest(cls, ncols: int) -> tuple[str,
                                             dict[str,
                                                  tuple[Player, set[str]]]]:
        """Return a LaTeX string with the game tree
           and the set of unique boards.

        Boards are returned as a dictionary indexed by codes
        with the set of player moves legal from there.
        """

        boards: dict[str, tuple[int, set[str]]] = {}

        def get_tree(board: 'Board', player: Player,
                     turn: Player,
                     a_move: str | None,
                     indent: str) -> tuple[str, Player]:
            code = board.get_code()
            if board.is_winner(other(player)) and a_move is not None:
                s = f"{indent}[{code},winner{other(player)},"
                s += f"move={{{other(player)}}}{{{a_move.lower()}}}]"
                return s, other(player)
            moves = board.get_legal_moves(player)
            if board.is_symmetrical():
                moves = board.prune_sym_moves(moves)
            if code in boards:
                for m in moves:
                    boards[code][1].add(m)
            elif code[::-1] in boards:
                for m in moves:
                    boards[code[::-1]][1].add(board.flip_move(m))
            else:
                boards[code] = (turn, set(moves))
            s = f"{indent}[{code},winner@"
            if a_move is not None:
                s += f",move={{{other(player)}}}{{{a_move.lower()}}},winner@"
            s += "\n"
            winners = []
            for m in moves:
                b = board.move(player, m[0], m[1])
                t, w = get_tree(b, other(player), turn+1, m, indent + " ")
                s += t + "\n"
                winners.append(w)
            if len(set(winners)) == 1:
                winner = winners[0]
            else:
                winner = player
            s = s.replace('@', str(winner))
            return s + indent + "]", winner

        f = """
%% Game tree for LEX --- Learning EX-a-pawn
%% Uncomment the lines which begin with % for a standalone LaTeX document
%\\documentclass[tikz]{standalone}
%\\usepackage{forest}
%\\begin{document}

\\forestset{
  default preamble={
    for tree={font=\\tiny}
  }
}
\\begin{forest}
  winner1/.style={draw,fill=cyan,inner sep=1pt,outer sep=0},
  winner2/.style={draw,fill=violet!60,inner sep=1pt,outer sep=0},
  move/.style n args=2{%
    if={#1<2}%
    {edge label/.expanded={%
      node [midway,fill=white,text=cyan,font=\\unexpanded{\\tiny}] {$#2$}%
    }}{edge label/.expanded={%
      node [midway,fill=white,text=violet!60,font=\\unexpanded{\\tiny}] {$#2$}%
    }},
  }
"""
        t, _ = get_tree(Board(ncols=ncols), CYAN, 1, None, " ")
        f = f + t
        f = f + "\n\\end{forest}"
        f = f + "\n%\\end{document}"

        for h in boards:
            b = Board(h)
            if b.is_symmetrical():
                moves = b.prune_sym_moves(list(boards[h][1]))
                boards[h] = (boards[h][0], set(moves))

        return f, boards

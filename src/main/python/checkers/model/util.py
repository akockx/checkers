# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains utility classes that are needed to implement a checkers game. """
from dataclasses import dataclass
from enum import auto, Enum, unique
from typing import Final, Iterator, override, Self


@unique
class CheckersPlayer(Enum):
    """ Store players of a checkers game in the order in which they take turns. """

    # The values of the members of this enumeration are used in the next() method.
    LIGHT: Final[int] = 0  # The player with the light pieces.
    DARK: Final[int] = 1  # The player with the dark pieces.

    def next(self):
        """ Return the player that takes a turn after this player. """

        # Determine the item in the CheckersPlayer enumeration that comes after this item.
        # After the last item in the CheckersPlayer enumeration, loop back to the first item.
        return CheckersPlayer((self.value + 1) % len(CheckersPlayer))

    @override
    def __str__(self) -> str:
        return self.name


@unique
class CheckersPieceType(Enum):
    """ Store checkers piece types. """

    MAN = auto()  # Normal checkers piece.
    KING = auto()  # Crowned checkers piece.

    @override
    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class CheckersPiece:
    """ Store immutable properties of a checkers piece. """

    owner: CheckersPlayer
    type: CheckersPieceType

    @override
    def __repr__(self) -> str:
        return f"Piece({self.owner!s}, {self.type!s})"


def sign(value: int) -> int:
    if value > 0:
        return 1
    elif value < 0:
        return -1
    else:  # If value is 0 or -0.
        return 0


@dataclass(frozen=True, slots=True)
class Index2D:
    """ Store an immutable 2D index that can be used to access an element of a 2D array.

    This class implements the following custom operations to make 2D indices behave like integer vectors:
        - element-wise addition
        - element-wise subtraction
        - element-wise multiplication by an integer
    """

    x: int  # Column index.
    y: int  # Row index.

    @classmethod
    def sign(cls, index_2d: Self) -> Self:
        """ Element-wise sign function. """

        return Index2D(sign(index_2d.x), sign(index_2d.y))

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index2D):
            return False

        return self.x == other.x and self.y == other.y

    def __add__(self, other: object) -> Self:
        if isinstance(other, Index2D):
            return Index2D(self.x + other.x, self.y + other.y)

        return NotImplemented

    def __iadd__(self, other: object) -> Self:
        return self.__add__(other)

    def __sub__(self, other: object) -> Self:
        if isinstance(other, Index2D):
            return Index2D(self.x - other.x, self.y - other.y)

        return NotImplemented

    def __isub__(self, other: object) -> Self:
        return self.__sub__(other)

    def __mul__(self, scalar: object) -> Self:
        if isinstance(scalar, int):
            return Index2D(self.x * scalar, self.y * scalar)

        return NotImplemented

    def __imul__(self, scalar: object) -> Self:
        return self.__mul__(scalar)

    def __rmul__(self, scalar: object) -> Self:
        return self.__mul__(scalar)

    @override
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


class CheckersBoard:
    """ Store a checkers board and the pieces on the board. """

    __slots__ = ('row_count', 'column_count', '_list_2d')

    def __init__(self, row_count: int, column_count: int):
        """ Create an empty checkers board that has the passed shape. """

        if row_count <= 0:
            raise ValueError(f"Number of rows must be positive, not '{row_count}'.")
        if column_count <= 0:
            raise ValueError(f"Number of columns must be positive, not '{column_count}'.")

        self.row_count: Final[int] = row_count  # Number of rows in board.
        self.column_count: Final[int] = column_count  # Number of columns in board.
        self._list_2d: Final[list[list[CheckersPiece | None]]] = [[None for _ in range(row_count)] for _ in range(column_count)]  # Store checkers pieces.

    def __iter__(self) -> Iterator[tuple[Index2D, CheckersPiece]]:
        """ Yield a tuple containing a checkers piece and its 2d index, for each piece on this board. """

        for x, column in enumerate(self._list_2d):
            for y, piece in enumerate(column):
                if piece:
                    yield Index2D(x, y), piece

    def __getitem__(self, index: Index2D) -> CheckersPiece | None:
        return self._list_2d[index.x][index.y]

    def __setitem__(self, index: Index2D, piece: CheckersPiece | None):
        self._list_2d[index.x][index.y] = piece

    def __contains__(self, index: Index2D) -> bool:
        """ Return True if the passed 2D index is within the bounds of this checkers board. Otherwise, return False.

        Note: this __contains__() method has been repurposed to make it easier and more Pythonic to check whether a 2D index is inside a checkers board.
        This is different from the normal usage of the __contains__() method, which is to check whether a container contains a given item.
        """

        return 0 <= index.x < self.column_count and 0 <= index.y < self.row_count


@dataclass(frozen=True, slots=True)
class CheckersJump:
    """ Store an immutable jump that is part of a move in a checkers game. """

    destination: Index2D
    captured_square: Index2D  # The square that contains the piece that is being captured in this jump.


@dataclass(frozen=True, slots=True)
class CheckersMove:
    """ Store an immutable move from a checkers game. """

    visited_squares: tuple[Index2D, ...]  # The squares that the moving piece visits during this move, in consecutive order.

    @property
    def origin(self) -> Index2D:
        """ Return the first visited square of this move. """

        return self.visited_squares[0]

    @property
    def destination(self) -> Index2D:
        """ Return the last visited square of this move. """

        return self.visited_squares[-1]

    def __len__(self) -> int:
        """ Return the number of visited squares of this move. """

        return len(self.visited_squares)

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" + ", ".join(str(square) for square in self.visited_squares) + ")"


@dataclass(frozen=True, slots=True)
class CheckersGameResult:
    """ Store immutable result of a checkers game. """

    winner: CheckersPlayer | None  # Winner of the game. None means that the game ended in a draw.
    total_ply_count: int  # Ply count when the game ended.

    def __post_init__(self):
        """ Validate attributes. """

        if self.total_ply_count <= 0:
            raise ValueError(f"Total ply count must be positive, not '{self.total_ply_count}'.")

    @override
    def __repr__(self) -> str:
        return f"Result(winner={self.winner!s}, total_ply_count={self.total_ply_count})"

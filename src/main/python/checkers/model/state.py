# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code that stores and changes the state of a checkers game. """
from copy import deepcopy
from typing import Final

from checkers.model.rules import apply, determine_legal_moves, determine_result
from checkers.model.util import CheckersBoard, CheckersGameResult, CheckersMove, CheckersPiece, CheckersPieceType, CheckersPlayer, Index2D


class CheckersState:
    """ Store a state of a checkers game and expose methods to change it.

    The exposed methods make sure that the stored state is only changed in ways that abide by the rules of an international checkers game.
    The rules of international checkers are described on https://en.wikipedia.org/wiki/International_draughts
    """

    __slots__ = ('_board', '_current_player', '_ply_count', '_cached_legal_moves')

    def __init__(self, row_count: int, column_count: int):
        """ Create a checkers state with an empty checkers board that has the passed shape. """

        # If row count or column count is less than 3, then it is not possible to capture pieces.
        if row_count < 3:
            raise ValueError(f"Number of rows must be 3 or more, not '{row_count}'.")
        if column_count < 3:
            raise ValueError(f"Number of columns must be 3 or more, not '{column_count}'.")
        # If row count is even and column count is odd, then for the starting position of a checkers game
        # the distribution of pieces across the board or the number of pieces is different for different players.
        if row_count % 2 == 0 and column_count % 2 == 1:
            raise ValueError("If number of rows is even, then number of columns must be even as well.")

        self._board: Final[CheckersBoard] = CheckersBoard(row_count, column_count)  # Store checkers pieces.

        self._current_player: CheckersPlayer = CheckersPlayer.LIGHT  # The player whose turn it is.
        self._ply_count: int = 0  # Number of plies (moves) that have been made since the start of the game.

        self._cached_legal_moves: tuple[CheckersMove, ...] | None = None  # Cache legal moves for this state.

    @property
    def board(self) -> CheckersBoard:
        return deepcopy(self._board)

    @property
    def current_player(self) -> CheckersPlayer:
        return self._current_player

    @property
    def ply_count(self) -> int:
        return self._ply_count

    def clear(self):
        """ Reset this state to an empty checkers board. """

        # Remove all pieces from the board.
        for square, _ in self._board:
            self._board[square] = None

        # Reset other attributes.
        self._current_player = CheckersPlayer.LIGHT
        self._ply_count = 0

        # Clear cache.
        self._cached_legal_moves = None

    def start_new_game(self):
        """ Reset this state to the starting position of a checkers game. """

        self.clear()

        # Add light pieces.
        occupied_row_count: Final[int] = (self._board.row_count - 1) // 2
        for x in range(self._board.column_count):
            for y in range(occupied_row_count):
                if (x + y) % 2 == 0:
                    self._board[Index2D(x, y)] = CheckersPiece(CheckersPlayer.LIGHT, CheckersPieceType.MAN)

        # Add dark pieces.
        for x in range(self._board.column_count):
            for y in range(self._board.row_count - occupied_row_count, self._board.row_count):
                if (x + y) % 2 == 0:
                    self._board[Index2D(x, y)] = CheckersPiece(CheckersPlayer.DARK, CheckersPieceType.MAN)

        # The player with the light pieces moves first.
        self._current_player = CheckersPlayer.LIGHT
        self._ply_count = 0

    @property
    def legal_moves(self) -> tuple[CheckersMove, ...]:
        """ Return a tuple with all legal moves for this state. Return an empty tuple if there are no legal moves. """

        if self._cached_legal_moves is None:
            # Cache legal moves.
            self._cached_legal_moves = tuple(determine_legal_moves(self._current_player, self._board))

        return self._cached_legal_moves

    def apply(self, move: CheckersMove):
        """ Apply the passed move to this state. If the passed move is not legal for this state, raise an exception. """

        if move not in self.legal_moves:
            raise ValueError(f"Move '{move}' is not legal for state '{self}'.")

        # Update board.
        apply(move, self._board)

        # Advance turn to the next player.
        self._current_player = self._current_player.next()
        self._ply_count += 1

        # Clear cache, since the cached legal moves are no longer valid after making a move.
        self._cached_legal_moves = None

    @property
    def result(self) -> CheckersGameResult | None:
        """ Return the result of a checkers game that has reached this state. Return None if the game is still in progress. """

        return determine_result(self._board, self._current_player, self._ply_count, len(self.legal_moves))

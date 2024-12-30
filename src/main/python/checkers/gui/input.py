# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code that handles user input for a checkers game. """
from typing import Final, override

from checkers.model.move_selectors import CheckersMoveSelector
from checkers.model.state import CheckersState
from checkers.model.util import CheckersMove, Index2D


class UserCheckersMoveSelector(CheckersMoveSelector):
    """ Bridge the gap between a checkers game, which needs a complete move as input, and the user, who selects one square at a time.

    A single checkers move may consist of multiple consecutive jumps.
    This class makes it possible for the user to select a complete checkers move step-by-step, by selecting squares one by one.

    At any given time this class stores the squares on the checkers board that can be selected as the next step in selecting a complete move.
    After the user selects one of these squares, it is stored and the squares that can be selected are updated to the next step.
    When the squares that have been selected together form a complete move, this move is stored and can be retrieved by calling selected_move().
    """

    __slots__ = ('_selectable_moves', '_selectable_squares', '_selected_squares', '_selected_move')

    def __init__(self):
        """ Create an empty user checkers move selector. """

        # Input for the selection procedure.
        self._selectable_moves: tuple[CheckersMove, ...] = tuple()  # Complete moves that can be selected.

        # Temporary variables to keep track of the selection procedure.
        self._selectable_squares: Final[set[Index2D]] = set()  # Squares that can be selected as the next step in the selection procedure.
        self._selected_squares: Final[list[Index2D]] = []  # Squares that have been selected so far, in the order of selection, which together form a partial move.

        # Result of the selection procedure.
        self._selected_move: CheckersMove | None = None

    @property
    def selectable_squares(self) -> frozenset[Index2D]:
        return frozenset(self._selectable_squares)

    @property
    def selected_squares(self) -> tuple[Index2D, ...]:
        return tuple(self._selected_squares)

    @override
    def reset(self):
        self._selectable_moves = tuple()
        self._selectable_squares.clear()
        self._selected_squares.clear()
        self._selected_move = None

    @override
    def start(self, state: CheckersState):
        self.reset()

        self._selectable_moves = state.legal_moves
        self._update_selectable_squares()

    def select(self, square: Index2D):
        """ Select the passed square if it is selectable and update the selection procedure. """

        # If nothing to select, do nothing.
        if not self._selectable_squares:
            return

        if square in self._selectable_squares:
            # Continue the selection procedure.
            self._selected_squares.append(square)
        else:
            # Restart the selection procedure.
            self._selected_squares.clear()
            self._selected_move = None

        self._update_selectable_squares()

    def _update_selectable_squares(self):
        """ Determine which squares can be selected, using the selectable moves and the squares that have been selected already. """

        # If selection procedure has been completed, do nothing.
        if self._selected_move:
            return

        self._selectable_squares.clear()
        if not self._selectable_moves:
            return

        # Find all moves that start with the partial move that has been selected so far.
        matching_moves: Final[list[CheckersMove]] = []
        selected_partial_move_length: Final[int] = len(self._selected_squares)
        for move in self._selectable_moves:
            if len(move) < selected_partial_move_length:
                continue

            # Compare start of move with selected squares.
            for n in range(selected_partial_move_length):
                if move.visited_squares[n] != self._selected_squares[n]:
                    break
            else:  # If start of move matches the partial move that has been selected so far.
                matching_moves.append(move)
        assert len(matching_moves) >= 1

        # Check if a complete move has been selected.
        for matching_move in matching_moves:
            if len(matching_move) == selected_partial_move_length:
                assert len(matching_moves) == 1

                # End selection procedure.
                self._selected_move = matching_move
                self._selected_squares.clear()
                return

        # For each matching move, mark the next square as selectable.
        for matching_move in matching_moves:
            self._selectable_squares.add(matching_move.visited_squares[selected_partial_move_length])

    @override
    def selected_move(self) -> CheckersMove | None:
        return self._selected_move

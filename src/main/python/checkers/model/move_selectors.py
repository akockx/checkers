# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code for checkers move selectors. """
import random
from abc import ABC, abstractmethod
from typing import override

from checkers.model.state import CheckersState
from checkers.model.util import CheckersMove


class CheckersMoveSelector(ABC):
    """ Extend this abstract base class to create a specific checkers move selector. """

    __slots__ = ()

    @abstractmethod
    def start(self, state: CheckersState):
        """ Start the selection procedure to select a move that is legal for the passed state. """

        pass

    @abstractmethod
    def selected_move(self) -> CheckersMove | None:
        """ Return the move that was selected during the selection procedure. Return None if the selection procedure has not finished yet. """

        pass

    @abstractmethod
    def reset(self):
        """ Cancel the current selection procedure and clear this move selector so that it can be used again for a new selection procedure. """

        pass


class RandomCheckersMoveSelector(CheckersMoveSelector):
    """ Select a random legal move for a given state of a checkers game. """

    __slots__ = ("_selected_move",)

    def __init__(self):
        """ Create an empty random checkers move selector. """

        self._selected_move: CheckersMove | None = None

    @override
    def reset(self):
        self._selected_move = None

    @override
    def start(self, state: CheckersState):
        self.reset()

        self._selected_move = random.choice(state.legal_moves) if state.legal_moves else None

    @override
    def selected_move(self) -> CheckersMove | None:
        return self._selected_move

# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains a mapping between user choices and implementations of checkers move selectors. """
from asyncio import Event
from concurrent.futures import Future, ThreadPoolExecutor
from enum import auto, Enum, unique
from typing import Final, override

from checkers.ai.solver import pure_monte_carlo_game_search
from checkers.gui.input import UserCheckersMoveSelector
from checkers.model.move_selectors import CheckersMoveSelector, RandomCheckersMoveSelector
from checkers.model.state import CheckersState
from checkers.model.util import CheckersMove


class AICheckersMoveSelector(CheckersMoveSelector):
    """ Select the best legal move for a given state of a checkers game. """

    __slots__ = ('_future_selected_move', '_executor', '_cancelled_event', '_playout_count_per_move')

    def __init__(self, playout_count_per_move: int):
        """ Create an empty AI checkers move selector with the passed number of playouts per move. """

        self._future_selected_move: Future[CheckersMove | None] | None = None  # Future that holds the selected move after the selection procedure has finished.

        # Create a worker thread that is used to run the selection procedure.
        self._executor: Final[ThreadPoolExecutor] = ThreadPoolExecutor(max_workers=1)
        self._cancelled_event: Final[Event] = Event()  # Event to signal to a running thread that the selection procedure has been cancelled.

        if playout_count_per_move <= 0:
            raise ValueError(f"Number of playouts per move must be positive, not '{playout_count_per_move}'.")

        self._playout_count_per_move: Final[int] = playout_count_per_move

    def __del__(self):
        self.reset()
        self._executor.shutdown()

    @override
    def reset(self):
        if self._future_selected_move:
            # Signal the selection procedure to stop running.
            self._cancelled_event.set()
            # Wait until the selection procedure has stopped running.
            self._future_selected_move.result()

        self._future_selected_move = None
        self._cancelled_event.clear()

    @override
    def start(self, state: CheckersState):
        self.reset()

        # Run the selection procedure in a separate thread so that it does not block the main thread.
        self._future_selected_move = self._executor.submit(pure_monte_carlo_game_search, state, self._playout_count_per_move, self._cancelled_event)

    @override
    def selected_move(self) -> CheckersMove | None:
        if self._future_selected_move is None or not self._future_selected_move.done():
            return None

        return self._future_selected_move.result()


@unique
class CheckersMoveSelectorType(Enum):
    """ Store checkers move selector types. """

    USER = auto()
    RANDOM = auto()
    AI_EXTREMELY_EASY = auto()
    AI_VERY_EASY = auto()
    AI_EASY = auto()
    AI_MEDIUM = auto()
    AI_HARD = auto()
    AI_VERY_HARD = auto()
    AI_EXTREMELY_HARD = auto()


def create_checkers_move_selector(move_selector_type: CheckersMoveSelectorType) -> CheckersMoveSelector:
    """ Create and return a checkers move selector instance that implements the passed checkers move selector type. """

    match move_selector_type:
        case CheckersMoveSelectorType.USER:
            return UserCheckersMoveSelector()
        case CheckersMoveSelectorType.RANDOM:
            return RandomCheckersMoveSelector()
        case CheckersMoveSelectorType.AI_EXTREMELY_EASY:
            return AICheckersMoveSelector(1)
        case CheckersMoveSelectorType.AI_VERY_EASY:
            return AICheckersMoveSelector(5)
        case CheckersMoveSelectorType.AI_EASY:
            return AICheckersMoveSelector(15)
        case CheckersMoveSelectorType.AI_MEDIUM:
            return AICheckersMoveSelector(45)
        case CheckersMoveSelectorType.AI_HARD:
            return AICheckersMoveSelector(135)
        case CheckersMoveSelectorType.AI_VERY_HARD:
            return AICheckersMoveSelector(405)
        case CheckersMoveSelectorType.AI_EXTREMELY_HARD:
            return AICheckersMoveSelector(1215)
        case _:
            raise ValueError(f"Invalid {CheckersMoveSelectorType.__name__} '{move_selector_type}'.")

# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code that selects a move in a checkers game using the Pure Monte Carlo game search algorithm.

The Pure Monte Carlo game search algorithm is described on https://en.wikipedia.org/wiki/Monte_Carlo_tree_search#Pure_Monte_Carlo_game_search
"""
import random
from asyncio import Event
from copy import deepcopy
from math import isclose
from statistics import mean, stdev
from typing import Final

from checkers.ai.util import print_time
from checkers.model.state import CheckersState
from checkers.model.util import CheckersGameResult, CheckersMove, CheckersPlayer

MAX_RECURSION_DEPTH: Final[int] = 200


@print_time("processing time")
def pure_monte_carlo_game_search(state: CheckersState, playout_count_per_move: int, cancelled_event: Event) -> CheckersMove | None:
    """ Use Pure Monte Carlo game search with the passed number of playouts per move to find and return the best move for the passed state.
    Return None if there are no legal moves for the passed state.

    The passed cancelled_event indicates whether the search has been cancelled from outside this function by another thread.
    If cancelled_event becomes set, this function will stop as soon as possible and return None.

    The Pure Monte Carlo game search algorithm is described on https://en.wikipedia.org/wiki/Monte_Carlo_tree_search#Pure_Monte_Carlo_game_search
    """

    legal_moves: Final[tuple[CheckersMove, ...]] = state.legal_moves
    if not legal_moves:
        return None

    # If there is only one legal move, return that one.
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Determine score and uncertainty for each legal move.
    scores: Final[dict[CheckersMove: tuple[float, float]]] = {}
    for move in legal_moves:
        scores[move] = determine_score_for_move(move, state, playout_count_per_move, cancelled_event)

        if cancelled_event.is_set():
            return None

    # Print debug output.
    if __debug__:
        sorted_scores: Final[list[tuple[float, float]]] = sorted(scores.values(), key=lambda pair: pair[0], reverse=True)
        print("scores: " + ", ".join(f"({score:.1f} +/- {uncertainty:.1f})" for score, uncertainty in sorted_scores))

    # Keep only the moves with the best score and choose one of those randomly.
    best_score: Final[float] = max(score for score, _ in scores.values())
    best_moves: Final[list[CheckersMove]] = [move for move, (score, _) in scores.items() if isclose(score, best_score, rel_tol=1e-5, abs_tol=1e-5)]
    return random.choice(best_moves)


def determine_score_for_move(move: CheckersMove, root_state: CheckersState, playout_count: int, cancelled_event: Event) -> tuple[float, float] | None:
    """ Return a score and uncertainty for the passed move by running the passed number of playouts.
    Each playout starts with the passed root_state and the passed move.

    This function assumes that the passed move is legal for the passed root_state.

    The passed cancelled_event indicates whether the playouts have been cancelled from outside this function by another thread.
    If cancelled_event becomes set, this function will stop as soon as possible and return None.
    """

    if playout_count <= 0:
        raise ValueError(f"Number of playouts must be positive, not '{playout_count}'.")

    # Run playouts.
    max_ply_count: Final[int] = root_state.ply_count + MAX_RECURSION_DEPTH
    playout_start_state: Final[CheckersState] = deepcopy(root_state)
    playout_start_state.apply(move)
    playout_results: Final[list[CheckersGameResult | None]] = []
    for _ in range(playout_count):
        playout_results.append(run_playout(playout_start_state, max_ply_count, cancelled_event))

        if cancelled_event.is_set():
            return None

    # Determine score for each playout.
    scores: Final[list[float]] = [determine_score(result, root_state.current_player) for result in playout_results]

    # Return mean and standard deviation of scores.
    assert len(scores) >= 1
    return mean(scores), stdev(scores) if len(scores) >= 2 else 0


def run_playout(state: CheckersState, max_ply_count: int, cancelled_event: Event) -> CheckersGameResult | None:
    """ Apply randomly chosen legal moves to a copy of the passed state until it reaches an end state of the game
    and return the result of that end state.
    Return None (no result) if the passed max_ply_count is reached before an end state occurs.

    The passed cancelled_event indicates whether the playout has been cancelled from outside this function by another thread.
    If cancelled_event becomes set, this function will stop as soon as possible and return None.
    """

    state = deepcopy(state)
    while True:
        # If playout has been cancelled, return None.
        if cancelled_event.is_set():
            return None

        # If an end state has been reached, return result.
        if result := state.result:
            return result

        # If max_ply_count has been reached, return None (no result).
        if state.ply_count >= max_ply_count:
            return None

        # Make a random move and repeat.
        state.apply(random.choice(state.legal_moves))


def determine_score(result: CheckersGameResult | None, player: CheckersPlayer) -> float:
    """ Return the score for the passed checkers game result as seen from the passed player's perspective. """

    if result is None:  # Maximum recursion depth was reached and the game was not finished yet.
        return 0.5

    game_duration_score: Final[float] = min(0.001 * result.total_ply_count, 0.2)
    if result.winner is None:  # Game ended in a draw.
        # The algorithm should postpone a draw as long as possible, because an opportunity to win the game might still come along.
        # Therefore add game duration score.
        # The longer the game takes, the higher the score for a draw, but it is never as high as the score for a win.
        return 0.5 + game_duration_score

    elif result.winner is player:  # Game ended in a win.
        # The algorithm should win as soon as possible.
        # Therefore subtract game duration score.
        # The longer the game takes, the lower the score for a win, but it is never as low as the score for a draw.
        return 1 - game_duration_score

    else:  # Game ended in a loss.
        # The algorithm should postpone a loss as long as possible, because an opportunity to win/draw the game might still come along.
        # Therefore add game duration score.
        # The longer the game takes, the higher the score for a loss, but it is never as high as the score for a draw.
        return 0 + game_duration_score

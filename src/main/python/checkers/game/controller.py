# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code that controls the flow of a checkers game. """
from typing import Final

import pygame
from frozendict import frozendict
from pygame import Vector2
from pygame.event import Event
from pygame.time import Clock

from checkers.game.move_selector_types import CheckersMoveSelectorType, create_checkers_move_selector
from checkers.gui.input import UserCheckersMoveSelector
from checkers.gui.view import CheckersView
from checkers.gui.world import CheckersBoardGeometry, CheckersPieceGeometry
from checkers.model.move_selectors import CheckersMoveSelector
from checkers.model.rules import BOARD_SHAPE
from checkers.model.state import CheckersState
from checkers.model.util import CheckersMove, CheckersPlayer, Index2D


# Store move selector type for each player.
LIGHT_PLAYER_MOVE_SELECTOR_TYPE: Final[CheckersMoveSelectorType] = CheckersMoveSelectorType.USER
DARK_PLAYER_MOVE_SELECTOR_TYPE: Final[CheckersMoveSelectorType] = CheckersMoveSelectorType.AI_EASY

DISPLAY_SIZE: Final[tuple[int, int]] = (960, 960)  # Width, height in pixels.
FRAMES_PER_SECOND: Final[int] = 30


class CheckersController:
    """ Control the flow of a checkers game. """

    __slots__ = ('_state', '_move_selectors', '_current_move_selector', '_view', '_board_geometry', '_piece_geometries', '_alive')

    def __init__(self):
        """ Create a checkers controller. """

        # Initialize game.
        row_count, column_count = BOARD_SHAPE
        self._state: Final[CheckersState] = CheckersState(row_count, column_count)  # Keep track of the current state of the game.
        self._move_selectors: Final[frozendict[CheckersPlayer: CheckersMoveSelector]] = frozendict({
            CheckersPlayer.LIGHT: create_checkers_move_selector(LIGHT_PLAYER_MOVE_SELECTOR_TYPE),
            CheckersPlayer.DARK: create_checkers_move_selector(DARK_PLAYER_MOVE_SELECTOR_TYPE)
        })  # Store move selector for each player.
        self._current_move_selector: CheckersMoveSelector | None = None  # Keep track of the move selector for the current player.

        # Initialize GUI.
        display_width, display_height = DISPLAY_SIZE
        self._view: Final[CheckersView] = CheckersView(display_width, display_height)
        # Center board within the display.
        board_center: Final[Vector2] = Vector2(0, 0)
        # Adjust square size, so that the board fits the display, including a border that is at least one square wide on all sides.
        square_size: Final[int] = max(1, min(display_width // (column_count + 2), display_height // (row_count + 2)))  # In pixels.
        self._board_geometry: Final[CheckersBoardGeometry] = CheckersBoardGeometry(board_center, square_size, row_count, column_count)
        self._piece_geometries: Final[list[CheckersPieceGeometry]] = []

        self._alive: bool = True

    def _start_new_game(self):
        self._state.start_new_game()
        self._update_piece_geometries()

    def _apply_move(self, selected_move: CheckersMove):
        self._state.apply(selected_move)
        self._update_piece_geometries()

    def _update_piece_geometries(self):
        """ For each piece on the board in the current state, create a geometry that can be rendered. """

        self._piece_geometries.clear()
        self._piece_geometries.extend(CheckersPieceGeometry(piece, self._board_geometry.convert_square_to_world_coordinates(square)) for square, piece in self._state.board)

    def _start_move_selection(self):
        self._current_move_selector = self._move_selectors[self._state.current_player]
        self._current_move_selector.start(self._state)

    def _stop_move_selection(self):
        self._current_move_selector.reset()
        self._current_move_selector = None

    def play(self):
        """ Play a single checkers game from start to end. """

        if not self._alive:
            raise RuntimeError(f"Cannot call method '{self.play.__name__}' on '{self.__class__.__name__}' that has already finished.")

        # Start game.
        self._start_new_game()

        # Game loop.
        clock: Final[Clock] = Clock()
        while True:
            # Handle events.
            self._handle_events()
            if not self._alive:
                break

            # Update game.
            self._update()

            # Render game.
            self._view.render(self._board_geometry, self._piece_geometries, self._current_move_selector)

            # Wait until next frame.
            clock.tick(FRAMES_PER_SECOND)

    def _update(self):
        # If no move selector present, start the move selection procedure.
        if not self._current_move_selector:
            self._start_move_selection()
            return

        # If a move has been selected, make the move and update the GUI.
        if selected_move := self._current_move_selector.selected_move():
            self._stop_move_selection()
            self._apply_move(selected_move)

    def _handle_events(self):
        """ Handle all events in the pygame event queue. """

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self._alive = False
                    return

                case pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_event(event)

                case _:
                    pass

    def _handle_mouse_event(self, mouse_event: Event):
        """ Handle the passed mouse_event. """

        match mouse_event.button:
            case pygame.BUTTON_LEFT:
                # Determine world coordinates for clicked position.
                clicked_display_coordinates: Final[Vector2] = Vector2(mouse_event.pos)
                clicked_world_coordinates: Final[Vector2] = self._view.convert_display_to_world_coordinates(clicked_display_coordinates)
                if clicked_world_coordinates not in self._board_geometry:
                    return

                # Delegate to user move selector, if present.
                if isinstance(self._current_move_selector, UserCheckersMoveSelector):
                    clicked_square: Final[Index2D] = self._board_geometry.convert_world_coordinates_to_square(clicked_world_coordinates)
                    self._current_move_selector.select(clicked_square)

            case _:
                pass

# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains code that renders a checkers game to the screen. """
from math import floor
from typing import Collection, Final

import pygame.display as window
from pygame import Surface, Vector2

from checkers.gui.graphics import draw_checkers_board, draw_checkers_piece, draw_path, draw_square
from checkers.gui.input import UserCheckersMoveSelector
from checkers.gui.world import CheckersBoardGeometry, CheckersPieceGeometry
from checkers.model.move_selectors import CheckersMoveSelector
from checkers.model.util import CheckersPieceType, CheckersPlayer

# Graphics constants.
BACKGROUND_COLOR: Final[tuple[int, int, int, int]] = (0, 0, 0, 255)

LIGHT_SQUARE_COLOR: Final[tuple[int, int, int, int]] = (255, 192, 128, 255)
DARK_SQUARE_COLOR: Final[tuple[int, int, int, int]] = (100, 50, 25, 255)

LIGHT_PIECE_FILL_COLOR: Final[tuple[int, int, int, int]] = (255, 255, 255, 255)
# LIGHT_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (160, 160, 160, 255)  # Low contrast mode.
LIGHT_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (80, 80, 80, 255)  # Normal mode.
# LIGHT_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (0, 0, 0, 255)  # High contrast mode.
DARK_PIECE_FILL_COLOR: Final[tuple[int, int, int, int]] = (0, 0, 0, 255)
# DARK_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (64, 64, 64, 255)  # Low contrast mode.
DARK_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (96, 96, 96, 255)  # Normal mode.
# DARK_PIECE_LINE_COLOR: Final[tuple[int, int, int, int]] = (128, 128, 128, 255)  # High contrast mode.
PIECE_LINE_THICKNESS: Final[int] = 1  # In pixels.

BOX_COLOR: Final[tuple[int, int, int, int]] = (0, 192, 0, 255)
BOX_LINE_THICKNESS: Final[int] = 3  # In pixels.

PATH_COLOR: Final[tuple[int, int, int, int]] = (0, 192, 0, 255)
PATH_LINE_THICKNESS: Final[int] = 4  # In pixels.


class CheckersView:
    """ Create a window and use that to render a checkers game to the screen. """

    __slots__ = ('_display_width', '_display_height', '_canvas')

    def __init__(self, display_width: int, display_height: int):
        """ Create a window with the passed display_width (in pixels) and display_height (in pixels). """

        if display_width <= 0:
            raise ValueError(f"Display width must be positive, not '{display_width}'.")
        if display_height <= 0:
            raise ValueError(f"Display height must be positive, not '{display_height}'.")

        # Create window.
        self._display_width: Final[int] = display_width  # In pixels.
        self._display_height: Final[int] = display_height  # In pixels.
        window.set_caption("International Checkers")
        self._canvas: Final[Surface] = window.set_mode(size=(self._display_width, self._display_height))

    def render(self, board: CheckersBoardGeometry, pieces: Collection[CheckersPieceGeometry], move_selector: CheckersMoveSelector | None):
        """ Render the passed board, the passed pieces and markings for the passed move_selector to the screen. """

        # Draw off-screen image.
        self._canvas.fill(BACKGROUND_COLOR)
        self._draw_checkers_game(board, pieces, move_selector)

        # Update screen.
        window.flip()

    def _draw_checkers_game(self, board: CheckersBoardGeometry, pieces: Collection[CheckersPieceGeometry], move_selector: CheckersMoveSelector | None):
        """ Draw the passed board, the passed pieces and markings for the passed move_selector. """

        # Draw board.
        draw_checkers_board(self._canvas, self.convert_world_to_display_coordinates(board.center),
                            board.row_count, board.column_count, board.square_size, LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)

        # Draw pieces.
        piece_width: Final[int] = 3 * board.square_size // 4  # In pixels.
        for piece in pieces:
            fill_color, line_color = get_checkers_piece_colors(piece.owner)
            draw_checkers_piece(self._canvas, self.convert_world_to_display_coordinates(piece.center), piece_width,
                                piece.type is CheckersPieceType.KING, fill_color, line_color, PIECE_LINE_THICKNESS)

        # Draw markings.
        if isinstance(move_selector, UserCheckersMoveSelector):
            # Draw a path along the selected squares to indicate the selected partial move.
            waypoints: Final[tuple[Vector2, ...]] = tuple(self.convert_world_to_display_coordinates(board.convert_square_to_world_coordinates(square))
                                                          for square in move_selector.selected_squares)
            draw_path(self._canvas, waypoints, 2 * PATH_LINE_THICKNESS, PATH_COLOR, PATH_LINE_THICKNESS)

            # Draw boxes to indicate the selectable squares.
            for square in move_selector.selectable_squares:
                square_center: Vector2 = self.convert_world_to_display_coordinates(board.convert_square_to_world_coordinates(square))
                draw_square(self._canvas, square_center, board.square_size, BOX_COLOR, BOX_LINE_THICKNESS)

    def convert_world_to_display_coordinates(self, world_coordinates: Vector2) -> Vector2:
        """ Return the display coordinates (in pixels) that correspond to the passed world_coordinates (in pixels). """

        # Convert world coordinates to display coordinates.
        display_coordinates: Vector2 = world_coordinates + 0.5 * Vector2(self._display_width, self._display_height)
        # Invert y coordinate.
        display_coordinates.y = self._display_height - display_coordinates.y
        # Round display coordinates to integers.
        return Vector2(floor(display_coordinates.x), floor(display_coordinates.y))

    def convert_display_to_world_coordinates(self, display_coordinates: Vector2) -> Vector2:
        """ Return the world coordinates (in pixels) that correspond to the passed display_coordinates (in pixels). """

        # Convert display coordinates to pixel center.
        pixel_center: Vector2 = display_coordinates.elementwise() + 0.5
        # Invert y coordinate.
        pixel_center.y = self._display_height - pixel_center.y
        # Convert pixel center to world coordinates.
        return pixel_center - 0.5 * Vector2(self._display_width, self._display_height)


def get_checkers_piece_colors(player: CheckersPlayer) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """ Return the colors of the pieces of the passed player as a tuple: (fill color, line color). """

    match player:
        case CheckersPlayer.LIGHT:
            return LIGHT_PIECE_FILL_COLOR, LIGHT_PIECE_LINE_COLOR
        case CheckersPlayer.DARK:
            return DARK_PIECE_FILL_COLOR, DARK_PIECE_LINE_COLOR
        case _:
            raise ValueError(f"Invalid {CheckersPlayer.__name__} '{player}'.")

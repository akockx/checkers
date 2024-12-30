# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains classes that are needed to render a checkers game. """
from math import floor
from typing import Final

from pygame import Vector2

from checkers.model.util import CheckersPiece, CheckersPieceType, CheckersPlayer, Index2D


class CheckersPieceGeometry:
    """ Store a geometrical representation of a checkers piece. """

    __slots__ = ('owner', 'type', 'center')

    def __init__(self, piece: CheckersPiece, center: Vector2):
        """ Create a geometry for the passed checkers piece with the passed center (world coordinates in pixels). """

        self.owner: Final[CheckersPlayer] = piece.owner
        self.type: Final[CheckersPieceType] = piece.type
        self.center: Vector2 = center  # World coordinates in pixels.


class CheckersBoardGeometry:
    """ Store a geometrical representation of a checkers board. """

    __slots__ = ('center', 'square_size', 'row_count', 'column_count', 'width', 'height')

    def __init__(self, center: Vector2, square_size: int, row_count: int, column_count: int):
        """ Create a checkers board geometry with the passed center (world coordinates in pixels), square_size (in pixels) and number of rows and columns. """

        if square_size <= 0:
            raise ValueError(f"Square size must be positive, not '{square_size}'.")
        if row_count <= 0:
            raise ValueError(f"Number of rows must be positive, not '{row_count}'.")
        if column_count <= 0:
            raise ValueError(f"Number of columns must be positive, not '{column_count}'.")

        self.center: Final[Vector2] = center  # World coordinates in pixels.
        self.square_size: Final[int] = square_size  # In pixels.
        self.row_count: Final[int] = row_count
        self.column_count: Final[int] = column_count

        self.width: Final[int] = self.column_count * self.square_size  # In pixels.
        self.height: Final[int] = self.row_count * self.square_size  # In pixels.

    def convert_square_to_world_coordinates(self, square: Index2D) -> Vector2:
        """ Return the world coordinates (in pixels) of the center of the passed square on this board. """

        # Convert 2D index to square center.
        square_center: Final[Vector2] = Vector2(square.x + 0.5, square.y + 0.5)  # In squares.
        # Convert square center to board coordinates.
        board_coordinates: Final[Vector2] = square_center * self.square_size - 0.5 * Vector2(self.width, self.height)  # In pixels.
        # Convert board coordinates to world coordinates.
        return self.center + board_coordinates  # In pixels.

    def convert_world_coordinates_to_square(self, world_coordinates: Vector2) -> Index2D:
        """ Return the 2D index that corresponds to the square on this board that contains the passed world_coordinates (in pixels). """

        # Convert world coordinates to board coordinates.
        board_coordinates: Final[Vector2] = world_coordinates - self.center  # In pixels.
        # Convert board coordinates to square coordinates.
        square_coordinates: Final[Vector2] = (board_coordinates + 0.5 * Vector2(self.width, self.height)) / self.square_size  # In squares.
        # Round square coordinates to integers.
        return Index2D(floor(square_coordinates.x), floor(square_coordinates.y))  # Integer indices.

    def __contains__(self, world_coordinates: Vector2) -> bool:
        """ Return True if the passed world_coordinates (in pixels) are within the bounding box of this checkers board geometry. Otherwise, return False.

        Note: this __contains__() method has been repurposed to make it easier and more Pythonic to check whether certain coordinates are inside a bounding box.
        This is different from the normal usage of the __contains__() method, which is to check whether a container contains a given item.
        """

        return (self.center.x - self.width / 2 <= world_coordinates.x <= self.center.x + self.width / 2
                and self.center.y - self.height / 2 <= world_coordinates.y <= self.center.y + self.height / 2)

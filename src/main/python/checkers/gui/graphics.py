# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains functions that draw 2D graphics. """
from math import pi
from typing import Final

from pygame import draw, Rect, Surface, Vector2


def draw_square(canvas: Surface, center: Vector2, size: int, color: tuple[int, int, int, int], line_thickness: int):
    """ Draw a square with the passed properties and passed center (display coordinates in pixels) on the passed canvas. """

    upper_left_corner: Final[Vector2] = center - Vector2(size // 2)
    rect: Final[Rect] = Rect(upper_left_corner.x, upper_left_corner.y, size, size)
    draw.rect(canvas, color, rect, line_thickness)


def fill_square(canvas: Surface, center: Vector2, size: int, color: tuple[int, int, int, int]):
    """ Draw a filled square with the passed properties and passed center (display coordinates in pixels) on the passed canvas. """

    upper_left_corner: Final[Vector2] = center - Vector2(size // 2)
    rect: Final[Rect] = Rect(upper_left_corner.x, upper_left_corner.y, size, size)
    draw.rect(canvas, color, rect)


def draw_checkers_board(canvas: Surface, center: Vector2, row_count: int, column_count: int, square_size: int,
                        light_square_color: tuple[int, int, int, int], dark_square_color: tuple[int, int, int, int]):
    """ Draw a checkers board with the passed properties and passed center (display coordinates in pixels) on the passed canvas. """

    board_size: Final[Vector2] = Vector2(column_count * square_size, row_count * square_size)
    upper_left_square_center: Final[Vector2] = center - board_size // 2 + Vector2(square_size // 2)
    for y in range(row_count):
        for x in range(column_count):
            square_center: Vector2 = upper_left_square_center + Vector2(x * square_size, y * square_size)
            square_color: tuple[int, int, int, int] = light_square_color if (x + y) % 2 == 0 else dark_square_color
            fill_square(canvas, square_center, square_size, square_color)


def draw_checkers_piece(canvas: Surface, piece_center: Vector2, piece_width: int, two_layers: bool,
                        fill_color: tuple[int, int, int, int], line_color: tuple[int, int, int, int], line_thickness: int):
    """ Draw a checkers piece with the passed properties and passed center (display coordinates in pixels) on the passed canvas. """

    # Determine piece dimensions.
    rounded_piece_width: Final[int] = 2 * (piece_width // 2)  # Round piece width to an even number to avoid alignment problems.
    piece_radius: Final[int] = rounded_piece_width // 2
    ridge_radius: Final[int] = rounded_piece_width // 6
    piece_height: int = rounded_piece_width // 6
    if two_layers:
        piece_height *= 2
    rounded_piece_height: Final[int] = 2 * (piece_height // 2)  # Round piece height to an even number to avoid alignment problems.
    half_piece_height: Final[int] = rounded_piece_height // 2
    top_center: Final[Vector2] = piece_center + Vector2(0, -half_piece_height)
    bottom_center: Final[Vector2] = piece_center + Vector2(0, half_piece_height)

    # Draw bottom circle.
    rect: Rect = Rect(bottom_center.x - piece_radius, bottom_center.y - piece_radius, 2 * piece_radius, 2 * piece_radius)
    draw.ellipse(canvas, fill_color, rect)

    # Draw rectangle that connects the bottom and top circles.
    rect = Rect(piece_center.x - piece_radius, top_center.y, 2 * piece_radius, rounded_piece_height)
    draw.rect(canvas, fill_color, rect)

    if two_layers:
        # Draw border between the two layers.
        rect = Rect(piece_center.x - piece_radius, piece_center.y - piece_radius, 2 * piece_radius, 2 * piece_radius)
        draw.arc(canvas, line_color, rect, -pi, -0.001, line_thickness)

    # Draw top circle.
    rect = Rect(top_center.x - piece_radius, top_center.y - piece_radius, 2 * piece_radius, 2 * piece_radius)
    draw.ellipse(canvas, fill_color, rect)
    draw.ellipse(canvas, line_color, rect, line_thickness)

    # Draw ridges on top.
    draw.circle(canvas, line_color, top_center, ridge_radius, line_thickness)
    draw.circle(canvas, line_color, top_center, 2 * ridge_radius, line_thickness)


def draw_path(canvas: Surface, waypoints: tuple[Vector2, ...], waypoint_radius: int, color: tuple[int, int, int, int], line_thickness: int):
    """ Draw the passed waypoints (display coordinates in pixels) and lines between consecutive waypoints with the passed properties on the passed canvas. """

    for previous_waypoint, current_waypoint in zip(waypoints[:-1], waypoints[1:]):
        # Draw line from previous waypoint to current waypoint.
        draw.line(canvas, color, previous_waypoint, current_waypoint, line_thickness)

    for waypoint in waypoints:
        # Draw waypoint.
        draw.circle(canvas, color, waypoint, waypoint_radius)

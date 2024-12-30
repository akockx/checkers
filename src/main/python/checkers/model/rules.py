# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains functions that implement the rules of an international checkers game.

The rules of international checkers are described on https://en.wikipedia.org/wiki/International_draughts
"""
from typing import Final

from checkers.model.util import CheckersBoard, CheckersGameResult, CheckersJump, CheckersMove, CheckersPiece, CheckersPieceType, CheckersPlayer, Index2D

BOARD_SHAPE: Final[tuple[int, int]] = (10, 10)  # Shape of a checkers board (row count, column count).

DIAGONAL_DIRECTIONS: Final[tuple[Index2D, ...]] = (Index2D(-1, 1), Index2D(1, 1), Index2D(1, -1), Index2D(-1, -1))
LIGHT_PLAYER_FORWARD_DIRECTIONS: Final[tuple[Index2D, ...]] = (Index2D(-1, 1), Index2D(1, 1))
DARK_PLAYER_FORWARD_DIRECTIONS: Final[tuple[Index2D, ...]] = (Index2D(1, -1), Index2D(-1, -1))

EMPTY: Final[None] = None  # Alias to indicate an empty square on a checkers board.


def determine_legal_moves(current_player: CheckersPlayer, board: CheckersBoard) -> list[CheckersMove]:
    """ Return a tuple with all legal moves for the passed current_player on the passed board. Return an empty tuple if there are no legal moves. """

    # Gather capturing moves.
    moves: Final[list[CheckersMove]] = []
    visited_squares: Final[list[Index2D]] = []  # Temporary list to keep track of visited squares, which together form a (partial) move.
    captured_squares: Final[list[Index2D]] = []  # Temporary list to keep track of captured squares.
    # Loop over all squares that contain pieces owned by the current player.
    for square, piece in board:
        if piece.owner is not current_player:
            continue

        # Temporarily remove piece from the board, otherwise it would block moves where the piece gets back to or passes its starting square after several jumps.
        board[square] = None

        # Add capturing moves for piece.
        visited_squares.append(square)
        add_legal_capturing_moves(piece, visited_squares, captured_squares, board, moves)
        visited_squares.pop()

        # Put piece back on the board.
        board[square] = piece

    # If capturing is possible, it is mandatory to pick a capturing move with the maximum possible number of captures.
    if moves:
        # At this point the list of moves contains only capturing moves.
        # Return only the moves with the maximum possible number of captures, i.e. the moves with the maximum possible length.
        max_move_length: Final[int] = max(len(move) for move in moves)
        return [move for move in moves if len(move) == max_move_length]

    # If capturing is not possible, gather non-capturing moves.
    # At this point the list of moves is empty.
    forward_directions: Final[tuple[Index2D, ...]] = get_forward_directions(current_player)
    # Loop over all squares that contain pieces owned by the current player.
    for square, piece in board:
        if piece.owner is not current_player:
            continue

        add_legal_non_capturing_moves(piece.type, forward_directions, square, board, moves)

    return moves


def add_legal_non_capturing_moves(piece_type: CheckersPieceType, forward_directions: tuple[Index2D, ...], origin: Index2D, board: CheckersBoard,
                                  moves: list[CheckersMove]):
    """ Construct all legal non-capturing moves for a piece with the passed piece_type and forward_directions at the passed square (origin) on the passed board,
    and add them to the passed list of moves.

    This function assumes that the passed square (origin) is within the passed board.
    Note that the passed board does not actually need to contain a piece at the passed square (origin) in order for this function to work.
    """

    match piece_type:
        case CheckersPieceType.MAN:
            # A man can move one step in one of the diagonally forward directions if the destination square is free.
            for delta in forward_directions:
                destination: Index2D = origin + delta
                if destination in board and board[destination] is EMPTY:
                    moves.append(CheckersMove((origin, destination)))

        case CheckersPieceType.KING:
            # A king can move any number of steps in one of the diagonal directions as long as it has a free path (not blocked by any other pieces).
            for delta in DIAGONAL_DIRECTIONS:
                # Continue moving in the current direction until the path is blocked.
                destination: Index2D = origin + delta
                while destination in board:
                    if board[destination] is not EMPTY:
                        break

                    moves.append(CheckersMove((origin, destination)))

                    destination += delta

        case _:
            raise ValueError(f"Invalid {CheckersPieceType.__name__} '{piece_type}'.")


def add_legal_capturing_moves(piece: CheckersPiece, visited_squares: list[Index2D], captured_squares: list[Index2D], board: CheckersBoard,
                              moves: list[CheckersMove]):
    """ Construct all legal capturing moves for the passed piece at the last square in the passed visited_squares on the passed board,
    and add them to the passed list of moves.

    This function assumes that the passed visited_squares is not empty and that the squares in visited_squares and captured_squares are within the passed board.
    Note that the passed board does not actually need to contain a piece at the last square in the passed visited_squares in order for this function to work.

    This function can be called recursively.
    """

    # Gather all legal jumps that start from the last square in visited_squares.
    jumps: Final[list[CheckersJump]] = []
    add_legal_jumps(piece, visited_squares[-1], captured_squares, board, jumps)

    # If no further jumps are possible, then the current partial move is a complete move.
    if not jumps:
        # Add current partial move to the list of moves and return.
        if len(visited_squares) >= 2:
            moves.append(CheckersMove(tuple(visited_squares)))
        return

    # After a successful jump, another jump can be made as part of the same move.
    for jump in jumps:
        visited_squares.append(jump.destination)
        captured_squares.append(jump.captured_square)
        # Add additional jumps recursively.
        add_legal_capturing_moves(piece, visited_squares, captured_squares, board, moves)
        captured_squares.pop()
        visited_squares.pop()


def add_legal_jumps(piece: CheckersPiece, origin: Index2D, captured_squares: list[Index2D], board: CheckersBoard,
                    jumps: list[CheckersJump]):
    """ Construct all legal jumps for the passed piece at the passed square (origin) on the passed board,
    and add them to the passed list of jumps.

    This function assumes that the passed square (origin) is within the passed board.
    Note that the passed board does not actually need to contain a piece at the passed square (origin) in order for this function to work.
    """

    match piece.type:
        case CheckersPieceType.MAN:
            # A man can jump over a single square that contains an enemy piece in one of the diagonal directions if the destination square is free.
            for delta in DIAGONAL_DIRECTIONS:
                # The captured square must contain a piece owned by another player.
                captured_square: Index2D = origin + delta
                if captured_square not in board:
                    continue
                captured_piece: CheckersPiece | None = board[captured_square]
                if captured_piece is None or captured_piece.owner is piece.owner:
                    continue

                # The destination square must be empty.
                destination: Index2D = captured_square + delta
                if destination not in board or board[destination] is not EMPTY:
                    continue

                # Cannot capture the same piece more than once.
                if captured_square in captured_squares:
                    continue

                jumps.append(CheckersJump(destination, captured_square))

        case CheckersPieceType.KING:
            # A king can jump over a single square that contains an enemy piece plus any number of empty squares in one of the diagonal directions.
            for delta in DIAGONAL_DIRECTIONS:
                # Search for the nearest piece in the current direction.
                captured_piece_owner: CheckersPlayer | None = None
                captured_square: Index2D | None = None
                square: Index2D = origin + delta
                while square in board:
                    if captured_piece := board[square]:
                        captured_piece_owner = captured_piece.owner
                        captured_square = square
                        break

                    square += delta

                # The captured piece must be owned by another player.
                if captured_piece_owner is None or captured_piece_owner is piece.owner:
                    continue

                # Cannot capture the same piece more than once.
                if captured_square in captured_squares:
                    continue

                # Continue moving in the current direction until the path is blocked.
                destination: Index2D = captured_square + delta
                while destination in board:
                    if board[destination] is not EMPTY:
                        break

                    jumps.append(CheckersJump(destination, captured_square))

                    destination += delta

        case _:
            raise ValueError(f"Invalid {CheckersPieceType.__name__} '{piece.type}'.")


def get_forward_directions(player: CheckersPlayer) -> tuple[Index2D, ...]:
    """ Return the directions that are diagonally forward, as seen from the passed player's perspective. """

    match player:
        case CheckersPlayer.LIGHT:
            return LIGHT_PLAYER_FORWARD_DIRECTIONS
        case CheckersPlayer.DARK:
            return DARK_PLAYER_FORWARD_DIRECTIONS
        case _:
            raise ValueError(f"Invalid {CheckersPlayer.__name__} '{player}'.")


def get_kings_row_index(player: CheckersPlayer, board: CheckersBoard) -> int:
    """ Return the row index of the far edge of the passed board, as seen from the passed player's perspective. """

    match player:
        case CheckersPlayer.LIGHT:
            return board.row_count - 1
        case CheckersPlayer.DARK:
            return 0
        case _:
            raise ValueError(f"Invalid {CheckersPlayer.__name__} '{player}'.")


def apply(move: CheckersMove, board: CheckersBoard):
    """ Apply the passed move to the passed board.

    This function assumes that the passed move is legal for the passed board.
    """

    # Pick up piece.
    origin: Final[Index2D] = move.origin
    destination: Final[Index2D] = move.destination
    moving_piece: CheckersPiece = board[origin]
    board[origin] = None

    # Crown piece.
    if destination.y == get_kings_row_index(moving_piece.owner, board) and moving_piece.type is CheckersPieceType.MAN:
        moving_piece = CheckersPiece(moving_piece.owner, CheckersPieceType.KING)

    # Remove captured pieces.
    # This must be done after moving_piece has been picked up from the board and before it is put down again,
    # since for a moving king the origin and/or destination square can be between two visited squares.
    for previous_square, square in zip(move.visited_squares[:-1], move.visited_squares[1:]):
        remove_pieces_between(previous_square, square, board)

    # Put down piece.
    # Note that for a move with many jumps a square can be visited more than once and it is possible that origin and destination are the same square.
    board[destination] = moving_piece


def remove_pieces_between(start_square: Index2D, end_square: Index2D, board: CheckersBoard):
    """ Remove all pieces between the passed start_square and end_square (both exclusive) from the passed board.

    This function assumes that the passed start_square and end_square are within the passed board and are on the same diagonal path.
    """

    delta: Final[Index2D] = Index2D.sign(end_square - start_square)
    square: Index2D = start_square + delta
    while square != end_square:
        board[square] = None
        square += delta


def determine_result(board: CheckersBoard, current_player: CheckersPlayer, ply_count: int, legal_move_count: int) -> CheckersGameResult | None:
    """ Return the result of a checkers game with the passed board, current_player, ply_count and legal_move_count.
    Return None if the game is still in progress.
    """

    # If the current player cannot make a move, then the other player is the winner.
    if legal_move_count <= 0:
        match current_player:
            case CheckersPlayer.LIGHT:
                winner: Final[CheckersPlayer] = CheckersPlayer.DARK
            case CheckersPlayer.DARK:
                winner: Final[CheckersPlayer] = CheckersPlayer.LIGHT
            case _:
                raise ValueError(f"Invalid {CheckersPlayer.__name__} '{current_player}'.")
        return CheckersGameResult(winner, ply_count)

    # Count pieces.
    light_man_count: int = 0
    dark_man_count: int = 0
    light_king_count: int = 0
    dark_king_count: int = 0
    for _, piece in board:
        match piece.owner:
            case CheckersPlayer.LIGHT:
                match piece.type:
                    case CheckersPieceType.MAN:
                        light_man_count += 1
                    case CheckersPieceType.KING:
                        light_king_count += 1
                    case _:
                        raise ValueError(f"Invalid {CheckersPieceType.__name__} '{piece.type}'.")

            case CheckersPlayer.DARK:
                match piece.type:
                    case CheckersPieceType.MAN:
                        dark_man_count += 1
                    case CheckersPieceType.KING:
                        dark_king_count += 1
                    case _:
                        raise ValueError(f"Invalid {CheckersPieceType.__name__} '{piece.type}'.")

            case _:
                raise ValueError(f"Invalid {CheckersPlayer.__name__} '{piece.owner}'.")

    # A king-versus-king endgame is automatically declared a draw.
    if light_man_count == 0 and dark_man_count == 0 and light_king_count == 1 and dark_king_count == 1:
        return CheckersGameResult(None, ply_count)

    # If the game is still in progress, there is no result, so return None.
    return None

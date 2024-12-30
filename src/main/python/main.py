# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

import pygame

from checkers.game.controller import CheckersController


def main():
    # Start game engine.
    pygame.init()

    # Run checkers game.
    CheckersController().play()

    # Stop game engine.
    pygame.quit()


if __name__ == "__main__":
    main()

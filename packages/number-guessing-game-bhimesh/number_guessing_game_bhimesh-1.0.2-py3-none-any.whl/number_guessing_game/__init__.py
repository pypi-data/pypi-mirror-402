"""Number Guessing Game - A fun interactive guessing game."""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "An interactive number guessing game where players try to guess a random number between 1 and 100."

from .game import play_game

__all__ = ["play_game"]

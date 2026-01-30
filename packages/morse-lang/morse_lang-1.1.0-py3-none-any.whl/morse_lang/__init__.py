"""Morse Programming Language - A programming language written in Morse code."""

__version__ = "1.1.0"
__author__ = "Blaz"

from .morse_map import MORSE_MAP
from .lexer import morse_to_text
from .interpreter import run

__all__ = ["MORSE_MAP", "morse_to_text", "run"]

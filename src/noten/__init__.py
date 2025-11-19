"""
Noten: LLM-Parseable Chord Progression Format

A token-efficient, unambiguous text-based musical chord notation system
designed for seamless integration with Large Language Models.
"""

__version__ = "0.1.0"

from .noten_parser import parse, ChordParser
from .noten_rhythm import calculate_durations, print_rhythm_analysis

__all__ = [
    "parse",
    "ChordParser",
    "calculate_durations",
    "print_rhythm_analysis",
]

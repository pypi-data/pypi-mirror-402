"""
This module provides next-move selection strategies for local search algorithms.

Next movement strategies determine how the next candidate move
is chosen from a sequence or neighborhood of possible moves.
They define the exploration order of the local search.

"""

from opt_flow.localsearch.strategies.next_movement.sequential_next import SequentialNext

__all__ = ["SequentialNext"]
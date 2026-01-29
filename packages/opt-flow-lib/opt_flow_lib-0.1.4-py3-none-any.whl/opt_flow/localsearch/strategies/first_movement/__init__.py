"""
This module provides first-move selection strategies for local search algorithms.

First movement strategies determine which candidate move is selected
initially from a set of possible moves. This is typically used to
initialize or bias the local search process.

"""

from opt_flow.localsearch.strategies.first_movement.sequential_first import SequentialFirst

__all__ = ["SequentialFirst"]
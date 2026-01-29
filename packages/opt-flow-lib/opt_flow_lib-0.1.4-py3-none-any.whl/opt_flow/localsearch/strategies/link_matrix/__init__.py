"""
This module provides link checking strategies for local search algorithms.

Link checkers validate or track relationships between moves or solutions,
enabling efficient management of feasible transitions, move dependencies,
or constraints during the search.

"""

from opt_flow.localsearch.strategies.link_matrix.link_matrix import LinkMatrix

__all__ = ["LinkMatrix"]
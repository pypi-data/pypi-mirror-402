"""
This module provides memory strategies for local search algorithms.

Memory strategies store and manage information about previously
visited moves or solutions in order to guide the search process.
They are commonly used to prevent cycling or encourage diversification.
"""

from opt_flow.localsearch.strategies.memory.no_memory import NoMemory
from opt_flow.localsearch.strategies.memory.tabu_memory import TabuMemory

__all__ = ["NoMemory", "TabuMemory"]
"""
This module provides score filtering strategies for local search algorithms.

Score filters decide which candidate moves or scores should be
kept or discarded before selection, enabling pruning strategies
such as thresholding, dominance filtering, or no-op filtering.

"""

from opt_flow.localsearch.strategies.score_filter.no_filter import NoFilter

__all__ = ["NoFilter"]
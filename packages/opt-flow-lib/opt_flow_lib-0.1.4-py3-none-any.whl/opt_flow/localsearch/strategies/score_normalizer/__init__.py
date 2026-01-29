"""
This module provides score normalization strategies for local search algorithms.

Score normalizers transform raw move scores into a normalized scale,
allowing fair comparison and selection of candidate moves across
different evaluation criteria.

"""

from opt_flow.localsearch.strategies.score_normalizer.default_normalizer import DefaultNormalizer

__all__ = ["DefaultNormalizer"]
"""
This module provides score calculation strategies for local search algorithms.

Score calculators are responsible for assigning a numerical score
to candidate moves or solutions, typically based on objective
function values or heuristic evaluations.

"""

from opt_flow.localsearch.strategies.score_calculator.objective_score_calculator import ObjectiveScoreCalculator

__all__ = ["ObjectiveScoreCalculator"]
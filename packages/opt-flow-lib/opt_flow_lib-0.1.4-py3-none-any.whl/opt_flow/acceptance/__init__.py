"""
Acceptance criteria for comparing individuals in optimization workflows.

This subpackage provides a collection of acceptance strategies that decide
whether a candidate individual should be accepted over a reference individual.
All acceptance strategies inherit from :class:`BaseAcceptance`.


"""

from opt_flow.acceptance.all_acceptance import AllAcceptance
from opt_flow.acceptance.deterministic_acceptance import DeterministicAcceptance
from opt_flow.acceptance.lexicographic_acceptance import LexicographicAcceptance
from opt_flow.acceptance.scalar_acceptance import ScalarAcceptance
from opt_flow.acceptance.score_acceptance import ScoreAcceptance
from opt_flow.acceptance.simulated_annealing_acceptance import (
    SimulatedAnnealingAcceptance,
)
from opt_flow.acceptance.single_objective_acceptance import SingleObjectiveAcceptance
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.acceptance.random_acceptance import RandomAcceptance

__all__ = [
    "BaseAcceptance",
    "SimulatedAnnealingAcceptance",
    "ScoreAcceptance",
    "ScalarAcceptance",
    "LexicographicAcceptance",
    "DeterministicAcceptance",
    "AllAcceptance",
    "RandomAcceptance",
    "SingleObjectiveAcceptance"
]




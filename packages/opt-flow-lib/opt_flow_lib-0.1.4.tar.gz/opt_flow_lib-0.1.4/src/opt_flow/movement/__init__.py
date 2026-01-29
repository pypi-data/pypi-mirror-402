"""
Core components for defining and exploring local search movements.

This module provides the fundamental classes and types required to implement
movements and search spaces for local search algorithms.

Classes:
    Movement: Base class for any movement that can be applied to a individual.
    SearchSpace: Abstract base class representing the set of candidate moves
                 for a given individual.
    ParametrizedSearchSpace: for more custom parametrized search spaces.
    MovementType: Enum defining how movements are applied (DIRECT, SIMULATE, DO_UNDO).
    
Types:
    ArgsT: Generic type representing the arguments used by a movement.

Usage:
    Import the desired classes when implementing custom movements or search spaces
    for local search metaheuristics.
"""

from opt_flow.movement.movement import Movement
from opt_flow.movement.args import ArgsT
from opt_flow.movement.movement_type import MovementType
from opt_flow.movement.search_space import SearchSpace
from opt_flow.movement.parametrized_search_space import ParametrizedSearchSpace


__all__ = ["Movement", "ArgsT", "MovementType", "SearchSpace", "ParametrizedSearchSpace"]
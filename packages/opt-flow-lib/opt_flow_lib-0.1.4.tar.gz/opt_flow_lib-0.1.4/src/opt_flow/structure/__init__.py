"""
The `structure` module defines the core abstractions and data representations 
used for optimization problems within the framework. It provides base classes 
and concrete implementations for data, individuals, objectives, and 
multi-objective handling.

Key components:

- Data
    Abstract representation of the data necessary to solve the problem.

- BaseIndividual
    Abstract representation of an individual in the context of some data. 
    Includes methods for copying, comparing, and overwriting solutions.

- ScalarObjective
    Represents a single optimization objective with a value and a direction 
    (minimize or maximize).

- MultiObjective
    Represents a multi-objective optimization scenario composed of multiple 
    ScalarObjective instances. Supports iteration, indexing, and name 
    aggregation.

- ObjectiveDirection
    Enum specifying the optimization direction for a scalar objective, either 
    MINIMIZE or MAXIMIZE.

This module forms the foundational data layer upon which metaheuristics, 
local search, and other optimization algorithms operate.
"""

from opt_flow.structure.scalar_objective import ScalarObjective
from opt_flow.structure.data import Data
from opt_flow.structure.base_individual import BaseIndividual
from opt_flow.structure.multi_objective import MultiObjective
from opt_flow.structure.objective_direction import ObjectiveDirection

__all__ = [
    "ScalarObjective",
    "Data",
    "BaseIndividual",
    "MultiObjective",
    "ObjectiveDirection",
    "MultiObjectiveGenerator",
    "ScalarObjectiveGenerator"
]

"""
This module provides core classes and configurations for metaheuristic algorithms.

It defines the structure, execution, and types of metaheuristic algorithms, 
as well as global configuration and identification management.

"""

from opt_flow.metaheuristic.algorithm_type import AlgorithmType
from opt_flow.metaheuristic.algorithm import Algorithm
from opt_flow.metaheuristic.population_metaheuristic import PopulationMetaheuristic
from opt_flow.metaheuristic.trajectory_metaheuristic import TrajectoryMetaheuristic

__all__ = ["Algorithm", "AlgorithmType", "PopulationMetaheuristic",  "TrajectoryMetaheuristic"]
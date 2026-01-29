"""
Population-based Metaheuristics Module

This module provides classes for population-oriented optimization algorithms.
These algorithms maintain and evolve a set of candidate solutions to solve
complex optimization problems. The main strategies include multistart heuristics,
GRASP (Greedy Randomized Adaptive Search Procedure), and Genetic Algorithms.

Available Classes
-----------------
- BaseMultistart
    Abstract base class for multistart algorithms. Handles repeated solution
    construction and evaluation, optionally in parallel.

- Multistart
    Concrete multistart implementation that repeatedly constructs solutions
    using a constructive heuristic and returns the best one.

- GRASP
    Greedy Randomized Adaptive Search Procedure. Extends BaseMultistart by
    combining solution construction with local improvement strategies.

- GeneticAlgorithm
    Evolutionary algorithm that maintains a population of solutions, applying
    recombination (crossover), mutation, and selection based on acceptance
    criteria. Supports parallel execution for improved efficiency.

Purpose
-------
This module is intended for scenarios where maintaining a population of
solutions and iteratively improving them provides better results than
single-solution approaches. It supports flexible configuration of
constructive heuristics, recombination operators, acceptance criteria,
stopping conditions, and parallel execution.

"""

from opt_flow.population.algorithm import GeneticAlgorithm
from opt_flow.population.algorithm import GRASP
from opt_flow.population.algorithm.multistart import Multistart
from opt_flow.population.algorithm.base_multistart import BaseMultistart

__all__ = ["GRASP", "GeneticAlgorithm", "Multistart", "BaseMultistart"]
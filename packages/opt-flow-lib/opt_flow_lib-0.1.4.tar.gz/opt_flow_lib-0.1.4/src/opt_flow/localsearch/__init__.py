"""
Local Search Algorithms Module

This module provides implementations of local search metaheuristics for combinatorial optimization 
problems. It exposes two main strategies:

- LocalSearch: A straightforward local search that iterates over a single search space 
  using a specified movement type and acceptance criterion.

- EjectionChain: An advanced local search that constructs chains of movements across 
  multiple search spaces, allowing deeper exploration of the solution space with optional memory 
  and chain argument strategies.

These classes can be combined with different acceptance criteria, movement types, and stopping 
conditions to create customized local search algorithms.
"""

from opt_flow.localsearch.core import LocalSearch
from opt_flow.localsearch.ejection_chain import EjectionChain 

__all__ = ["LocalSearch", "EjectionChain"]
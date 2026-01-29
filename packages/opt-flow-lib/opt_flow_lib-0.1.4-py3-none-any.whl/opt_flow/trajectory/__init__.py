"""
This module provides classes and algorithms for trajectory-based metaheuristics.

Trajectory metaheuristics iteratively modify individuals by exploring the 
space according to a defined neighborhood structure. This module 
includes base classes, classic trajectory algorithms, and ensemble strategies 
for combining multiple trajectory operators.

"""

from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.trajectory.algorithm import VNS, ILS
from opt_flow.trajectory.composite import AdaptativeDescent, AdaptativeUCBDescent, RandomizedDescent, VND, SequentialDescent, BestComposite, ParallelTrajectory 
from opt_flow.trajectory.core import HillClimbing 

__all__ = ["BaseTrajectory", "VNS", "ILS", "AdaptativeDescent", "AdaptativeUCBDescent", "RandomizedDescent", "VND", "SequentialDescent", "BestComposite", "ParallelTrajectory", "HillClimbing"]
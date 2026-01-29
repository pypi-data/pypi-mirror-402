from opt_flow.metaheuristic.factories._base import TrajectoryFactory
from opt_flow.trajectory import BaseTrajectory
from typing import List
from abc import abstractmethod

class BaseMultipleFactory(TrajectoryFactory):
    
    """
    Abstract factory for managing and selecting among multiple trajectory algorithms.

    This class serves as a base for factories that dynamically select trajectory
    algorithms from a predefined set, potentially using adaptive or stochastic
    strategies.
    """
    
    
    def __init__(self, trajectories: List[BaseTrajectory], **kwargs):
        super().__init__(**kwargs)
        self.trajectories = trajectories
        
    @abstractmethod
    def should_continue(self) -> bool:
        """
        Indicates whether the factory should continue producing trajectory algorithms.

        This method can be used to define stopping conditions based on internal
        criteria such as performance, iteration count, or convergence.

        Returns:
            bool: True if the factory should continue producing trajectory
            algorithms; False otherwise.
        """
        pass
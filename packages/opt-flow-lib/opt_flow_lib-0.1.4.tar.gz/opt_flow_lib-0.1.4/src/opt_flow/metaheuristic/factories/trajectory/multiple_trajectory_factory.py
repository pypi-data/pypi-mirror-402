from opt_flow.metaheuristic.factories.trajectory._base import BaseMultipleFactory
from opt_flow.trajectory import BaseTrajectory
from typing import List

class MultipleTrajectoryFactory(BaseMultipleFactory):
    
    """
    Factory for sequentially selecting trajectory algorithms.

    This factory returns trajectory algorithms one by one in the order
    they were provided, making it suitable for deterministic pipelines.
    """
    
    
    def __init__(self, trajectories: List[BaseTrajectory]):
        """
        Returns the next trajectory algorithm in the sequence.

        Each call advances the internal index by one.

        Returns:
            BaseTrajectory: The next trajectory algorithm.
        """
        super().__init__(trajectories=trajectories)
        self.k = 0
        
    def create(self) -> BaseTrajectory:
        trajectory = self.trajectories[self.k]
        self.k += 1
        return trajectory
    
    def should_continue(self) -> bool:
        """
        Indicates whether there are remaining trajectory algorithms to apply.

        Returns:
            bool: True if there are still trajectory algorithms remaining;
            False otherwise.
        """
        return self.k < len(self.trajectories)
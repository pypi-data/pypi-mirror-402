from opt_flow.metaheuristic.factories.trajectory._base import BaseMultipleFactory
from opt_flow.trajectory import BaseTrajectory
from typing import Optional, List
from opt_flow.utils import RandomClass

class RandomizedMultipleTrajectoryFactory(BaseMultipleFactory, RandomClass):
    
    """
    Factory that randomly selects a trajectory algorithm from a list.

    Each call to `create` returns one of the available trajectory
    algorithms selected uniformly at random. The factory never exhausts
    its trajectory list and always allows continuation.
    """
    
    
    def __init__(self, trajectories: List[BaseTrajectory], seed: Optional[int] = None):
        super().__init__(seed=seed, trajectories=trajectories)

    def create(self) -> BaseTrajectory:
        """
        Randomly selects and returns an trajectory algorithm.

        Returns:
            BaseTrajectory: A randomly chosen trajectory algorithm
            from the available list.
        """
        trajectory = self.trajectories[self.rng.choice(list(range(0, len(self.trajectories))))]
        return trajectory
    
    def should_continue(self) -> bool:
        """
        Indicates whether trajectory selection should continue.

        This factory never exhausts its trajectories and always allows
        continuation.

        Returns:
            bool: Always True.
        """
        return True
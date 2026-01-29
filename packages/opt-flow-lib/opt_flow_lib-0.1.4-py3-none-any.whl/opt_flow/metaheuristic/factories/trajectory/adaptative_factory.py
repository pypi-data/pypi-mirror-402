from opt_flow.metaheuristic.factories.trajectory._base import BaseMultipleFactory
from opt_flow.trajectory import BaseTrajectory
from opt_flow.utils import RandomClass
from typing import Optional, List

class AdaptativeFactory(BaseMultipleFactory, RandomClass):
    
    """
    Adaptive factory for selecting improvement algorithms using an
    epsilon-greedy strategy.

    The factory balances exploration and exploitation by either selecting
    a random improvement algorithm with probability `epsilon` or selecting
    the algorithm with the highest observed success rate.
    """
    
    
    def __init__(self, trajectories: List[BaseTrajectory], epsilon: float, seed: Optional[int] = None):
        super().__init__(trajectories=trajectories, seed=seed)
        self.k = None
        self.epsilon = epsilon
        self.success_counts = [0 for _ in trajectories]
        self.attempt_counts = [1 for _ in trajectories]
        
    def create(self) -> BaseTrajectory:
        """
        Selects and returns an improvement algorithm using an epsilon-greedy policy.

        With probability `epsilon`, a random improvement algorithm is selected.
        Otherwise, the algorithm with the highest success rate is chosen.

        Returns:
            BaseTrajectory: The selected improvement algorithm.
        """
        if self.rng.random() < self.epsilon:
            k = self.rng.integers(0, len(self.trajectories) - 1)
        else:
            scores = [s / a for s, a in zip(self.success_counts, self.attempt_counts)]
            k = scores.index(max(scores))
        trajectory = self.trajectories[k]
        self.k = k
        return trajectory
    
    def should_continue(self) -> bool:
        """
        Indicates whether the factory should continue providing trajectory algorithms.

        Returns:
            bool: Always True, as this adaptive factory does not impose
            an internal stopping condition.
        """
        return True
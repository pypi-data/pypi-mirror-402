from opt_flow.metaheuristic.factories.trajectory._base import BaseMultipleFactory
from opt_flow.trajectory import BaseTrajectory
from opt_flow.utils import RandomClass
from typing import Optional, List
import math

class AdaptativeUCBFactory(BaseMultipleFactory, RandomClass):
    
    """
    Adaptive factory for selecting trajectory algorithms using the
    Upper Confidence Bound (UCB) strategy.

    This factory models the selection of trajectory algorithms as a
    multi-armed bandit problem and balances exploitation and exploration
    based on theoretical confidence bounds.
    """
    
    
    def __init__(self, trajectories: List[BaseTrajectory], seed: Optional[int] = None):
        super().__init__(improvements=trajectories, seed=seed)
        self.success_counts = [0 for _ in trajectories]
        self.attempt_counts = [1 for _ in trajectories]
        self.total_attempts = len(trajectories)
        self.k = None
        
    def create(self) -> BaseTrajectory:
        """
        Selects and returns a trajectory algorithm using the UCB policy.

        The selection balances exploitation (historical success rate) and
        exploration (confidence bound based on the number of attempts).

        Returns:
            BaseTrajectory: The selected trajectory algorithm.
        """
        ucb_scores = []
        for i in range(len(self.trajectories)):
            exploitation = self.success_counts[i] / self.attempt_counts[i]
            exploration = math.sqrt(2 * math.log(self.total_attempts) / self.attempt_counts[i])
            ucb_scores.append(exploitation + exploration)

        k = ucb_scores.index(max(ucb_scores))
        trajectory = self.trajectories[k]
        self.k = k
        return trajectory
    
    def should_continue(self) -> bool:
        """
        Indicates whether the factory should continue producing trajectory algorithms.

        Returns:
            bool: Always True, as this adaptive UCB factory does not impose
            an internal stopping condition.
        """
        return True
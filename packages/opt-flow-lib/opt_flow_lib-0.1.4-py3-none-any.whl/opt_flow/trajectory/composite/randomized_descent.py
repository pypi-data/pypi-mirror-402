from opt_flow.trajectory.composite._base import BaseCompositeTrajectory
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.metaheuristic.factories.trajectory import RandomizedMultipleTrajectoryFactory
class RandomizedDescent(BaseCompositeTrajectory):
    """
    Composite trajectory operator that applies a randomized sequence of 
    trajectory factories to a solution.

    This class extends `BaseCompositeTrajectory` and executes multiple
    `TrajectoryFactory` instances in a randomized order. Each trajectory
    is applied sequentially, and the process continues until the stopping
    criterion is met.

    Attributes
    ----------
    _improvement_factory : RandomizedMultipleTrajectoryFactory
        Factory that manages the randomized order of the trajectories.
    _acceptance : BaseAcceptance
        Acceptance criterion used to evaluate solutions.
    num_trajectories : int
        Number of trajectories included in the randomized sequence.

    Parameters
    ----------
    trajectories : List[TrajectoryFactory]
        List of improvement factories to apply in randomized order.
    acceptance : BaseAcceptance, optional
        Acceptance criterion for selecting improved solutions. If not provided,
        a default acceptance criterion is used.
    seed : int, optional
        Random seed to control reproducibility of the randomized order.
    stopping : BaseStopping, optional
        Stopping criterion that determines when the improvement process should halt.
    callbacks : List[Callback], optional
        List of callbacks to execute during the improvement process.
    """
    def __init__(
        self,
        trajectories: List[TrajectoryFactory],
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None
    ):
        multiple_factory = RandomizedMultipleTrajectoryFactory(trajectories, seed)
        super().__init__(trajectory_factory=multiple_factory, acceptance=acceptance, seed=seed, stopping=stopping, callbacks=callbacks)


from opt_flow.trajectory.composite._base import BaseCompositeTrajectory
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.metaheuristic.factories.trajectory import MultipleTrajectoryFactory
class SequentialDescent(BaseCompositeTrajectory):
    """
    Composite trajectory operator that applies a sequence of trajectory factories 
    to a individual in a fixed, sequential order.

    This class extends `BaseCompositeTrajectory` and executes multiple 
    `TrajectoryFactory` instances one after another in the order provided. 
    Each trajectory is applied sequentially, and the process continues until 
    the stopping criterion is met.

    Attributes
    ----------
    _trajectory_factory : MultipleTrajectoryFactory
        Factory that manages the sequential execution of the trajectories.
    _acceptance : BaseAcceptance
        Acceptance criterion used to evaluate individuals.
    num_trajectories : int
        Number of trajectories included in the sequence.

    Parameters
    ----------
    trajectories : List[TrajectoryFactory]
        List of trajectory factories to apply sequentially.
    acceptance : BaseAcceptance, optional
        Acceptance criterion for selecting improved individuals. If not provided,
        a default acceptance criterion is used.
    seed : int, optional
        Random seed (used by trajectories if they are stochastic).
    stopping : BaseStopping, optional
        Stopping criterion that determines when the trajectory process should halt.
    callbacks : List[Callback], optional
        List of callbacks to execute during the trajectory process.
    """
    
    def __init__(
        self,
        trajectories: List[TrajectoryFactory],
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None
    ):
        multiple_factory = MultipleTrajectoryFactory(trajectories)
        super().__init__(trajectory_factory=multiple_factory, acceptance=acceptance, seed=seed, stopping=stopping, callbacks=callbacks)
from opt_flow.trajectory.composite._base import BaseCompositeTrajectory
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping 
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.metaheuristic.factories.trajectory import AdaptativeFactory
from opt_flow.callback.factories import AdaptativeFactoryUpdate
class AdaptativeDescent(BaseCompositeTrajectory):
    """
    Adaptive descent metaheuristic using multiple trajectory operators.

    This class applies a set of trajectory operators to a individual
    in an adaptive manner. The selection and application of trajectories
    are controlled by an `AdaptativeFactory`, which adjusts the probability
    of using each trajectories based on their observed performance. 

    The class also integrates callback support to update the adaptive
    probabilities after each iteration.

    Attributes
    ----------
    _trajectory_factory : AdaptativeFactory
        Factory managing multiple trajectories and their adaptive selection.
    _acceptance : BaseAcceptance
        Acceptance criterion used to determine which individuals are accepted.
    """
    
    def __init__(
        self,
        trajectories: List[TrajectoryFactory],
        epsilon: float, 
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None
    ):
        multiple_factory = AdaptativeFactory(trajectories, epsilon, seed)
        new_callbacks = []
        cb = AdaptativeFactoryUpdate(multiple_factory)
        if callbacks:
            new_callbacks.extend(callbacks)
            new_callbacks.append(cb)
        else:
            new_callbacks.append(cb)
        super().__init__(trajectory_factory=multiple_factory, acceptance=acceptance, seed=seed, stopping=stopping, callbacks=new_callbacks)



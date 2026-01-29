from opt_flow.trajectory.composite._base import BaseCompositeTrajectory
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.metaheuristic.factories.trajectory import AdaptativeUCBFactory
from opt_flow.callback.factories import AdaptativeUCBFactoryUpdate
class AdaptativeUCBDescent(BaseCompositeTrajectory):
    """
    Adaptive descent metaheuristic using Upper Confidence Bound (UCB) strategy.

    This class applies multiple trajectory operators to a individual while
    adaptively selecting among them using the UCB strategy. The UCB mechanism
    balances exploration and exploitation, favoring operators that have historically
    produced better trajectories while still occasionally trying less-used ones.

    A callback is automatically registered to update the UCB values after each
    improvement, ensuring the adaptive selection remains responsive to observed performance.
    """
    
    def __init__(
        self,
        trajectories: List[TrajectoryFactory],
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None
    ):
        multiple_factory = AdaptativeUCBFactory(trajectories, seed)
        new_callbacks = []
        cb = AdaptativeUCBFactoryUpdate(multiple_factory)
        if callbacks:
            new_callbacks.extend(callbacks)
            new_callbacks.append(cb)
        else:
            new_callbacks.append(cb)
        super().__init__(trajectory_factory=multiple_factory, acceptance=acceptance, seed=seed, stopping=stopping, callbacks=new_callbacks)

from opt_flow.trajectory.composite._base import BaseCompositeTrajectory
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping, NoStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.callback.factories import MultipleTrajectoryFactoryResetImprove
from opt_flow.metaheuristic.factories.trajectory import MultipleTrajectoryFactory
class VND(BaseCompositeTrajectory):
    
    def __init__(
        self,
        trajectories: List[TrajectoryFactory],
        acceptance: Optional[BaseAcceptance] = None,
        seed: int = 0,
        stopping: BaseStopping = NoStopping(),
        callbacks: Optional[List[Callback]] = None
    ):
        multiple_factory = MultipleTrajectoryFactory(trajectories) 
        callback = MultipleTrajectoryFactoryResetImprove(multiple_factory)
        new_callbacks = []
        if callbacks:
            new_callbacks.extend(callbacks)
            new_callbacks.append(callback)
        else:
            new_callbacks = [callback]
        super().__init__(multiple_factory, acceptance, seed, stopping, new_callbacks)
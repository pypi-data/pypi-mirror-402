from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.trajectory.algorithm.base_ils import BaseILS
from opt_flow.metaheuristic.factories import MultipleTrajectoryFactory, SimpleTrajectoryFactory
from opt_flow.trajectory import BaseTrajectory
from opt_flow.callback.factories import MultipleTrajectoryFactoryReset

class VNS(BaseILS):
    """
    Variable Neighborhood Search (VNS) algorithm implementation.

    This class implements a VNS metaheuristic by alternating among multiple
    perturbation operators to explore different neighborhoods and applying
    a trajectory operator to refine candidate solutions. It extends
    BaseILS and uses factories to manage perturbations and trajectories.

    """

    def __init__(
        self,
        perturbations: List[BaseTrajectory],
        trajectory: TrajectoryFactory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        perturbation_factory = MultipleTrajectoryFactory(perturbations)
        callback = MultipleTrajectoryFactoryReset(perturbation_factory)
        new_callbacks = []
        if callbacks:
            new_callbacks.extend(callbacks)
            new_callbacks.append(callback)
        else:
            new_callbacks = [callback]
        super().__init__(
            perturbation_factory=perturbation_factory,
            trajectory_factory=SimpleTrajectoryFactory(trajectory),
            acceptance=acceptance,
            seed=seed,
            stopping=stopping,
            callbacks=new_callbacks,
        )

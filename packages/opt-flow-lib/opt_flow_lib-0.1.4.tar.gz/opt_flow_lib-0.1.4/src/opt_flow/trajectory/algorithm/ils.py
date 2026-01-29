from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.trajectory import BaseTrajectory
from opt_flow.trajectory.algorithm.base_ils import BaseILS
from opt_flow.metaheuristic.factories import SimpleTrajectoryFactory


class ILS(BaseILS):
    """
    Iterated Local Search (ILS) algorithm implementation.

    This class provides a ready-to-use ILS metaheuristic by wrapping
    a perturbation and a local trajectory operator. It extends BaseILS 
    by using SimpleTrajectoryFactory to automatically create factories 
    from the provided perturbation and trajectory operators.
    """

    def __init__(
        self,
        perturbation: BaseTrajectory,
        improvement: BaseTrajectory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        super().__init__(
            perturbation_factory=SimpleTrajectoryFactory(perturbation),
            improvement_factory=SimpleTrajectoryFactory(improvement),
            acceptance=acceptance,
            seed=seed,
            stopping=stopping,
            callbacks=callbacks,
        )

from opt_flow.structure import BaseIndividual
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic.trajectory_metaheuristic import TrajectoryMetaheuristic
from opt_flow.metaheuristic.factories import TrajectoryFactory
from opt_flow.config import config

class BaseILS(TrajectoryMetaheuristic):
    """
    Base class for Iterated Local Search (ILS) algorithms.

    This class implements the general structure of an ILS algorithm, 
    combining perturbation and local trajectory operators with an 
    acceptance criterion. Users should provide factories for the 
    perturbation and trajectory operators.
    """
    
    def __init__(
        self,
        perturbation_factory: TrajectoryFactory,
        trajectory_factory: TrajectoryFactory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
        **kwargs,
    ):
        super().__init__(stopping=stopping, callbacks=callbacks, seed=seed, default_acceptance=acceptance, **kwargs)
        self._perturbation_factory = perturbation_factory
        self._trajectory_factory = trajectory_factory
        self._acceptance = acceptance or config.default_acceptance
        
    def iterate(self, individual: BaseIndividual):
        """
        Executes the Iterated Local Search to improve the given individual.

        The algorithm repeatedly applies a perturbation followed by 
        a local improvement. Each candidate individual is evaluated against 
        the acceptance criterion. The process continues until the stopping 
        criterion is met.

        Parameters
        ----------
        individual : BaseIndividual
            The individual to be improved. This individual is modified in place.

        Returns
        -------
        None
        """
        from opt_flow.metaheuristic import Algorithm, AlgorithmType
        acceptance = Algorithm(self._acceptance, "acceptance", AlgorithmType.acceptance)
        self.add_algorithm(acceptance)
        last_trajectory = None
        while True:
            perturbation = Algorithm(self._perturbation_factory.create(), "perturbation", AlgorithmType.trajectory)
            self.add_algorithm(perturbation)
            if last_trajectory:
                self.connect(last_trajectory, perturbation)
            trajectory = Algorithm(self._trajectory_factory.create(), "trajectory", AlgorithmType.trajectory)
            self.add_algorithm(trajectory)
            self.connect(perturbation, trajectory)
            self.connect(trajectory, acceptance)
            last_trajectory = trajectory
            self._run_iterate(individual)
            if not self.should_continue(trajectory):
                break
            acceptance._reset()
        individual.overwrite_with(acceptance.get_individual())
from opt_flow.structure import BaseIndividual
from opt_flow.acceptance import BaseAcceptance
from typing import Optional, List
from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.stopping import BaseStopping
from opt_flow.callback import Callback
from opt_flow.metaheuristic import AlgorithmType
from opt_flow.metaheuristic.trajectory_metaheuristic import TrajectoryMetaheuristic
from opt_flow.config import config
class BestComposite(TrajectoryMetaheuristic):
    """
    Composite trajectory metaheuristic that applies multiple trajectory operators
    in parallel and always retains the best resulting individual.

    This class wraps multiple `BaseTrajectory` instances and executes them on the
    same individual in each iteration. After executing all trajectories, an acceptance
    criterion is applied to select the best candidate individual. The process repeats
    until the stopping criterion is met.

    Attributes
    ----------
    trajectories : List[BaseTrajectory]
        List of improvement operators to apply in each iteration.
    _acceptance : BaseAcceptance
        Acceptance criterion used to determine the best individual in each iteration.
    """
    
    def __init__(
        self,
        trajectories: List[BaseTrajectory],
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None
    ):
        super().__init__(stopping=stopping, callbacks=callbacks, seed=seed)
        self._acceptance = acceptance or config.default_acceptance
        self.trajectories = trajectories

    
    def iterate(self, individual: BaseIndividual):
        """
        Applies all registered trajectory operators to the individual in parallel and
        retains the best individual according to the acceptance criterion.

        The method repeatedly applies each trajectory in `self.trajectories` to the
        current individual, evaluates all resulting candidates via the acceptance
        criterion, and updates the individual to the best candidate. This process
        continues until the stopping criterion signals termination.

        Parameters
        ----------
        individual : BaseIndividual
            The individual instance to be improved. It will be overwritten with the
            best candidate found in each iteration.
        """
        from opt_flow.metaheuristic.algorithm import Algorithm
        last_acceptance = None
        while True:
            traj_algorithms = []
            for traj in self.trajectories:
                trajectory = Algorithm(traj, "trajectory", AlgorithmType.trajectory)
                self.add_algorithm(trajectory)
                traj_algorithms.append(trajectory)
            if last_acceptance:
                for alg in traj_algorithms:
                    self.connect(last_acceptance, alg)
            acceptance = Algorithm(self._acceptance, "acceptance", AlgorithmType.acceptance)
            self.add_algorithm(acceptance)
            for alg in traj_algorithms:
                self.connect(alg, acceptance)
            last_acceptance = acceptance
            self._run_iterate(individual)
            if not self.should_continue(acceptance):
                break
            individual.overwrite_with(acceptance.get_individual())
from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.population.algorithm.base_multistart import BaseMultistart
from opt_flow.structure import Data
from opt_flow.acceptance import BaseAcceptance
from opt_flow.metaheuristic.factories._base import PopulationFactory
from opt_flow.metaheuristic.factories.algorithm import PopulationTrajectoryAlgFactory
from opt_flow.stopping import BaseStopping
from typing import Optional, List
from opt_flow.callback import Callback

class GRASP(BaseMultistart):
    """
    Greedy Randomized Adaptive Search Procedure (GRASP) metaheuristic implementation.

    This class uses a multistart approach where each iteration constructs an initial
    individual using a constructive heuristic, optionally improves it using a
    trajectory procedure, and selects individuals based on an acceptance criterion.
    
    Attributes:
        data (Data): The data for optimization problem.
        population_factory (PopulationFactory): Factory that generates constructive individuals.
        trajectory (BaseTrajectory): Trajectory operator to enhance individuals.
        acceptance (BaseAcceptance): Acceptance mechanism for selecting individuals.
        seed (int): Random seed for reproducibility.
        stopping (BaseStopping): Stopping criterion for the algorithm.
        callbacks (List[Callback]): Optional list of callback functions invoked during execution.
        parallel (bool): If True, run multiple iterations in parallel.
        max_workers (int): Maximum number of parallel workers.
    """

    def __init__(
        self,
        data: Data,
        population_factory: PopulationFactory,
        trajectory: BaseTrajectory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
        parallel = False,
        max_workers = None
    ):
        alg_factory = PopulationTrajectoryAlgFactory(data, population_factory, trajectory)
        super().__init__(data=data, algorith_factory=alg_factory, seed=seed, acceptance=acceptance, stopping=stopping, parallel=parallel, max_workers=max_workers, callbacks=callbacks)


from opt_flow.population.algorithm.base_multistart import BaseMultistart
from opt_flow.structure import Data
from opt_flow.acceptance import BaseAcceptance
from opt_flow.metaheuristic.factories._base import PopulationFactory
from opt_flow.metaheuristic.factories.algorithm import PopulationAlgFactory
from opt_flow.stopping import BaseStopping
from typing import Optional, List
from opt_flow.callback import Callback

class Multistart(BaseMultistart):
    """
    Multistart metaheuristic.

    This class repeatedly constructs individuals from a given constructive heuristic
    and selects the best individual according to an acceptance criterion.
    It is a specialization of `BaseMultistart` that uses only constructive algorithms.
    
    Attributes:
        data (Data): The data for the optimization problem.
        population_factory (PopulationFactory): Factory to generate initial individuals.
        acceptance (BaseAcceptance): Acceptance mechanism for selecting individuals.
        seed (int): Random seed for reproducibility.
        stopping (BaseStopping): Stopping criterion for the algorithm.
        callbacks (List[Callback]): Optional callbacks invoked during execution.
        parallel (bool): Whether to run multiple iterations in parallel.
        max_workers (int): Maximum number of parallel workers.
    """

    def __init__(
        self,
        data: Data,
        population_factory: PopulationFactory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
        parallel = False,
        max_workers = None
    ):
        alg_factory = PopulationAlgFactory(data, population_factory)
        super().__init__(data=data, algorith_factory=alg_factory, seed=seed, acceptance=acceptance, stopping=stopping, parallel=parallel, max_workers=max_workers, callbacks=callbacks)


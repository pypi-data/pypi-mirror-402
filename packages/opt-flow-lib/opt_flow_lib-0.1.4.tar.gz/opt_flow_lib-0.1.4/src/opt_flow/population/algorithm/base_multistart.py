from opt_flow.structure import Data, BaseIndividual
from opt_flow.acceptance import BaseAcceptance
from opt_flow.metaheuristic import Algorithm, AlgorithmType
from opt_flow.metaheuristic.population_metaheuristic import PopulationMetaheuristic
from opt_flow.metaheuristic.factories._base import AlgorithmFactory
from opt_flow.stopping import BaseStopping
import os
from typing import Optional, List
from opt_flow.callback import Callback

class BaseMultistart(PopulationMetaheuristic):
    
    """
    Base class for multistart metaheuristics, managing multiple algorithm
    instances running sequentially or in parallel to explore a search space.

    Each iteration generates a new set of algorithm instances (a "layer"),
    executes them, and updates the best found individual via an acceptance
    mechanism.

    Attributes:
        data (Data): The optimization data of the problem being solved.
        algorith_factory (AlgorithmFactory): Factory to create algorithm instances.
        seed (int, optional): Seed for reproducibility.
        parallel (bool): Whether to run multiple algorithms in parallel.
        max_workers (int): Maximum number of parallel workers.
        concurrent_layer_count (int): Number of algorithms executed in each layer.
    """

    def __init__(
        self,
        data: Data,
        algorith_factory: AlgorithmFactory,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        stopping: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None
    ):
        super().__init__(data=data, seed=seed, default_acceptance=acceptance, stopping=stopping, callbacks=callbacks)
        self.data = data
        self.seed = seed
        self.algorith_factory = algorith_factory
        self.parallel = parallel
        self.max_workers = max_workers or os.cpu_count()
        self.concurrent_layer_count = self.max_workers if self.parallel else 1


    def create(self) -> BaseIndividual:
        """
        Build a individual using multiple algorithm instances in a multistart fashion.

        Returns:
            BaseIndividual: The best individual found across all algorithm layers.
        """
        alg_factory = self.algorith_factory
        acceptance = Algorithm(self.default_acceptance, 'acceptance', AlgorithmType.acceptance)
        self.add_algorithm(acceptance)
        while True:
            for _ in range(self.concurrent_layer_count):
                self._create_layer(alg_factory, acceptance)
            self.partial_create(parallel=self.parallel, max_workers=self.max_workers)
            if not self.should_continue(acceptance):
                break
            acceptance._reset()
        return acceptance.get_individual()
    
    def _create_layer(self, alg_factory: AlgorithmFactory, acceptance: BaseAcceptance):
        alg = alg_factory.create()
        self.add_algorithm(alg)
        self.connect(alg, acceptance)

                        
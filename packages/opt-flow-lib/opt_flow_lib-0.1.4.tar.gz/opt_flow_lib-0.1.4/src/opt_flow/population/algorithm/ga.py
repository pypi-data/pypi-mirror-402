from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure import Data, BaseIndividual
from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.metaheuristic import Algorithm, AlgorithmType
from opt_flow.metaheuristic.population_metaheuristic import PopulationMetaheuristic
from opt_flow.metaheuristic.factories._base import PopulationFactory, RecombinationFactory
from opt_flow.stopping import BaseStopping
from typing import Optional, List
import os
from opt_flow.callback import Callback

class GeneticAlgorithm(PopulationMetaheuristic):
    """
    A Genetic Algorithm (GA) metaheuristic implementation using the PopulationMetaheuristic
    framework. This GA builds an initial population, applies recombination, and optionally
    mutations to evolve individuals over multiple generations.

    Attributes:
        problem (Data): The optimization problem to solve.
        population_factory (PopulationFactory): Factory to generate initial individuals.
        recombination_factory (RecombinationFactory): Factory to generate recombination operators.
        mutation (BaseTrajectory): Mutation operator applied probabilistically.
        parents_acceptance (BaseAcceptance): Acceptance criterion for parent selection.
        population_size (int): Number of individuals in each generation.
        mutation_rate (float): Probability of applying mutation to offspring.
        parallel (bool): If True, run algorithm layers in parallel.
        max_workers (int): Maximum number of parallel workers.
    """

    def __init__(
        self,
        data: Data,
        population_factory: PopulationFactory,
        recombination_factory: RecombinationFactory,
        mutation: BaseTrajectory,
        parents_acceptance: BaseAcceptance,
        population_size: int,
        mutation_rate: float,
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
        self.population_factory = population_factory
        self.recombination_factory = recombination_factory
        self.parents_acceptance = parents_acceptance
        self.mutation = mutation
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.parallel = parallel
        self.max_workers = max_workers or os.cpu_count()
        
    def create(self) -> BaseIndividual:
        """
        Construct a individual using the Genetic Algorithm process.

        This method builds the initial population using the constructive factory,
        applies recombination between parent individuals, optionally applies mutations,
        and iteratively evolves individuals until the stopping criterion is met.

        Returns:
            BaseIndividual: The best individual found by the GA.
        """
        last_layer: List[Algorithm] = []
        for _ in range(self.population_size):
            alg = Algorithm(self.population_factory.create(self.data), "population", AlgorithmType.population)
            self.add_algorithm(alg)
            last_layer.append(alg)
        final_acceptance = Algorithm(self.default_acceptance, "final acceptance", AlgorithmType.acceptance)
        self.add_algorithm(final_acceptance)
        self.connect_all(final_acceptance)
        self.partial_create()
        final_acceptance._reset()
        while True:
            acceptance = None
            parents = []
            new_layer = []
            for _ in range(self.population_size):
                new_acceptance = Algorithm(self.parents_acceptance, "parents", AlgorithmType.acceptance)
                self.add_algorithm(new_acceptance)
                for alg in last_layer:
                    self.connect(alg, new_acceptance)
                parents.append(new_acceptance)
                if acceptance is not None:
                    self.connect(acceptance, new_acceptance)
                    acceptance = None
                else:
                    acceptance = new_acceptance
                if len(parents) == 2:
                    for _ in range(2):
                        recombination = Algorithm(self.recombination_factory.create(), "recombination", AlgorithmType.recombination)
                        self.add_algorithm(recombination)
                        for parent in parents:
                            self.connect(parent, recombination)
                        if self.rng.random() <= self.mutation_rate:
                            mutation = Algorithm(self.mutation, "mutation", AlgorithmType.trajectory)
                            self.add_algorithm(mutation)
                            self.connect(recombination, mutation)
                            self.connect(mutation, final_acceptance)
                            new_layer.append(mutation)
                        else:
                            self.connect(recombination, final_acceptance)
                            new_layer.append(recombination)
                    parents = []
            self.partial_construct()
            last_layer = new_layer
            if not self.should_continue(final_acceptance):
                break
            final_acceptance._reset()
        self._run_create()
        return final_acceptance.get_individual()

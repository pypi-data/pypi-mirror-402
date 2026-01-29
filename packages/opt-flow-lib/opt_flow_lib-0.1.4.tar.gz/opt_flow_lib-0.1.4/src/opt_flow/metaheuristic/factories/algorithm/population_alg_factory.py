from opt_flow.metaheuristic.factories._base.algorithm_factory import AlgorithmFactory
from opt_flow.metaheuristic.factories._base.population_factory import PopulationFactory
from opt_flow.metaheuristic import Algorithm, AlgorithmType
from opt_flow.structure import Data

class PopulationAlgFactory(AlgorithmFactory):
    """
    Factory for creating Algorithm instances that wrap population algorithms.

    This factory combines a PopulationFactory with a specific optimization
    problem to produce fully configured Algorithm objects of type
    `AlgorithmType.population`.
    """
    
    def __init__(self, data: Data, population_factory: PopulationFactory):
        self.data = data
        self.population_factory = population_factory
        
    def create(self) -> Algorithm:
        """
        Creates and returns a new population Algorithm instance.

        The returned Algorithm wraps a BasePopulation algorithm created by
        the provided PopulationFactory and is labeled as a population
        metaheuristic node.

        Returns:
            Algorithm: A new Algorithm instance of type
            AlgorithmType.population.
        """
        alg = Algorithm(self.population_factory.create(self.data), "population", AlgorithmType.population)
        return alg
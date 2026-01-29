from opt_flow.metaheuristic.factories._base import PopulationFactory
from opt_flow.core import BasePopulation
from opt_flow.structure import Data
from typing import List

class MultiplePopulationFactory(PopulationFactory):
    """
    Factory for testing several BasePopulation algorithms

    This factory is useful for reproducible experiments and population-based
    initialization, where multiple population algorithms are created based on a
    given list.
    """
    
    def __init__(self, pops: List[BasePopulation], **kwargs):
        self.pops = pops
        self.nb_constrs = len(pops)
        self.k = 0

    
    def create(self, data: Data) -> BasePopulation:
        """
        Creates and returns an existing baseConstructive instance of the given list

        Args:
            problem (BaseProblem): The optimization problem for which the
                constructive algorithm is created.

        Returns:
            BaseConstructive: The next selected constructive from the list.
        """
        pop = self.pops[self.k]
        self.k += 1
        self.k %= self.nb_constrs
        return pop
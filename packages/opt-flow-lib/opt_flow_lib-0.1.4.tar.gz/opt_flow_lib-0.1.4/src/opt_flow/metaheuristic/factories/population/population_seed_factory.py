from opt_flow.metaheuristic.factories._base import PopulationFactory
from opt_flow.core import BasePopulation
from opt_flow.structure import Data
from typing import Optional, Type, Dict, Any

class PopulationSeedFactory(PopulationFactory):
    """
    Factory for creating BasePopulation algorithms with incrementing seeds.

    This factory is useful for reproducible experiments and population-based
    initialization, where multiple population algorithms are created with
    different random seeds following a deterministic pattern.
    """
    
    def __init__(self, pop_cls: Type[BasePopulation], extra_args: Optional[Dict[str, Any]] = None, seed: int = 0, step: int = 1):
        self.pop_cls = pop_cls
        self.extra_args = extra_args or {}
        self.seed = seed
        self.step = step
    
    def create(self, data: Data) -> BasePopulation:
        """
        Creates and returns a new BasePopulation instance with a unique seed.

        After creation, the internal seed is incremented by the configured step.

        Args:
            data (BaseData): The optimization fata for which the
                population algorithm is created.

        Returns:
            BasePopulation: A newly created population algorithm instance
            with the assigned seed.
        """
        constr =  self.pop_cls(data, self.seed, **self.extra_args)
        self.seed += self.step
        return constr
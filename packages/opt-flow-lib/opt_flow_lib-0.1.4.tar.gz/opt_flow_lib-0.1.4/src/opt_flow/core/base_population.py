from opt_flow.structure import Data
from opt_flow.structure.base_individual import BaseIndividual
from opt_flow.utils import RandomClass
from abc import abstractmethod
from opt_flow.utils import NamedOperator
from typing import Optional

class BasePopulation(NamedOperator, RandomClass):
    """
    Abstract base class for constructive operators in an optimization problem.

    This class defines the interface for operators that generate initial
    individuals for a given data. It combines random number generation
    capabilities with a nameable operator interface.

    Subclasses must implement the `create` method to provide a
    problem-specific generators of individuals.
    """
    
    def __init__(self, data: Data, seed: Optional[int]=None, *args, **kwargs):
        """
        Initialize a BaseConstructive operator.

        Args:
            data (Data): The optimization data for which
                individual will be created.
            seed (int, optional): Random seed for reproducibility. Defaults to None.
            *args: Additional arguments passed to parent classes.
            **kwargs: Additional keyword arguments passed to parent classes.
        """
        super().__init__(seed=seed, *args, **kwargs)
        self.data = data
        
        
    @abstractmethod
    def create(self) -> BaseIndividual:
        """
        Create a new individual for the associated data.

        Returns:
            BaseIndividual: The generated individual.
        """
        pass
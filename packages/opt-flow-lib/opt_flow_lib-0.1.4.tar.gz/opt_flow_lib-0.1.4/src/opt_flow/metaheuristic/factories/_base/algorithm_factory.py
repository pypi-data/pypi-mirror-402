from opt_flow.metaheuristic.factories._base.base_factory import BaseFactory
from typing import TYPE_CHECKING
if TYPE_CHECKING:   
    from opt_flow.metaheuristic.algorithm import Algorithm
from opt_flow.metaheuristic.algorithm_type import AlgorithmType
from abc import abstractmethod

class AlgorithmFactory(BaseFactory):
    
    """
    Abstract factory class for creating Algorithm instances.

    This class enforces a standard interface for generating different types
    of algorithms (constructive, improvement, recombination, acceptance).

    Attributes:
        alg_type (AlgorithmType): Type of algorithm this factory creates.
    """
    
    def __init__(self, alg_type: AlgorithmType, **kwargs):
        self.alg_type = alg_type
        
    @abstractmethod
    def create(self, **kwargs) -> "Algorithm":
        """
        Creates and returns a new Algorithm instance.

        This method must be implemented by all concrete subclasses.

        Args:
            **kwargs: Keyword arguments for configuring the Algorithm instance.

        Returns:
            Algorithm: A newly created algorithm object.
        """
        pass


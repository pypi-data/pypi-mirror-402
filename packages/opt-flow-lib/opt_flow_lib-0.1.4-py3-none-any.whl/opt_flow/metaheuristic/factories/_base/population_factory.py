from opt_flow.metaheuristic.factories._base.base_factory import BaseFactory
from opt_flow.structure import Data
from abc import abstractmethod
from opt_flow.core import BasePopulation  


class PopulationFactory(BaseFactory):
    
    """
    Abstract factory class for creating BasePopulation algorithm instances.

    This factory standardizes the creation of population algorithms
    that generate individuals for a given optimization data.
    """
    @abstractmethod
    def create(self, data: Data, **kwargs) -> BasePopulation:
        """
        Creates and returns a new BasePopulation algorithm instance for a given data.

        Args:
            data (Data): The optimization data for which the algorithm is created.
            **kwargs: Additional keyword arguments used to configure the algorithm instance.

        Returns:
            BasePopulation: A newly created constructive algorithm instance.
        """
        pass



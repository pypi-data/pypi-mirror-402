from opt_flow.metaheuristic.factories._base.base_factory import BaseFactory
from abc import abstractmethod
from opt_flow.recombination import BaseRecombination

class RecombinationFactory(BaseFactory):
    """
    Abstract factory class for creating BaseRecombination algorithm instances.

    This factory standardizes the creation of recombination algorithms that
    combine multiple solutions to generate new candidate solutions.
    """
    @abstractmethod
    def create(self, **kwargs) -> BaseRecombination:
        """
        Creates and returns a new BaseRecombination algorithm instance.

        Args:
            **kwargs: Arbitrary keyword arguments used to configure the
                recombination algorithm instance.

        Returns:
            BaseRecombination: A newly created recombination algorithm instance.
        """
        pass



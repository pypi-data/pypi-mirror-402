from opt_flow.structure import BaseIndividual
from abc import abstractmethod
from opt_flow.utils import NamedOperator

class BaseRecombination(NamedOperator):
    
    """
    Abstract base class for recombination operators.

    A recombination operator defines a method to combine two existing individuals
    into a single new individual. This is useful in contexts where multiple 
    individuals are available and combining them can potentially produce 
    improved outcomes.

    Methods
    -------
    recombine(sol1: BaseIndividual, sol2: BaseIndividual) -> BaseIndividual
        Abstract method to combine two individuals into a single new individual.
    """
    
    @abstractmethod
    def recombine(self, sol1: BaseIndividual, sol2: BaseIndividual) -> BaseIndividual:
        """
        Combine two individuals to produce a new individual.

        Parameters
        ----------
        sol1 : BaseIndividual
            The first individual to combine.
        sol2 : BaseIndividual
            The second individual to combine.

        Returns
        -------
        BaseIndividual
            A new individual created by combining elements of the input individuals.

        Notes
        -----
        Subclasses must implement this method to define a specific recombination
        strategy.
        """
        pass
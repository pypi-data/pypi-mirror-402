from abc import abstractmethod
from opt_flow.structure import BaseIndividual
from opt_flow.movement import Movement
from typing import Type, List
from opt_flow.utils import NamedOperator

class FirstMovementSelector(NamedOperator):
    
    """
    Abstract base class for selecting the first movement in a local search chain.

    Subclasses implement a strategy to choose which movement to apply first
    given a individual and a set of available movements.
    """
    
    @abstractmethod
    def select_first(self, individual: BaseIndividual, movements: List[Type[Movement]]) -> Type[Movement]:
        """
        Select the first movement to apply from the given list of movements.

        Args:
            individual (BaseIndividual): The current individual to improve.
            movements (List[Type[Movement]]): List of movement classes available for selection.

        Returns:
            Type[Movement]: The movement class chosen to start the chain.
        """
        pass
from abc import abstractmethod
from opt_flow.movement import Movement
from typing import Type, List
from opt_flow.utils import NamedOperator

class NextMovementSelector(NamedOperator):
    """
    Abstract base class for selecting the next movement in a local search chain.

    Subclasses implement a strategy to choose the next movement given the
    current movement and a list of available movements.
    """
    
    @abstractmethod
    def select_next(self, current: Type[Movement], movements: List[Type[Movement]]) -> Type[Movement]:
        """
        Select the next movement to apply in the chain.

        Args:
            current (Type[Movement]): The movement class currently being applied.
            movements (List[Type[Movement]]): List of movement classes available for selection.

        Returns:
            Type[Movement]: The movement class chosen to follow the current movement.
        """
        pass
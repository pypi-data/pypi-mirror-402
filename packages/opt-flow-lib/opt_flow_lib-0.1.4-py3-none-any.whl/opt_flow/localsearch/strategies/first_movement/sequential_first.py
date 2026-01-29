from opt_flow.structure import BaseIndividual
from opt_flow.movement import Movement
from typing import Type, List
from opt_flow.localsearch.interfaces import FirstMovementSelector

class SequentialFirst(FirstMovementSelector):
    """
    Selects the first movement in the provided movement list.
    """
    def select_first(self, individual: BaseIndividual, movements: List[Type[Movement]]) -> Type[Movement]:
        """
        Return the first movement in the list.

        Args:
            individual (BaseIndividual): Current individual (unused).
            movements (List[Type[Movement]]): Available movement classes.

        Returns:
            Type[Movement]: The first movement in the list.
        """
        return movements[0]
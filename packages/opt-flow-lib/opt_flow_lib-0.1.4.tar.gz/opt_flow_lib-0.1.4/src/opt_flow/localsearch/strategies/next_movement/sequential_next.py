from opt_flow.movement import Movement
from typing import Type, List
from opt_flow.localsearch.interfaces import NextMovementSelector

class SequentialNext(NextMovementSelector):
    """
    Sequentially selects the next movement in a circular order.

    Given a list of movement classes, this selector chooses the movement
    immediately after the current one. If the current movement is the
    last in the list, it wraps around to the first movement.
    """
    def select_next(self, current: Type[Movement], movements: List[Type[Movement]]) -> Type[Movement]:
        """
        Select the next movement class in sequence.

        Args:
            current (Type[Movement]): Current movement class.
            movements (List[Type[Movement]]): Ordered list of movement classes.

        Returns:
            Type[Movement]: The next movement class in the circular sequence.
        """
        index = movements.index(current)
        return movements[(index + 1) % len(movements)]
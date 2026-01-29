from opt_flow.localsearch.interfaces import MemoryStrategy
from opt_flow.structure import BaseIndividual
from opt_flow.structure._base import BaseObjective
from opt_flow.movement import ArgsT

class NoMemory(MemoryStrategy):
    """
    Trivial memory strategy that never marks moves as tabu.

    This strategy disables memory-based restrictions entirely:
    all candidate moves are always allowed, and no state is
    recorded after accepting a move.

    It is suitable for basic local search algorithms where
    tabu or historical information is not required.
    """

    def is_tabu(self, move_arg: ArgsT, objective: BaseObjective) -> bool:
        """
        Determine whether a move is forbidden.

        Args:
            move_arg (ArgsT): Argument representing the move.
            objective (BaseObjective): Objective value associated
                with the move.

        Returns:
            bool: Always False, since no moves are considered tabu.
        """
        return False

    def _on_accept(self, move_arg: ArgsT, individual: BaseIndividual):
        """
        Hook executed when a move is accepted.

        Args:
            move_arg (ArgsT): Accepted move argument.
            individual (BaseIndividual): individual after the move.

        Notes:
            This method performs no action, as no memory
            is maintained.
        """
        pass
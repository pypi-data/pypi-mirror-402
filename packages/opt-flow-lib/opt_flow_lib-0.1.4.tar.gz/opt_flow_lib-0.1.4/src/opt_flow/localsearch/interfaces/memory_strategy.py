from abc import abstractmethod
from opt_flow.structure import BaseIndividual
from opt_flow.structure._base import BaseObjective
from opt_flow.movement import ArgsT
from opt_flow.utils import NamedOperator

class MemoryStrategy(NamedOperator):
    """
    Abstract base class for memory strategies in local search.

    Memory strategies track moves and optionally forbid certain moves (tabu) 
    based on past history, individual, or objective values.
    """
    
    @abstractmethod
    def is_tabu(self, move_arg: ArgsT, objective: BaseObjective) -> bool:
        """
        Determine whether a candidate move is considered tabu.

        Args:
            move_arg (ArgsT): Arguments for the candidate movement.
            objective (BaseObjective): Objective associated with the move.

        Returns:
            bool: True if the move is forbidden (tabu), False otherwise.
        """
        pass

    @abstractmethod
    def _on_accept(self, move_arg: ArgsT, individual: BaseIndividual):
        """
        Update memory after a move is accepted.

        Args:
            move_arg (ArgsT): Arguments of the accepted move.
            individual (BaseIndividual): individual resulting from the accepted move.
        """
        pass
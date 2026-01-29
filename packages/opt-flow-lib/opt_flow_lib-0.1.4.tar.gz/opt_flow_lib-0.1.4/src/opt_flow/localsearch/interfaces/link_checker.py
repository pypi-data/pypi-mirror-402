from opt_flow.movement import ArgsT
from opt_flow.structure import BaseIndividual
from opt_flow.utils import NamedOperator
from abc import abstractmethod


class LinkChecker(NamedOperator):
    
    """
    Abstract base class for validating links between consecutive moves in a local search chain.

    Subclasses implement a strategy to determine whether a candidate move can follow
    a previous move, based on their arguments and resulting individuals.
    """
    
    @abstractmethod
    def check(self, prev_arg: ArgsT, prev_individual: BaseIndividual, next_arg: ArgsT, individual: BaseIndividual) -> bool:
        """
        Check whether the next move can validly follow the previous move.

        Args:
            prev_arg (ArgsT): Arguments used by the previous movement.
            prev_individual (BaseIndividual): individual resulting from the previous movement.
            next_arg (ArgsT): Arguments proposed for the next movement.
            individual (BaseIndividual): Current individual before applying the next movement.

        Returns:
            bool: True if the next movement is allowed to follow the previous one; False otherwise.
        """
        pass
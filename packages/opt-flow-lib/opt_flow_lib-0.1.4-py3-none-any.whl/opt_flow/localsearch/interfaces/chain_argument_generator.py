from typing import Iterator, Optional, Type
from opt_flow.movement import Movement
from opt_flow.structure import BaseIndividual
from opt_flow.movement import SearchSpace
from opt_flow.movement import ArgsT
from abc import abstractmethod
from opt_flow.utils import RandomClass
from opt_flow.utils import NamedOperator

class ChainArgumentGenerator(NamedOperator, RandomClass):
    """
    Abstract base class for generating arguments for moves in a chain of local search operations.

    This class defines the interface for generating the sequence of arguments that
    should be tested for the next move in an ejection chain or other multi-step local search.

    """
    
    @abstractmethod
    def generate(
        self,
        prev_movement: Optional[Movement],
        prev_movement_cls: Optional[Type[Movement]],
        prev_arg: Optional[ArgsT],
        individual: BaseIndividual,
        level: int,
        next_space_cls: Type[SearchSpace],
        last_individual: Optional[BaseIndividual],
        *args, 
        **kwargs, 
    ) -> Iterator[ArgsT]:
        """
        Generate allowed arguments for the next movement in the chain.

        This method should yield candidate arguments for the next move, 
        taking into account the previous movement, its argument, the current individual,
        and the level in the chain.

        Args:
            prev_movement (Optional[Movement]): The previous movement instance in the chain, if any.
            prev_movement_cls (Optional[Type[Movement]]): Class of the previous movement.
            prev_arg (Optional[ArgsT]): Argument used by the previous movement.
            individual (BaseIndividual): Current individual from which the chain proceeds.
            level (int): Depth in the movement chain.
            next_space_cls (Type[SearchSpace]): The search space class for the next movement.
            last_individual (Optional[BaseIndividual]): individual associated with the last move in the chain.
            *args: Additional arguments, to be defined by subclasses.
            **kwargs: Additional keyword arguments, to be defined by subclasses.

        Yields:
            Iterator[ArgsT]: Candidate arguments for the next movement.
        """
        pass
from abc import abstractmethod
from typing import Optional, Iterable, Type
from opt_flow.movement.args import ArgsT
from opt_flow.structure import BaseIndividual
from opt_flow.utils import RandomClass
from opt_flow.movement.movement import Movement
from opt_flow.utils import NamedOperator

class SearchSpace(RandomClass, NamedOperator):
    
    """
    Base class representing a search space for local search movements.

    A SearchSpace defines the set of candidate moves (arguments) that can be applied
    to a given individual using a specific Movement. It acts as an iterator over
    all possible movement arguments for exploration.

    Attributes:
        associated_movement (Type[Movement]): The movement class associated with this search space.
        individual (BaseIndividual): The individual instance over which this search space operates.
    """
    
    associated_movement: Type[Movement]

    def __init__(self, individual: BaseIndividual, *, seed: Optional[int]=None, **kwargs):
        self.individual = individual
        super().__init__(seed=seed, **kwargs)
    
    @abstractmethod
    def __iter__(self) -> Iterable[ArgsT]:
        """
        Return an iterator over candidate movement arguments for this search space.

        Each element yielded by the iterator represents a possible set of parameters
        that can be passed to the associated Movement's execute, simulate, or undo methods.

        Returns:
            Iterable[ArgsT]: An iterable of movement arguments for this search space.
        """
        ...
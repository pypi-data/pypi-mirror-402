from abc import abstractmethod
from opt_flow.movement.args import ArgsT
from opt_flow.structure import BaseIndividual
from opt_flow.structure._base import BaseObjective
from opt_flow.utils import NamedOperator

class Movement(NamedOperator):
    """
    Base class for all Movements in local search algorithms.

    A Movement represents a specific modification or operation that can be applied
    to an individual in a search space. Movements are used by local search procedures
    to explore neighboring individuals.

    This class defines a standard interface that all concrete movement types must
    implement. Movements can be executed directly, simulated, or undone depending
    on the chosen MovementType.

    Attributes:
        individual (BaseIndividual): The individual instance this movement operates on.
    """
    
    def __init__(self, individual: BaseIndividual, *args, **kwargs):
        self.individual = individual
        super().__init__(*args, **kwargs)
        
    @abstractmethod
    def execute(self, args: ArgsT):
        """
        Apply the movement to the individual.

        Subclasses must implement this method to modify the individual according
        to the movement logic.

        Args:
            args (ArgsT): The parameters or arguments required to perform the movement.
        """
        ...

    def simulate(self, args: ArgsT) -> BaseObjective:
        """
        Evaluate the effect of this movement without modifying the individual.

        Subclasses may override this method to provide a fast evaluation of the
        candidate individual after applying this movement. By default, this is
        a placeholder and returns None.

        Args:
            args (ArgsT): The parameters or arguments required to perform the movement.

        Returns:
            BaseObjective: The objective value of the candidate individual if simulated.
        """
        ...

    def undo(self, args: ArgsT):
        """
        Revert the movement applied to the individual.

        Subclasses may override this method to revert the effects of execute().
        This is used with MovementType.DO_UNDO to explore a individual and then
        backtrack if needed.

        Args:
            args (ArgsT): The parameters or arguments used for the movement to undo.
        """
        ...
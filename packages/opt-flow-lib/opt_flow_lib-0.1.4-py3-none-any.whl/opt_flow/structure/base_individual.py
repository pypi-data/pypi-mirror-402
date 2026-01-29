from abc import abstractmethod
from opt_flow.structure._base import BaseObjective

class BaseIndividual:
    """
    Abstract representation of a individual in an optimization problem.

    This class defines the interface that all concrete individual
    implementations must follow. A individual represents a candidate
    assignment of values to the problem's variables and can be
    evaluated, copied, or compared with other individual.
    """

    @abstractmethod
    def copy(self) -> "BaseIndividual":
        """
        Create and return a deep copy of this individual.

        Returns
        -------
        BaseIndividual
            A new instance of the individual with identical data.
        """
        pass

    @abstractmethod
    def get_objective(self) -> BaseObjective:
        """
        Evaluate and return the objective associated with this individual.

        Returns
        -------
        BaseObjective
            The objective value(s) for this individual.
        """
        pass

    @abstractmethod
    def overwrite_with(self, other: "BaseIndividual"):
        """
        Replace the contents of this individual with another individual's data.

        Parameters
        ----------
        other : BaseIndividual
            The individual whose data will overwrite the current individual.
        """
        pass

    @abstractmethod
    def __eq__(self, other: "BaseIndividual") -> bool:
        """
        Check if this individual is equal to another individual.

        Parameters
        ----------
        other : BaseIndividual
            The individual to compare with.

        Returns
        -------
        bool
            True if the individuals are considered equal, False otherwise.
        """
        pass

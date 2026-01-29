from opt_flow.structure import BaseIndividual
from abc import abstractmethod
from opt_flow.utils import NamedOperator

class ScoreFilter(NamedOperator):
    """
    Abstract base class for filtering individuals based on score-related criteria.

    Score filters are typically used to decide whether a individual is eligible
    for further processing, evaluation, or acceptance based on derived metrics
    rather than direct objective comparisons.
    """
    
    @abstractmethod
    def is_allowed(self, individual: BaseIndividual) -> bool:
        """
        Determine whether the given individual passes the filter.

        Args:
            individual (BaseIndividual): individual instance to be evaluated.

        Returns:
            bool: ``True`` if the individual is allowed to proceed, ``False`` otherwise.
        """
        pass 
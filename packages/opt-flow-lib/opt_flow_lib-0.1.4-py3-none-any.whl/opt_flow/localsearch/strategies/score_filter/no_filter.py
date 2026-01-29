from opt_flow.structure import BaseIndividual
from typing import Any
from opt_flow.localsearch.interfaces import ScoreFilter

class NoFilter(ScoreFilter):
    """
    A score filter that allows all individuals.

    This filter does not impose any restriction on individuals based on their
    score. It is effectively a no-op filter.
    """
    
    def is_allowed(self, score: Any, individual: BaseIndividual) -> bool:
        """
        Determine whether a individual is allowed.

        Args:
            score (Any): The score of the individual.
            individual (BaseIndividual): The individual being evaluated.

        Returns:
            bool: Always returns True, allowing all individuals.
        """
        return True
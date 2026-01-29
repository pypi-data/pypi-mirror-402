from opt_flow.acceptance._base import BaseAcceptance
from typing import List
from opt_flow.acceptance.scalar_acceptance import ScalarAcceptance
from opt_flow.structure import MultiObjective


class LexicographicAcceptance(BaseAcceptance):
    """
    Lexicographic acceptance strategy for multi-objective comparisons.

    Objectives are compared sequentially using a corresponding list of
    scalar acceptance strategies. The candidate is accepted as soon as it
    is accepted by the first objective where the two differ.
    """

    def __init__(self, acceptances: List[ScalarAcceptance]):
        """
        Initialize the lexicographic acceptance strategy.

        Args:
            acceptances (List[ScalarAcceptance]): Ordered list of scalar
                acceptance strategies, one per objective dimension.
        """
        self._acceptances = acceptances
        self._nb_acceptances = len(acceptances)
        


    def compare(
        self, a: MultiObjective, b: MultiObjective
    ) -> bool:
        """
        Compare two multi-objective values lexicographically.

        The objectives are compared in order using the corresponding
        scalar acceptance strategies. The candidate is accepted as soon
        as it is accepted for a given objective. If no objective accepts
        the candidate, it is rejected.

        If the number of objectives does not match the number of
        acceptance strategies, the candidate is rejected.

        Args:
            a (MultiObjective): Reference objective.
            b (MultiObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted
            over the reference objective ``a``.
        """
        acceptances = self._acceptances
        for obj1, obj2, acceptance in zip(a, b, acceptances):
            # First, check if objectives are different
            if acceptance.compare(obj1, obj2):
                # Candidate is better for this objective
                return True
        return False


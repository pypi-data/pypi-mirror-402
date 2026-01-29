from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure import MultiObjective
from opt_flow.utils import RandomClass

class RandomAcceptance(RandomClass, BaseAcceptance):
    """
    Random acceptance strategy for multi-objective comparisons.

    The candidate is accepted probabilistically, independent of objective
    values. The decision is based solely on a random number generator.
    """

    def compare(
        self, a: MultiObjective, b: MultiObjective
    ) -> bool:
        """
        Compare two multi-objective values randomly.

        Args:
            a (MultiObjective): Reference objective.
            b (MultiObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted
            over the reference objective ``a`` (randomly, with 50% chance).
        """
        return self.rng.random() < 0.5

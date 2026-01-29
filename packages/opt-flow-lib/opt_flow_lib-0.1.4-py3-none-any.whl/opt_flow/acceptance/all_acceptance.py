from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure import MultiObjective


class AllAcceptance(BaseAcceptance):
    """
    Acceptance strategy that unconditionally accepts the candidate.
    """


    def compare(
        self, a: MultiObjective, b: MultiObjective
    ) -> bool:
        """
        Accept the candidate objective regardless of its value.

        Args:
            a (MultiObjective): Reference objective.
            b (MultiObjective): Candidate objective.

        Returns:
            bool: Always ``True``, indicating that the candidate objective
            ``b`` is accepted over the reference objective ``a``.
        """
        return True

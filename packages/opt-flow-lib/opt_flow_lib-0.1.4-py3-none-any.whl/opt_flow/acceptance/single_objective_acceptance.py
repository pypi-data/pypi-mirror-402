from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure import MultiObjective


class SingleObjectiveAcceptance(BaseAcceptance):
    """
    Single-objective acceptance strategy that focuses on a specific objective index.
    
    This class extracts a single objective from multi-objective individuals and applies
    a scalar acceptance strategy to that specific objective only.
    """

    def __init__(self, i: int, acceptance: BaseAcceptance):
        """
        Initialize the single-objective acceptance strategy.

        Args:
            i (int): Index of the objective to focus on (0-based index).
            acceptance (BaseAcceptance): Scalar acceptance strategy to apply
                to the selected objective.
        """
        self.i = i
        self.acceptance = acceptance


    def compare(
        self, a: MultiObjective, b: MultiObjective
    ) -> bool:
        """
        Compare two multi-objective based on a single objective.
        
        Extracts the i-th objective from both objectives and applies the scalar
        acceptance strategy to compare only those values.

        Args:
            a (MultiObjective): Reference multi-objective.
            b (MultiObjective): Candidate multi-objective.

        Returns:
            bool: True if the candidate's i-th objective ``b[i]`` is accepted
            over the reference's i-th objective ``a[i]`` according to the
            scalar acceptance strategy.
            
        Raises:
            IndexError: If the index i is out of bounds for either individual.
        """
        i = self.i
        return self.acceptance.compare(a[i], b[i])

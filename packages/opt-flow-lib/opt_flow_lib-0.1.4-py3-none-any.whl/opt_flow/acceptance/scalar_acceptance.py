from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure.scalar_objective import ScalarObjective
from opt_flow.structure.objective_direction import ObjectiveDirection
from typing import Optional
from math import isclose

class ScalarAcceptance(BaseAcceptance):
    
    """
    Base class for acceptance strategies operating on scalar objectives.

    This class provides:
    - Tolerance-based numeric comparison helpers (:meth:`_is_close`).
    - An abstract :meth:`compare` method to be implemented by subclasses.

    Args:
        tol (float): Absolute tolerance for numeric comparisons.
        rtol (float): Relative tolerance for numeric comparisons.
        *args, **kwargs: Passed to the parent :class:`BaseAcceptance`.
    """


    
    __slots__ = ("tol", "rtol", "direction")
    def __init__(self, direction: ObjectiveDirection, tol=1e-4, rtol=1e-8, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tol = tol
        self.rtol = rtol
        self.direction = direction
        
    def compare(
        self, a: Optional[ScalarObjective], b: Optional[ScalarObjective]
    ) -> bool:
        """
        Compare two scalar objectives and decide whether the candidate is accepted.

        Subclasses should implement the numeric or rule-based logic for
        acceptance. Automatic checks for None and mismatched metadata
        are applied by the class decorator.

        Args:
            a (Optional[ScalarObjective]): Reference objective.
            b (Optional[ScalarObjective]): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted over
            the reference objective ``a``.
        """
        raise NotImplementedError
    

    def _is_close(self, a: float, b: float) -> bool:
        """
        Check whether two scalar values are close within tolerances.

        Args:
            a (float): First value.
            b (float): Second value.

        Returns:
            bool: ``True`` if the absolute difference is within
            `tol + rtol * abs(b)`.
        """
        return isclose(a, b, rel_tol=self.rtol, abs_tol=self.tol)
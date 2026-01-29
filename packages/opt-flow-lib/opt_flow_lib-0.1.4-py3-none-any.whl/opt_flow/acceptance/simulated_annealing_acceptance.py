from math import exp
from opt_flow.structure import ScalarObjective
from opt_flow.structure import ObjectiveDirection
from opt_flow.acceptance.scalar_acceptance import ScalarAcceptance
from opt_flow.utils import RandomClass
from typing import Optional


class SimulatedAnnealingAcceptance(ScalarAcceptance, RandomClass):
    """
    Simulated annealing acceptance strategy for scalar objectives.

    The candidate is accepted probabilistically depending on the
    improvement over the reference and the current temperature. Small
    improvements may be accepted with a probability that decreases as the
    temperature cools.
    """
    def __init__(
        self,
        initial_temperature: float,
        cooling_rate: float,
        min_temperature: float,
        *args,
        seed: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a SimulatedAnnealingAcceptance instance.

        Args:
            initial_temperature (float): Starting temperature for the annealing process.
            cooling_rate (float): Factor by which temperature is multiplied after each step.
            min_temperature (float): Minimum temperature allowed.
            seed (int, optional): Random seed for reproducibility.
        """
        super().__init__(*args, **kwargs, seed=seed)
        self.temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        if self.direction == ObjectiveDirection.MAXIMIZE:
            self.compare = self.compare_maximize
        else:
            self.compare = self.compare_minimize

    def compare_maximize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        """
        Compare two scalar objectives using simulated annealing logic.

        The difference between candidate and reference values is computed
        according to the objective direction. If the candidate improves
        upon the reference, it is accepted. Otherwise, it may still be
        accepted with a probability proportional to exp(-delta / temperature).

        Args:
            a (ScalarObjective): Reference objective.
            b (ScalarObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted
            over the reference objective ``a``.
        """
        delta =  a.value - b.value

        if self._is_close(delta, 0):
            return False

        if delta < 0:
            return True
        temp = self.temperature
        acceptance_probability = (
            exp(-delta / temp) if temp > 0 else 0
        )
        return self.rng.random() < acceptance_probability

    def compare_minimize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        """
        Compare two scalar objectives using simulated annealing logic.

        The difference between candidate and reference values is computed
        according to the objective direction. If the candidate improves
        upon the reference, it is accepted. Otherwise, it may still be
        accepted with a probability proportional to exp(-delta / temperature).

        Args:
            a (ScalarObjective): Reference objective.
            b (ScalarObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted
            over the reference objective ``a``.
        """
        delta = - a.value + b.value

        if self._is_close(delta, 0):
            return False

        if delta < 0:
            return True
        temp = self.temperature
        acceptance_probability = (
            exp(-delta / temp) if temp > 0 else 0
        )
        return self.rng.random() < acceptance_probability
from opt_flow.structure import BaseIndividual
from opt_flow.structure import ScalarObjective
from opt_flow.structure import ObjectiveDirection
from opt_flow.acceptance.scalar_acceptance import ScalarAcceptance
from opt_flow.localsearch.interfaces import ScoreCalculator
from logging import warning

class ScoreAcceptance(ScalarAcceptance):
    """
    Acceptance strategy based on a numeric score computed for scalar objectives.

    The candidate objective or individual is accepted if its score improves
    upon the reference, according to the specified objective direction.
    """
    def __init__(
        self,
        score_calculator: ScoreCalculator,
        *args, 
        **kwargs,
    ):
        """
        Initialize a ScoreAcceptance instance.

        Args:
            score_calculator (ScoreCalculator): Object that calculates a numeric
                score for a given objective or individual.
            direction (ObjectiveDirection): Indicates whether higher or lower
                scores are better (MAXIMIZE or MINIMIZE).
        """
        super().__init__(*args, **kwargs)
        self.score_calculator = score_calculator
        self.calc_score = score_calculator.calculate_score
        warning("In case of using movement type SIMULATE, the score must be calculated just with respect to the objective function.")
        if self.direction == ObjectiveDirection.MAXIMIZE:
            self.compare = self.compare_maximize
            self.compare_individuals = self.compare_individuals_maximize
        else:
            self.compare = self.compare_minimize
            self.compare_individuals = self.compare_individuals_minimize

    def compare_maximize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        """
        Compare two scalar objectives using their computed scores.

        Args:
            a (ScalarObjective): Reference objective.
            b (ScalarObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` has a better score
            than the reference objective ``a`` according to the objective
            direction.
        """
        calc_score = self.calc_score
        first_score = calc_score(a, None)
        second_score = calc_score(b, None)
    
        return first_score < second_score

    
    def compare_minimize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        """
        Compare two scalar objectives using their computed scores.

        Args:
            a (ScalarObjective): Reference objective.
            b (ScalarObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` has a better score
            than the reference objective ``a`` according to the objective
            direction.
        """
        calc_score = self.calc_score
        first_score = calc_score(a, None)
        second_score = calc_score(b, None)
    
        return first_score > second_score
    
    def compare_individuals_maximize(self, a: BaseIndividual, b: BaseIndividual) -> bool: 
        """
        Compare two individuals using their scalar objective scores.

        Args:
            a (BaseIndividual): Reference individual.
            b (BaseIndividual): Candidate individual.

        Returns:
            bool: ``True`` if the candidate individual ``b`` has a better score
            than the reference individual ``a`` according to the objective
            direction.
        """
        calc_score = self.calc_score
        first_score = calc_score(a.get_objective(), a)
        second_score = calc_score(b.get_objective(), b)

        return first_score < second_score

    def compare_individuals_minimize(self, a: BaseIndividual, b: BaseIndividual) -> bool: 
        """
        Compare two individuals using their scalar objective scores.

        Args:
            a (BaseIndividual): Reference individual.
            b (BaseIndividual): Candidate individual.

        Returns:
            bool: ``True`` if the candidate individual ``b`` has a better score
            than the reference individual ``a`` according to the objective
            direction.
        """
        calc_score = self.calc_score
        first_score = calc_score(a.get_objective(), a)
        second_score = calc_score(b.get_objective(), b)

        return first_score > second_score
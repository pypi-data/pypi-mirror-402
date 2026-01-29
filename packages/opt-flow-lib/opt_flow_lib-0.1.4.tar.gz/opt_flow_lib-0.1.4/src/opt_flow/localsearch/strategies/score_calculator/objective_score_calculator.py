from opt_flow.localsearch.interfaces import ScoreCalculator
from opt_flow.structure._base import BaseObjective
from opt_flow.structure import ScalarObjective 
from opt_flow.structure import BaseIndividual
from opt_flow.structure import MultiObjective

class ObjectiveScoreCalculator(ScoreCalculator):
    """
    Computes numeric scores for objectives, converting them into a form suitable
    for minimization-based local search algorithms.

    Scalar objectives are inverted if they are to be maximized. Multi-objectives
    are converted into tuples of scores, one per component objective.
    """
    
    def calculate_score(self, objective: BaseObjective, individual: BaseIndividual):
        """
        Calculate a numeric score for a given individual's objective.

        Args:
            objective (BaseObjective): The objective to score.
            individual (BaseIndividual): The individual associated with the objective.

        Returns:
            float or tuple: A score suitable for minimization. Returns a float
            for scalar objectives or a tuple of floats for multi-objectives.
        """
        if isinstance(objective, ScalarObjective):
            return (objective.value,)
        elif isinstance(objective, MultiObjective):
            return tuple(comp.value for comp in objective.objectives)
        

from opt_flow.structure._base import BaseObjective
from opt_flow.structure import BaseIndividual
from abc import abstractmethod
from opt_flow.utils import NamedOperator
from typing import Optional

class ScoreCalculator(NamedOperator):
    
    """
    Abstract base class for computing scalar scores from objectives and/or individuals.

    Score calculators are used by acceptance criteria (e.g. score-based or
    simulated annealing variants) to transform objectives or full individuals
    into comparable scalar values.
    """
    
    @abstractmethod
    def calculate_score(self, objective: Optional[BaseObjective], individual: Optional[BaseIndividual]) -> float:
        """
        Compute a scalar score for a given objective and/or individual.

        Implementations may rely solely on the objective, solely on the individual,
        or on a combination of both. Either argument may be ``None`` depending on
        the context in which the score is computed.

        Args:
            objective (Optional[BaseObjective]): Objective associated with the individual,
                or ``None`` if not available.
            individual (Optional[BaseIndividual]): Full individual instance,
                or ``None`` if not required.

        Returns:
            float: Scalar score used for comparison in acceptance decisions.
        """
        pass 
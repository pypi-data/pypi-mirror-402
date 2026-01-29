from abc import abstractmethod
from typing import List, Any
from opt_flow.utils import NamedOperator

class ScoreNormalizer(NamedOperator):
    """
    Abstract base class for normalizing collections of scores.

    Score normalizers transform raw scores into a normalized form
    (e.g., scaling, ranking, or probabilistic distributions) to make
    them comparable or suitable for downstream decision processes.
    """
    
    @abstractmethod
    def normalize(self, scores: List[Any]) -> List[Any]:
        """
        Normalize a list of scores.

        Implementations may modify score magnitudes, order, or representation,
        but must preserve positional correspondence between input and output.

        Args:
            scores (List[Any]): List of raw scores to normalize.

        Returns:
            List[Any]: Normalized scores, aligned with the input order.
        """
        pass 
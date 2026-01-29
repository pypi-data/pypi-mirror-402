from opt_flow.localsearch.interfaces import ScoreNormalizer

class DefaultNormalizer(ScoreNormalizer):
    """
    A score normalizer that leaves scores unchanged.

    This normalizer performs no transformation on the input scores and
    simply returns them as-is. Useful when no normalization is required.
    """
    
    def normalize(self, scores):
        """
        Return the input scores without any modification.

        Args:
            scores (List[Any]): A list of scores to normalize.

        Returns:
            List[Any]: The same list of scores, unchanged.
        """
        return scores
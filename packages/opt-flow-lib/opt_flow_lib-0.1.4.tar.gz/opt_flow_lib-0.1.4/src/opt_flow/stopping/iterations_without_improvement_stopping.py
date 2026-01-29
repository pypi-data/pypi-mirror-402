from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs


class IterationsWithoutImprovementStopping(BaseStopping):
    """
    Stopping criterion that triggers after a fixed number of iterations
    without any improvement.

    This stopping condition stops the algorithm once a solution has not
    improved for a predefined number of consecutive iterations. It is
    commonly used to detect stagnation in metaheuristic searches.
    """
    __dependencies__ = ["iterations_without_improvement"]
    __slots__ = ("iteration_limit",)
    def __init__(self, iteration_limit: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iteration_limit = iteration_limit
        
    def _stop(self, args: CallbackArgs) -> bool:
        return args.iterations_without_improvement >= self.iteration_limit
    
    def _is_null(self, individual) -> bool:
        return self.iteration_limit <= 0
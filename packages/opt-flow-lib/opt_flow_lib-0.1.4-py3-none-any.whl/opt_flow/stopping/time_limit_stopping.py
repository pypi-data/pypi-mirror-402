from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs

class TimeLimitStopping(BaseStopping):
    """
    Stopping criterion that triggers after a fixed elapsed time.

    This stopping condition stops the algorithm once the total
    execution time exceeds a predefined limit. It is commonly used
    to enforce time budgets in metaheuristic algorithms.
    """
    __slots__ = ("time_limit",)
    def __init__(self, time_limit: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_limit = time_limit
        
    def _stop(self, args: CallbackArgs) -> bool:
        return self._elapsed_time() >= self.time_limit
    
    def _is_null(self, individual) -> bool:
        return self.time_limit <= 0
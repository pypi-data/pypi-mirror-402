from opt_flow.stopping._base.base_stopping import BaseStopping
from opt_flow.callback import CallbackArgs


class TimeWithoutImprovementStopping(BaseStopping):
    
    """
    Stopping criterion that triggers after a fixed amount of time
    without improvement.

    This stopping condition stops the algorithm once the time elapsed
    without any improvement exceeds a predefined limit. It is commonly
    used to detect stagnation in metaheuristic searches.
    """
    __dependencies__ = ["time_without_improvement"]
    __slots__ = ("time_limit",)
    def __init__(self, time_limit: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_limit = time_limit
        
    def _stop(self, args: CallbackArgs) -> bool:
        return args.time_without_improvement >= self.time_limit
    
    def _is_null(self, individual) -> bool:
        return self.time_limit <= 0
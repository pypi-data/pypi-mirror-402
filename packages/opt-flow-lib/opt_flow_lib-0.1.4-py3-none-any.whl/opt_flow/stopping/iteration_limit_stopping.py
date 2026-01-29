from opt_flow.stopping._base import BaseStopping 
from opt_flow.callback import CallbackArgs

class IterationLimitStopping(BaseStopping):
    """
    Stopping criterion that triggers after a fixed number of iterations.

    This stopping condition stops the algorithm once the number of
    iterations reaches a predefined limit. It can be used to control
    the computational budget of a metaheuristic.
    """
    __dependencies__ = ["iteration"]
    __slots__ = ("iteration_limit",)
    def __init__(self, iteration_limit: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iteration_limit = iteration_limit
        
    def _stop(self, args: CallbackArgs) -> bool:
        return args.iteration >= self.iteration_limit
    
    def _is_null(self, individual) -> bool:
        return self.iteration_limit <= 0
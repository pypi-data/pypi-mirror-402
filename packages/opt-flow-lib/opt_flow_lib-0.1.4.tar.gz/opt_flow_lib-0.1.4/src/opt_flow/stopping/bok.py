from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs

class Bok(BaseStopping):
    """
    Stopping criterion that triggers after a fixed number of improvements.

    This stopping condition stops the algorithm once the total number of
    improvements reaches a predefined threshold `k`. It can be used to
    limit the number of improvement steps in a metaheuristic.
    """
    __dependencies__ = ["total_improvements"]
    
    __slots__ = ("k",)
    def __init__(self, k: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k = k

    def _stop(self, args: CallbackArgs) -> bool:
        return args.total_improvements >= self.k
    
    def _is_null(self, individual) -> bool:
        return self.k <= 0
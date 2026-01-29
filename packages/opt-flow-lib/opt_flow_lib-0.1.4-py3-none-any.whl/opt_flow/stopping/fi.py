from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs

class FI(BaseStopping):
    """
    Stopping criterion that triggers when an improvement is accepted.

    This stopping condition stops the algorithm immediately if the most
    recent solution was accepted. It is useful for single-improvement
    evaluation scenarios or greedy metaheuristics.
    """

    def _stop(self, args: CallbackArgs) -> bool:
        return args.accepted
    
    def _is_null(self, individual) -> bool:
        return False
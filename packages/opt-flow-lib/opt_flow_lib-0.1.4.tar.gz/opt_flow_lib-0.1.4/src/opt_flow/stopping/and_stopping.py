from opt_flow.stopping._base import BaseCompositeStopping
from opt_flow.callback import CallbackArgs

class AndStopping(BaseCompositeStopping):
    
    """
    Composite stopping criterion that stops only when all contained
    strategies signal stopping.

    This is useful when combining multiple stopping conditions with
    logical AND semantics, e.g., stop when both time limit and iteration
    limit are reached.
    """

    def _stop(self, args: CallbackArgs) -> bool:
        return all(s._stop(args) for s in self.strategies)
    
    def _is_null(self, individual) -> bool:
        return all(s._is_null(individual) for s in self.strategies)
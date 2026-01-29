from opt_flow.stopping._base import BaseCompositeStopping
from opt_flow.callback import CallbackArgs

class OrStopping(BaseCompositeStopping):
    
    """
    Composite stopping criterion that stops if any contained strategy signals stop.

    This is useful when combining multiple stopping conditions with
    logical OR semantics, e.g., stop when either a time limit or an
    iteration limit is reached.
    """

    def _stop(self, args: CallbackArgs) -> bool:
        return any(s._stop(args) for s in self.strategies)
    
    def _is_null(self, individual) -> bool:
        return any(s._is_null(individual) for s in self.strategies)
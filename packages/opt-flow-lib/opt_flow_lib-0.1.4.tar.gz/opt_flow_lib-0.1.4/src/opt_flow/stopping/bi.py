from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs

class BI(BaseStopping):
    """
    A trivial stopping criterion.

    This stopping criterion never triggers a stop and considers all
    individuals as valid (non-null). It can be used as a placeholder
    or default stopping strategy when no actual stopping condition
    is required.
    """
    def _stop(self, args: CallbackArgs) -> bool:
        return False
    
    def _is_null(self, individual) -> bool:
        return False
from opt_flow.stopping._base import BaseStopping
from opt_flow.callback import CallbackArgs
from opt_flow.structure._base import BaseObjective
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.config import config
from typing import Optional

class QualityStopping(BaseStopping):
    
    """
    Stopping criterion that triggers when a individual reaches a target quality.

    This stopping condition uses a BaseAcceptance strategy to determine
    whether the current individual meets or exceeds a predefined target
    objective. It is commonly used to terminate metaheuristics once a
    desired individual quality is achieved.
    """
    
    def __init__(self, target_objective: BaseObjective, acceptance: Optional[BaseAcceptance] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_objective = target_objective or config
        self.acceptance = acceptance
        
    def _stop(self, args: CallbackArgs) -> bool:
        return self.acceptance.compare(self.target_objective, args.objective)
    
    def _is_null(self, individual) -> bool:
        return self.acceptance.compare(self.target_objective, individual.get_objective())
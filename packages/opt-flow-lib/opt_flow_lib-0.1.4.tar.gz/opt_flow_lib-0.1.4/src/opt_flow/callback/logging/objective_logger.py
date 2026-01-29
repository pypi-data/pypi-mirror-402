from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
from logging import INFO, log



class ObjectiveLogger(Callback):
    
    """
    Callback that logs objective values during optimization.

    Depending on the `on_improvement` flag, the objective is logged
    only when the candidate individual is accepted (improvement), or
    at every callback call.
    """
    
    def __init__(self, on_improvement=True, level=INFO):
        """
        Initialize the ObjectiveLogger callback.

        Args:
            on_improvement (bool): If True, log only when a candidate individual
                is accepted. If False, log every callback invocation.
            level (int): Logging level to use (e.g., logging.INFO, logging.DEBUG).
        """
        self.on_improvement = on_improvement
        self.level = level
    
    def __call__(self, arg: CallbackArgs):
        """
        Log the objective value based on the callback context.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback,
                including whether the candidate individual was accepted and its objective value.
        """
        if arg.accepted and self.on_improvement:
            log(self.level, arg.objective)
        elif not self.on_improvement:
            log(self.level, arg.objective)
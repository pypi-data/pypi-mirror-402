from __future__ import annotations
from typing import TYPE_CHECKING
from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
if TYPE_CHECKING:
    from opt_flow.trajectory.composite import ParallelTrajectory
    from opt_flow.stopping import TimeLimitStopping
    
class ParallelTrajectoryTimeStoppingUpdate(Callback):
    """
    Callback that updates the time limit of a TimeLimitStopping object
    based on the polling interval of a ParallelTrajectory instance.

    The stopping time limit is synchronized with the current polling interval,
    allowing dynamic adjustment during the optimization process.
    """
    
    def __init__(self, imp: "ParallelTrajectory", stopping: "TimeLimitStopping"):
        """
        Initialize the callback with a ParallelTrajectory and TimeLimitStopping instance.

        Args:
            imp (ParallelTrajectory): The parallel improvement object whose
                polling interval is used to update the time limit.
            stopping (TimeLimitStopping): The stopping object whose time limit
                will be updated.
        """
        self.imp = imp
        self.stopping = stopping

    
    def __call__(self, arg: CallbackArgs):
        """
        Update the stopping time limit based on the polling interval.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback.
        """
        self.stopping.time_limit = self.imp.polling_interval
        


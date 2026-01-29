from __future__ import annotations
from typing import TYPE_CHECKING
from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
if TYPE_CHECKING:
    from opt_flow.trajectory.composite import ParallelTrajectory

class ParallelPollingUpdate(Callback):
    """
    Callback that updates the polling interval of a ParallelTrajectory instance.

    The polling interval is adjusted dynamically based on whether the
    candidate individual was accepted. It decreases when a individual is
    accepted and increases when rejected, within the minimum and maximum
    interval bounds.
    """

    
    def __init__(self, imp: "ParallelTrajectory"):
        """
        Initialize the callback with a ParallelTrajectory instance.

        Args:
            imp (ParallelTrajectory): The parallel trajectory object
                whose polling interval will be updated.
        """
        self.imp = imp

    
    def __call__(self, arg: CallbackArgs):
        """
        Adjust the polling interval based on the acceptance of the candidate individual.

        If the candidate was accepted, the interval is decreased but not
        below the minimum interval. If rejected, it is increased but not
        above the maximum interval.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback,
                including whether the current candidate individual was accepted.
        """
        if arg.accepted:
            self.imp.polling_interval = max(self.imp.min_polling_interval, self.imp.polling_interval * (1 - self.imp.polling_delta))
        else:
            self.imp.polling_interval = min(self.imp.max_polling_interval, self.imp.polling_interval * (1 + self.imp.polling_delta))



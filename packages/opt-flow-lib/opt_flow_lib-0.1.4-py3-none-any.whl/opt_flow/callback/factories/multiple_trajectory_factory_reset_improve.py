from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
from opt_flow.metaheuristic.factories import MultipleTrajectoryFactory

class MultipleTrajectoryFactoryResetImprove(Callback):

    """
    Callback that resets the current operator index in a MultipleTrajectoryFactory if 
    any improvement is found in the current iteration.

    This callback sets the factory's operator index `k` to zero, typically
    used to restart or reset the selection sequence in the factory.
    """
    def __init__(self, factory: MultipleTrajectoryFactory):
        """
        Initialize the callback with a MultipleTrajectoryFactory instance.

        Args:
            factory (MultipleTrajectoryFactory): The factory object whose
                operator index will be reset.
        """
        self.factory = factory
    
    def __call__(self, arg: CallbackArgs):
        if arg.accepted:
            self.factory.k = 0

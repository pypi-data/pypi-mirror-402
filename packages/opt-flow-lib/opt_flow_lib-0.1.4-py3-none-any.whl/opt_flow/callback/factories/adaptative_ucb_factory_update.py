from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
from opt_flow.metaheuristic.factories.trajectory import AdaptativeUCBFactory

class AdaptativeUCBFactoryUpdate(Callback):
    """
    Callback that updates success and attempt counts in an AdaptativeUCBFactory.

    This callback tracks the performance of the currently selected operator
    within the UCB-based factory. The attempt counts and total attempts are
    always incremented, while the success count is incremented if the candidate
    solution was accepted.
    """

    
    def __init__(self, factory: AdaptativeUCBFactory):
        """
        Initialize the callback with an AdaptativeUCBFactory instance.

        Args:
            factory (AdaptativeUCBFactory): The UCB factory object whose counters
                will be updated.
        """
        self.factory = factory

    
    def __call__(self, arg: CallbackArgs):
        """
        Update the UCB factory's counters based on the callback event.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback,
                including whether the current candidate solution was accepted.
        """
        k = self.factory.k 
        self.factory.attempt_counts[k] += 1
        self.factory.total_attempts += 1
        if arg.accepted:
            self.factory.success_counts[k] += 1
            
        

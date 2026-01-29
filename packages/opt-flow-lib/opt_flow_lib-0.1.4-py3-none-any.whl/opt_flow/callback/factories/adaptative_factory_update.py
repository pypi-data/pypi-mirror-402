from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
from opt_flow.metaheuristic.factories.trajectory import AdaptativeFactory

class AdaptativeFactoryUpdate(Callback):

    """
    Callback that updates success and attempt counts in an AdaptativeFactory.

    This callback tracks the performance of the currently selected operator
    within the factory, incrementing the success count if the candidate
    individual was accepted, and always incrementing the attempt count.
    """
    def __init__(self, factory: AdaptativeFactory):
        """
        Initialize the callback with an AdaptativeFactory instance.

        Args:
            factory (AdaptativeFactory): The factory object whose counters
                will be updated.
        """
        self.factory = factory

    
    def __call__(self, arg: CallbackArgs):
        """
        Update the factory's success and attempt counters based on the callback event.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback,
                including whether the current candidate individual was accepted.
        """
        k = self.factory.k
        if arg.accepted:
            self.factory.success_counts[k] += 1
        self.factory.attempt_counts[k] += 1
        
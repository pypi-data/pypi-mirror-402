from opt_flow.callback.base.callback_args import CallbackArgs
from abc import ABC, abstractmethod


class Callback(ABC):
    
    """
    Abstract base class for callbacks in the optimization framework.

    Subclasses should implement the ``__call__`` method to define
    behavior triggered during specific events or stages of an algorithm.
    """
    __dependencies__ = []
    def __init__(self, *args, **kwargs):
        """
        Initialize a callback instance.

        Args:
            *args, **kwargs: Additional arguments for subclasses.
        """
        super().__init__(*args, **kwargs)
        
    @abstractmethod
    def __call__(self, args: CallbackArgs):
        """
        Execute the callback logic.

        This method is called with an instance of :class:`CallbackArgs`,
        which contains context and data relevant to the callback event.

        Args:
            args (CallbackArgs): Object containing contextual information
                for the callback.
        """
        pass
    

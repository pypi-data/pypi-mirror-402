from abc import ABC, abstractmethod
from opt_flow.callback import CallbackArgs 
import time


class BaseStopping(ABC):
    
    __dependencies__ = []
    def __init__(self, *args, **kwargs):
        self.start_time = None

    def _start(self):
        self.start_time = time.time()
    
    @abstractmethod
    def _is_null(self, individual) -> bool:
        pass

    @abstractmethod
    def _stop(self, cb_args: CallbackArgs) -> bool:
        pass

    def _elapsed_time(self) -> float:
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
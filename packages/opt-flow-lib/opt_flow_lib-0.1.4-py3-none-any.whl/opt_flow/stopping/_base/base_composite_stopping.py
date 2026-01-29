from opt_flow.stopping._base.base_stopping import BaseStopping
from typing import List

class BaseCompositeStopping(BaseStopping):

    def __init__(self, strategies: List[BaseStopping], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.strategies = strategies
        self.__dependencies__ = {dep for strategy in strategies for dep in strategy.__dependencies__}

    def _start(self):
        super()._start()
        for s in self.strategies:
            s._start()

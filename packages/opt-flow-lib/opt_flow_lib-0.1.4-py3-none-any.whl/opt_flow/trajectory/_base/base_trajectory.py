from opt_flow.structure import BaseIndividual
from abc import abstractmethod
from opt_flow.stopping._base.base_stopping import BaseStopping
from opt_flow.stopping.no_stopping import NoStopping
from opt_flow.stats import StatsTracker
from opt_flow.stats import StatsRecord
from opt_flow.utils import NamedOperator
from opt_flow.callback import Callback
from opt_flow.callback import CallbackArgs
from opt_flow.stats import ImprovementHistory
from opt_flow.stats.improvement_history_view import ImprovementHistoryView
from typing import Optional, List
from opt_flow.reproducibility.iterations_registry import _register_execution, _init_registry
from opt_flow.config import config
import logging
from opt_flow.reproducibility.iterations_registry import _init_registry
from functools import wraps


def _ensure_on_start(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._on_start()
        return method(self, *args, **kwargs)
    return wrapper

def _check_null_stoppings(func):
    @wraps(func)
    def wrapper(self, individual):
        if self._stopping_criterion._is_null(individual):
            return
        return func(self, individual)
    return wrapper



class BaseTrajectory(NamedOperator):
    """
    Abstract base class for trajectory operators in optimization algorithms.

    A trajectory operator attempts to enhance a given individual according to 
    a defined strategy. This class manages execution tracking, stopping criteria, 
    and callback invocation. Subclasses must implement the `iterate` method.
    """
    
    decorators = [_check_null_stoppings, _register_execution, _ensure_on_start]
    
    def __init_subclass__(cls):
        super().__init_subclass__()
        for name, func in cls.__dict__.items():
            if name == "iterate" and callable(func):
                for dec in reversed(cls.decorators):
                    func = dec(func)
                setattr(cls, name, func)
    
    def __init__(self, stopping: BaseStopping=NoStopping(), callbacks: Optional[List[Callback]]=None, **kwargs):
        super().__init__(**kwargs)
        self._stopping_criterion = stopping
        self._tracker = StatsTracker()
        if not hasattr(self, "_callbacks") or not self._callbacks:
            self._callbacks = callbacks or []
        self._execution_id = 0
        config._increment_imp_id()
        _init_registry()
        
    def get_improvement_history(self) -> ImprovementHistory:
        """
        Returns the history of improvements recorded by this operator.

        Returns
        -------
        ImprovementHistory
            Object containing the sequence of improvements and associated statistics.
        """
        return self._tracker.get_improvement_history()
    
    def get_improvement_history_view(self) -> ImprovementHistoryView:
        """
        Returns a view of the history of improvements recorded by this operator.

        Returns
        -------
        ImprovementHistoryView
            Object containing a view of the sequence of improvements and associated statistics.
        """
        return self.get_improvement_history().view()
    

    @property
    def imp_id(self):
        return config.imp_id

    @abstractmethod
    def iterate(self, individual: BaseIndividual):
        """
        Abstract method that performs a trajectory operator on the provided individual.

        Subclasses must implement this method to define the actual trajectory operator 
        strategy.

        Parameters
        ----------
        individual : BaseIndividual
            The individual to be modified.

        Returns
        -------
        None
        """
        pass
    
    @property
    def id(self):
        return 'IMP' + str(self.imp_id) + '_' + str(self._execution_id)
    
    def _increment_execution_id(self):
        self._execution_id += 1

    def _should_continue(self, individual: BaseIndividual, improved: bool, name: str) -> bool:
        record = StatsRecord(individual.get_objective(), improved, individual, name)
        self._tracker._record(record)
        args = CallbackArgs.from_stats(record, self._tracker)
        self._run_callbacks(args)
        return not self._stopping_criterion._stop(args) 

    def _on_start(self):
        dependencies = {dep for x in self._callbacks for dep in x.__dependencies__}.union(set(self._stopping_criterion.__dependencies__))
        self._tracker = StatsTracker(dependencies)
        self._stopping_criterion._start()

    def _run_callbacks(self, args: CallbackArgs):
        for cb in self._callbacks:
            try:
                cb(args)
            except Exception as e:
                logging.error(f'Error invoking callback {cb.__class__.__name__}: {e}')
                raise

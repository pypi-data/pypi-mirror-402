from abc import abstractmethod
from opt_flow.structure import BaseIndividual
from opt_flow.movement import MovementType
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.utils import RandomClass
from opt_flow.utils import NamedOperator
from opt_flow.callback import Callback
from opt_flow.callback import CallbackArgs
from opt_flow.stats import StatsTracker
from opt_flow.stats import StatsRecord
from opt_flow.stopping._base import BaseStopping
from opt_flow.stopping import BI
from typing import Optional, List
from opt_flow.structure._base import BaseObjective
from opt_flow.reproducibility.iterations_registry import _register_execution
from opt_flow.config import config
from logging import error
from opt_flow.reproducibility.iterations_registry import _init_registry
from functools import wraps
from opt_flow.config import config

def _check_null_stoppings(func):
    """
    Decorator that skips the execution of a function if the stopping criterion
    considers the individual "null" (i.e., no further improvement is needed).
    """
    @wraps(func)
    def wrapper(self, individual):
        if self._stopping_criterion._is_null(individual):
            return False
        return func(self, individual)
    return wrapper


class BaseLocalSearch(RandomClass, NamedOperator):
    
    """
    Abstract base class for local search algorithms.

    This class provides a framework for implementing local search operators
    in an optimization problem. It manages execution IDs, stopping criteria,
    callbacks, acceptance criteria, and statistical tracking of improvements.

    Subclasses must implement the `_search` method with problem-specific
    search logic.
    """

    def __init__(
        self, movement_type: MovementType, acceptance: Optional[BaseAcceptance] = None, seed: Optional[int] = None, stopping_criterion: Optional[BaseStopping] = None, callbacks: Optional[List[Callback]] = None
    ):
        """
        Initialize a BaseLocalSearch operator.

        Args:
            movement_type (MovementType): The type of move to perform during local search.
            acceptance (BaseAcceptance, optional): Acceptance criterion for candidate individuals.
                Defaults to the global default acceptance in `config`.
            seed (int, optional): Random seed for reproducibility. Defaults to None.
            stopping_criterion (BaseStopping, optional): Stopping criterion. Defaults to BI().
            callbacks (List[Callback], optional): List of callbacks to invoke during search.
        """
        self.acceptance = acceptance or config.default_acceptance
        self.movement_type = movement_type
        self._tracker = StatsTracker()
        self._callbacks = callbacks or []
        self._stopping_criterion = stopping_criterion or BI()
        self._execution_id = 0
        config._increment_ls_id()
        super().__init__(seed=seed)
        _init_registry()

    def _on_start(self):
        dependencies = {dep for x in self._callbacks for dep in x.__dependencies__}.union(set(self._stopping_criterion.__dependencies__))
        dependencies.add("total_improvements")
        self._tracker = StatsTracker(dependencies)
        self._stopping_criterion._start()
        
    @property
    def ls_id(self):
        return int(config.ls_id)
        
    def _increment_execution_id(self):
        self._execution_id += 1
        
    @property
    def id(self):
        return 'LS' + str(self.ls_id) + '_' + str(self._execution_id)
        
    def _should_continue(self, individual: BaseIndividual, objective: BaseObjective, improved: bool, name: str) -> bool:
        record = StatsRecord(objective, improved, individual, name)
        tracker = self._tracker
        tracker._record(record)
        args = CallbackArgs.from_stats(record, tracker)
        if self._callbacks:
            self._run_callbacks(args)
        return not self._stopping_criterion._stop(args) 
                
                
    @_check_null_stoppings
    @_register_execution
    def _attempt_improvement(self, individual: BaseIndividual) -> bool:
        self._on_start()
        return self._search(individual)
    
    @abstractmethod
    def _search(self, individual: BaseIndividual) -> bool:
        pass
    
    def _run_callbacks(self, args: CallbackArgs):
        for cb in self._callbacks:
            try:
                cb(args)
            except Exception as e:
                error(f'Error invoking callback {cb.__class__.__name__}: {e}')
                raise
            
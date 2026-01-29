from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.structure.base_individual import BaseIndividual
from opt_flow.localsearch._base import BaseLocalSearch
from opt_flow.stopping import OrStopping 
from opt_flow.stopping.iterations_without_improvement_stopping import (
    IterationsWithoutImprovementStopping,
)
from opt_flow.stopping import BaseStopping, NoStopping
from opt_flow.callback import Callback
from typing import Optional, List

class HillClimbing(BaseTrajectory):
    """
    Implements a simple hill-climbing metaheuristic using a given local search.

    Hill Climbing repeatedly applies the local search to a individual until no further improvement 
    is possible or a stopping criterion is reached. It is a greedy strategy, accepting only 
    improvements in the individual.

    Parameters
    ----------
    ls : BaseLocalSearch
        The local search instance used to attempt improvements on the individual.
    stopping_criterion : BaseStopping, optional
        A stopping criterion to terminate the improvement process (default: NoStopping()).
        The class automatically combines it with a stopping criterion that halts after 
        one iteration without improvement.
    callbacks : List[Callback], optional
        List of callback functions invoked during the improvement process.
    """

    def __init__(self, ls: BaseLocalSearch, stopping_criterion: BaseStopping = NoStopping(), callbacks: Optional[List[Callback]] = None):
        stopping_criterion = OrStopping(
            [stopping_criterion, IterationsWithoutImprovementStopping(1)]
        )
        super().__init__(stopping_criterion, callbacks)
        self._local_search = ls

    @property
    def short_name(self) -> str:
        return f"{self.variant} - {self._local_search.short_name}"

    def iterate(self, individual: BaseIndividual):
        """
        Perform hill-climbing trajectory on the given individual.

        Repeatedly applies the local search to the individual, accepting only improvements,
        until the stopping criterion is met.

        Parameters
        ----------
        individual : BaseIndividual
            The individual to be iterated upon.
        """
        self._on_start()
        improved = False
        while True:
            if self._local_search._attempt_improvement(individual):
                improved = True
            else:
                improved = False
            if not self._should_continue(
                individual, improved, self._local_search.short_name
            ):
                break

from opt_flow.localsearch.interfaces import MemoryStrategy
from collections import deque
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure import BaseIndividual
from opt_flow.structure._base import BaseObjective
from opt_flow.movement import ArgsT
from logging import warning



class TabuMemory(MemoryStrategy):
    """
    Tabu-based memory strategy with aspiration criterion.

    This strategy maintains a fixed-length tabu list of recently
    accepted move arguments. A move is considered tabu if its
    argument is present in the tabu list, unless the aspiration
    criterion is satisfied.

    The aspiration criterion allows tabu moves if they improve
    upon the best individual found so far, according to the provided
    acceptance rule.

    Notes:
        - Movement arguments must implement a meaningful `__eq__`
          method, as tabu membership is checked using equality.
        - The tabu list operates as a FIFO queue with a fixed tenure.
    """
    def __init__(self, tenure: int, acceptance: BaseAcceptance):
        """
        Initialize the tabu memory.

        Args:
            tenure (int): Maximum number of move arguments stored
                in the tabu list.
            acceptance (BaseAcceptance): Acceptance rule used to
                compare objectives and evaluate aspiration.
        """
        warning('Ensure that the movement args define a suitable __eq__ method to use TabuMemory.')
        self.tabu_list = deque(maxlen=tenure)
        self.acceptance = acceptance
        self.best_individual = None
        
    @property
    def name(self, sep='\n') -> str:
        return f"tabu memory {sep}Tenure: {self.tabu_list.maxlen}"

    def is_tabu(self, move_arg: ArgsT, objective: BaseObjective) -> bool:
        is_tabu = move_arg in self.tabu_list
        return is_tabu and not self._aspiration(objective)

    def _aspiration(self, objective: BaseObjective) -> bool:
        if self.best_individual is None:
            return True
        return self.acceptance.compare(self.best_individual.get_objective(), objective)

    def _on_accept(self, move_arg: ArgsT, individual: BaseIndividual):
        self.tabu_list.append(move_arg)
        if self.best_individual is None or self.acceptance.compare_individuals(self.best_individual, individual):
            self.best_individual = individual.copy()
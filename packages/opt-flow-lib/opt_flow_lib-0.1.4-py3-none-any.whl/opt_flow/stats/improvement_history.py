from typing import List, Tuple, Any
from opt_flow.stats.improvement_history_view import ImprovementHistoryView



class ImprovementHistory(list):
    """
    Tracks the history of improvements in a metaheuristic algorithm.

    Each entry is a tuple of:
        (objective, event_name, accepted_flag, timestamp)
    """


    def get_all(self) -> List[Tuple[Any, str, bool, float]]:
        return self.copy()

    def copy(self):
        new_hist = ImprovementHistory(self[:])
        return new_hist


    def clear_history(self):
        self.clear()

    def timestamps(self) -> List[float]:
        return [r[3] for r in self]

    def events(self) -> List[str]:
        return [r[1] for r in self]

    def objectives(self) -> List[tuple]:
        from opt_flow.structure import ScalarObjective
        values = []
        for r in self:
            v = r[0]
            if isinstance(v, ScalarObjective):
                values.append((v.value,))
            else:
                values.append(tuple(vx.value for vx in v))
        return values
    
    def names(self) -> List[Any]:
        from opt_flow.structure import ScalarObjective
        values = []
        for r in self:
            v = r[0]
            if isinstance(v, ScalarObjective):
                values.append((v.name,))
            else:
                values.append(tuple(vx.name for vx in v))
        return values
    

    def accepted_mask(self) -> List[bool]:
        return [r[2] for r in self]

    def get(self, only_accepted=False) -> List[Tuple[Any, str, bool, float]]:
        return [r for r in self if (r[2] or not only_accepted)]

    def view(self) -> ImprovementHistoryView:
        """
        Get a view object for analyzing or plotting the improvement history.

        Returns:
            ImprovementHistoryView: A view of the history.
        """
        return ImprovementHistoryView(self)

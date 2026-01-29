from typing import Tuple, List
from opt_flow.structure.scalar_objective import ScalarObjective
from opt_flow.structure._base import BaseObjective


class MultiObjective(BaseObjective):
    __slots__ = ("objectives",)

    def __init__(self, objectives: List[ScalarObjective]):
        self.objectives = objectives

    def __len__(self):
        return len(self.objectives)

    def __getitem__(self, index):
        return self.objectives[index]
    @property
    def name(self, sep=" || ") -> str:
        return sep.join([obj.__repr__() for obj in self.objectives])
    
    def __iter__(self):
        return iter(self.objectives)
    
    def __repr__(self) -> str:
        return self.name
    
    def to_tuple(self) -> Tuple[Tuple[float], Tuple[str]]:
        return tuple(o.value for o in self.objectives), tuple(o._name for o in self.objectives)
    


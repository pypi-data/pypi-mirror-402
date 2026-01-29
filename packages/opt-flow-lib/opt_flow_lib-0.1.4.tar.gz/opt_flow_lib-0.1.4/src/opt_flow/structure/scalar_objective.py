from opt_flow.structure._base import BaseObjective
from typing import Tuple
class ScalarObjective(BaseObjective):
    """
    Represents a single scalar optimization objective.

    Attributes
    ----------
    name : str
        The name of the objective.
    value : float
        The numeric value of the objective.
    """
    __slots__ = ('_name', 'value')
    def __init__(self, name: str, value: float):
        self._name = name
        self.value = value
        
    def __repr__(self) -> str:
        return self.short_name
    
    @property
    def short_name(self) -> str:
        return f"{self._name} - {self.value}"

    @property
    def name(self):
        return self._name
    
    def to_tuple(self) -> Tuple[Tuple[float], Tuple[str]]:
        return (self.value,), (self._name,)

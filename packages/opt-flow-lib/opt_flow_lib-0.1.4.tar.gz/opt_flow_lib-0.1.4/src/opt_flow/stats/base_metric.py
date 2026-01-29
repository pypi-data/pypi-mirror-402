from abc import ABC, abstractmethod
from typing import Any, Dict, Union
from opt_flow.stats.improvement_history import ImprovementHistory

class BaseMetric(ABC):
    """Abstract base for any metric computation."""

    name: str = "unnamed"
    description: str = ""

    @abstractmethod
    def compute(self, history: ImprovementHistory) -> Union[float, Dict[str, Any]]:
        pass

    def info(self):
        """Return human-readable information about this metric."""
        return {"name": self.name, "description": self.description, "parameters": self.__dict__}
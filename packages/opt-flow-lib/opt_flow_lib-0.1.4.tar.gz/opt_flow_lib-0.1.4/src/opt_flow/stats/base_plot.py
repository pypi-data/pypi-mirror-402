from abc import ABC, abstractmethod
from opt_flow.stats.improvement_history import ImprovementHistory

class BasePlot(ABC):
    """Abstract base for any plot computation."""

    name: str = "unnamed"
    description: str = ""

    @abstractmethod
    def plot(self, history: ImprovementHistory):
        pass

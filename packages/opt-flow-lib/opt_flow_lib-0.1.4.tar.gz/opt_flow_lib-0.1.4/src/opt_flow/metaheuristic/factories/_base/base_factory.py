from abc import ABC, abstractmethod
from typing import Any
class BaseFactory(ABC):
    
    """
    Abstract base class for factories that create objects.

    Subclasses must implement the `create` method to return a new object
    instance. This class is designed to standardize object creation across
    different types of factories.
    """
    
    @abstractmethod
    def create(self, **kwargs) -> Any:
        """Return a new algorithm instance."""
        pass



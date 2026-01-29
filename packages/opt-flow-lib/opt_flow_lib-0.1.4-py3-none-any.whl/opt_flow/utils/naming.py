from abc import ABC
from re import compile
from functools import lru_cache

_CAMEL_TO_SNAKE_PATTERN = compile(r'(?<!^)(?=[A-Z])')

@lru_cache(maxsize=128)  # Cache up to 128 most recent conversions
def camel_to_snake(name: str) -> str:
    """Convert CamelCase/PascalCase to snake_case with caching."""
    return _CAMEL_TO_SNAKE_PATTERN.sub('_', name).lower()

class NamedOperator(ABC):
    variant: str
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variant = camel_to_snake(type(self).__name__)
    
    @property
    def name(self, sep='\n') -> str:
        """Full name used in logs/stats."""
        return f"{self.variant}"
    
    @property
    def short_name(self, sep='-') -> str:
        return f"{self.variant}"

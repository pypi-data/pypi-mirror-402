from opt_flow.structure._base import BaseObjective
from opt_flow.structure import BaseIndividual
from functools import wraps
from opt_flow.utils import NamedOperator

def _handle_null_individuals(func):
    """
    Decorator to handle comparisons involving null individuals.

    The comparison logic follows these rules:
    - If the first argument is None, it is always accepted.
    - If the second argument is None, it is always rejected.
    - Otherwise, delegate to the wrapped comparison function.

    This decorator is intended for internal use and is automatically
    applied to individual comparison methods.
    """
    @wraps(func)
    def wrapper(self, a, b):
        if a is None:
            return True
        if b is None:
            return False
        return func(self, a, b)
    return wrapper

class BaseAcceptance(NamedOperator):
    """
    Base class for acceptance criteria between two individuals.
    
    All comparisons follow the convention (reference, candidate).

    Subclasses can customize the acceptance logic in one of two ways:

    **Simple usage**
        Override :meth:`compare` to compare two objectives. The default
        :meth:`compare_individuals` implementation will automatically extract
        objectives from individuals.

    **Advanced usage**
        Override :meth:`compare_individuals` directly to implement custom
        individual-level comparison logic.

    """
    
    decorators = [_handle_null_individuals]

    def __init_subclass__(cls):
        """
        Apply individual comparison decorators to subclass implementations.

        If a subclass defines its own ``compare_individuals`` method, all
        decorators listed in :attr:`decorators` are automatically applied
        to it. This ensures consistent handling of ``None`` individuals
        across all implementations.
        """
        super().__init_subclass__()
        for name, func in cls.__dict__.items():
            if name == "compare_individuals" and callable(func):
                for dec in reversed(cls.decorators):
                    func = dec(func)
                setattr(cls, name, func)
                
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def compare(self, a: BaseObjective, b: BaseObjective) -> bool:
        """
        Compare two objectives and decide whether the candidate is accepted.

        This method is intended for simple acceptance criteria that depend
        only on objective values.

        Subclasses implementing custom individual-level logic should override
        :meth:`compare_individuals` instead.

        Args:
            a (BaseObjective): Reference objective.
            b (BaseObjective): Candidate objective.

        Returns:
            bool: ``True`` if the candidate objective ``b`` is accepted over
            the reference objective ``a``.
        """
        pass

    @_handle_null_individuals
    def compare_individuals(self, a: BaseIndividual, b: BaseIndividual):
        """
        Compare two individuals and decide whether the candidate is accepted.

        This default implementation extracts objectives from the given
        individuals and delegates the comparison to :meth:`compare`.

        Subclasses may override this method to implement custom
        individual-level comparison logic (e.g., using additional individual
        metadata). Decorators defined in :attr:`decorators` are applied
        automatically.

        Args:
            a (BaseIndividual): Reference individual.
            b (BaseIndividual): Candidate individual.

        Returns:
            bool: ``True`` if the candidate individual ``b`` is accepted over
            the reference individual ``a``.
        """
        return self.compare(a.get_objective(), b.get_objective())

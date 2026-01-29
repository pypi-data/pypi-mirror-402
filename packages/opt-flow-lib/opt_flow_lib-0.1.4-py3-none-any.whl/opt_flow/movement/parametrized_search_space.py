from typing import Optional, Type, Any, Dict
from opt_flow.structure import BaseIndividual
from opt_flow.movement import SearchSpace

class ParametrizedSearchSpace:
    """
    Factory class for creating parametrized SearchSpace classes.

    Instantiating this class immediately returns a *new SearchSpace subclass*
    with the given parameters injected.

    This avoids the need for an extra call and allows direct usage like:

        search_space_cls = ParametrizedSearchSpace(
            RegretkSearchSpace,W
            k=3
        )

    The returned object is a real class:
    - Compatible with LocalSearch
    - Preserves associated_movement
    - Accepts (individual, *, seed=None)
    """

    def __new__(
        cls,
        base_cls: Type[SearchSpace],
        **params: Any,
    ) -> Type[SearchSpace]:

        if not issubclass(base_cls, SearchSpace):
            raise TypeError(
                f"{base_cls.__name__} is not a subclass of SearchSpace"
            )

        class _ParametrizedSearchSpace(base_cls):
            def __init__(
                self,
                individual: BaseIndividual,
                *,
                seed: Optional[int] = None,
                **kwargs,
            ):
                merged_kwargs: Dict[str, Any] = dict(params)
                merged_kwargs.update(kwargs)
                super().__init__(individual, **merged_kwargs)

        # Preserve framework-required metadata
        _ParametrizedSearchSpace.associated_movement = (
            base_cls.associated_movement
        )

        # Improve introspection / logging
        param_str = ",".join(f"{k}={v}" for k, v in params.items())
        _ParametrizedSearchSpace.__name__ = (
            f"{base_cls.__name__}[{param_str}]"
            if param_str
            else base_cls.__name__
        )
        _ParametrizedSearchSpace.__qualname__ = _ParametrizedSearchSpace.__name__

        return _ParametrizedSearchSpace

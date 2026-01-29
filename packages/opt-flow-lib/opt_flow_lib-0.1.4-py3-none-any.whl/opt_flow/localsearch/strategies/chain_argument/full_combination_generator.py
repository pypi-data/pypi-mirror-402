from opt_flow.localsearch.interfaces import ChainArgumentGenerator
from typing import Optional, Type, Iterator
from opt_flow.movement import Movement
from opt_flow.movement import SearchSpace
from opt_flow.movement import ArgsT
from opt_flow.structure import BaseIndividual

class FullCombinationGenerator(ChainArgumentGenerator):
    
    """
    Chain argument generator that enumerates all arguments of the next search space.

    This generator ignores the previous movement, arguments, and chain context,
    and simply iterates over all possible arguments produced by the given
    search space for the current individual.
    """
    
    def generate(
        self,
        prev_movement: Optional[Movement],
        prev_movement_cls: Optional[Type[Movement]],
        prev_arg: Optional[ArgsT],
        individual: BaseIndividual,
        level: int,
        next_space_cls: Type[SearchSpace],
        last_individual: Optional[BaseIndividual]
    ) -> Iterator[ArgsT]:
        """
        Generate all possible arguments from the next search space.

        The generated arguments correspond to a full enumeration of the
        provided search space, without any filtering or dependency on
        previous chain elements.

        Args:
            prev_movement (Optional[Movement]): Previous movement instance (unused).
            prev_movement_cls (Optional[Type[Movement]]): Previous movement class (unused).
            prev_arg (Optional[ArgsT]): Argument used in the previous move (unused).
            individual (BaseIndividual): Current individual at this chain level.
            level (int): Depth of the chain (unused).
            next_space_cls (Type[SearchSpace]): Search space defining valid arguments.
            last_individual (Optional[BaseIndividual]): Fallback individual (unused).

        Returns:
            Iterator[ArgsT]: Iterator over all arguments produced by the search space.
        """
        return iter(next_space_cls(individual, seed=self.rng.integers(0, 10000000)))

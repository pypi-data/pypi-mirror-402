from opt_flow.localsearch.interfaces import ChainArgumentGenerator
from typing import Optional, Type, Iterator
from opt_flow.movement import Movement
from opt_flow.movement import SearchSpace
from opt_flow.movement import ArgsT
from opt_flow.localsearch.strategies.link_matrix import LinkMatrix 
from opt_flow.structure.base_individual import BaseIndividual

class LinkedElementGenerator(ChainArgumentGenerator):
    
    """
    Chain argument generator enforcing link constraints between successive moves.

    This generator restricts candidate arguments based on a link checker matrix,
    ensuring that only arguments compatible with the previous movement and
    argument are generated.
    """
    
    def __init__(self, link_checker_matrix: LinkMatrix, seed: Optional[int] = None):
        """
        Initialize the linked element generator.

        Args:
            link_checker_matrix (LinkMatrix): Matrix defining valid transitions
                between pairs of movement types.
            seed (int, optional): Random seed for reproducibility.
        """
        super().__init__(seed=seed)
        self.link_checker_matrix = link_checker_matrix
        
    @property 
    def name(self, sep="\n") -> str:
        return f"{self.short_name(sep)} - {sep}Link Checker Matrix: {self.link_checker_matrix.name(sep)}"

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
        next_movement_type = next_space_cls.associated_movement
        link_checker = self.link_checker_matrix.get(
            (prev_movement_cls, next_movement_type)
        )

        if link_checker is None:
            return iter(next_space_cls(individual, seed=self.rng.integers(0, 10000000)))

        return (
            arg
            for arg in next_space_cls(individual, seed=self.rng.integers(0, 10000000))
            if link_checker.check(prev_arg, last_individual, arg, individual)
        )

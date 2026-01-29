from typing import Type, Optional, Tuple, List, Iterable
from opt_flow.movement import Movement
from opt_flow.movement import SearchSpace
from opt_flow.movement import MovementType
from opt_flow.structure.base_individual import BaseIndividual
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure._base import BaseObjective
from opt_flow.movement import ArgsT
from opt_flow.localsearch.interfaces import MemoryStrategy
from opt_flow.stopping._base import BaseStopping
from opt_flow.localsearch.interfaces import FirstMovementSelector
from opt_flow.localsearch.interfaces import NextMovementSelector
from opt_flow.localsearch.strategies.memory import NoMemory
from opt_flow.stopping import BI
from opt_flow.localsearch.strategies.first_movement import (
    SequentialFirst,
)
from opt_flow.localsearch.strategies.next_movement import SequentialNext
from opt_flow.localsearch._base import BaseLocalSearch
from opt_flow.localsearch.interfaces import ChainArgumentGenerator
from opt_flow.localsearch.strategies.chain_argument import (
    FullCombinationGenerator,
)
from opt_flow.utils import camel_to_snake
from opt_flow.callback import Callback


Stack = List[
    Tuple[
        int,
        Type[Movement],
        Movement,
        BaseIndividual,
        Iterable[ArgsT],
        Optional[ArgsT],
        Optional[BaseIndividual],
    ]
]


class EjectionChain(BaseLocalSearch):
    
    """
    Local search operator implementing the Ejection Chain metaheuristic.

    This operator iteratively applies a sequence of movements on a individual
    to explore deep chains of improvements. It supports multiple search spaces,
    different movement types (DIRECT, SIMULATE, DO_UNDO), memory strategies,
    and custom selection of first and next movements.

    """
    __slots__ = ("max_chain_length", "_short_name")
    
    def __init__(
        self,
        search_spaces: List[Type[SearchSpace]],
        movement_type: MovementType,
        max_chain_length: int,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        memory: Optional[MemoryStrategy] = None, 
        stopping_criterion: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
        first_selector: Optional[FirstMovementSelector] = None,
        next_selector: Optional[NextMovementSelector] = None,
        chain_arguments_generator: Optional[ChainArgumentGenerator] = None,
    ):
        """
        Initialize an EjectionChainLocalSearch operator.

        Args:
            search_spaces (List[Type[SearchSpace]]): List of search space classes to explore.
            movement_type (MovementType): Type of movement execution (DIRECT, SIMULATE, DO_UNDO).
            max_chain_length (int): Maximum depth of the ejection chain.
            acceptance (BaseAcceptance, optional): Acceptance criterion. Defaults to global default.
            seed (int, optional): Random seed for reproducibility.
            memory (MemoryStrategy, optional): Memory strategy for tabu or acceptance restrictions.
            stopping_criterion (BaseStopping, optional): Stopping criterion. Defaults to BI().
            callbacks (List[Callback], optional): Callbacks invoked during search.
            first_selector (FirstMovementSelector, optional): Selector for the first movement in the chain.
            next_selector (NextMovementSelector, optional): Selector for subsequent movements.
            chain_arguments_generator (ChainArgumentGenerator, optional): Generator for movement arguments.
        """
        super().__init__(acceptance=acceptance, movement_type=movement_type, seed=seed, stopping_criterion=stopping_criterion or BI(), callbacks=callbacks)
        self.search_spaces = search_spaces
        self.movements = [ss.associated_movement for ss in search_spaces]
        self.max_chain_length = max_chain_length
        self.memory = memory or NoMemory()
        self.first_selector = first_selector or SequentialFirst()
        self.next_selector = next_selector or SequentialNext()
        self.chain_arguments_generator = (
            chain_arguments_generator or FullCombinationGenerator(seed)
        )
        self._short_name = f"{self.variant} {[camel_to_snake(search_space_cls.__name__) + ' ' for search_space_cls in self.search_spaces]}"

        
    @property
    def short_name(self, sep='-') -> str:
        return self._short_name



    def _initialize_chain(
        self, individual: BaseIndividual
    ) -> Tuple[list, BaseObjective, Stack]:
        initial_individual = individual.copy()
        best_chain: list[Tuple[Type[Movement], ArgsT]] = []
        best_objective = individual.get_objective()

        stack: Stack = []
        first_mov_cls = self.first_selector.select_first(initial_individual, self.movements)
        first_space_cls = self._find_search_space_for(first_mov_cls)
        first_chain_args_iterator = self.chain_arguments_generator.generate(
            None, None, None, initial_individual, 0, first_space_cls, None
        )
        stack.append(
            (
                0,
                first_mov_cls,
                first_mov_cls(initial_individual),
                initial_individual,
                first_chain_args_iterator,
                None,
                self._generate_fallback_individual(initial_individual, 0),
            )
        )

        return best_chain, best_objective, stack

    def _search(self, individual: BaseIndividual) -> bool:

        best_chain, best_objective, stack = self._initialize_chain(
            individual
        )

        while stack:
            level, mov_cls, mov_obj, current_individual, it, arg, fallback_individual = (
                stack[-1]
            )

            if self._process_fallback(stack):
                continue
            try:
                arg = next(it)
            except StopIteration:
                stack.pop()
                continue

            candidate_obj = self._evaluate_chain_move(
                mov_obj, current_individual, arg, level
            )

            is_final, best_chain, best_objective, improved = self._process_final_level(
                level,
                candidate_obj,
                mov_cls,
                stack,
                current_individual,
                fallback_individual,
                mov_obj,
                arg,
                best_objective,
                best_chain,
                individual
            )
            if not self._should_continue(current_individual, best_objective, improved, self.name):
                break
            if is_final:
                continue
            
            self._deepen_search(
                mov_cls, current_individual, stack, level, mov_obj, it, arg, fallback_individual
            )

        return self._apply_best_chain(
            individual, best_chain
        )

    # rest of methods mostly unchanged from your version, but using selectors
    def _deepen_search(
        self,
        mov_cls: Type[Movement],
        individual: BaseIndividual,
        stack: Stack,
        level: int,
        mov_obj: Movement,
        it: Iterable[ArgsT],
        arg: ArgsT,
        fallback_individual: Optional[BaseIndividual],
    ):
        next_cls = self.next_selector.select_next(mov_cls, self.movements)
        next_space_cls = self._find_search_space_for(next_cls)
        next_chain_args_iterator = self.chain_arguments_generator.generate(mov_obj, mov_cls, arg, individual, level + 1, next_space_cls, fallback_individual)
        stack[-1] = (level, mov_cls, mov_obj, individual, it, arg, fallback_individual)
        next_individual = individual.copy()
        next_fallback = self._generate_fallback_individual(next_individual, level + 1)
        stack.append(
            (
                level + 1,
                next_cls,
                next_cls(next_individual),
                next_individual,
                next_chain_args_iterator,
                None,
                next_fallback,
            )
        )

    def _find_search_space_for(self, movement: Type[Movement]) -> Type[SearchSpace]:
        for ss in self.search_spaces:
            if ss.associated_movement == movement:
                return ss
        raise ValueError(f"No search space found for movement {movement}")

    def _evaluate_chain_move(
        self,
        movement: Movement,
        individual: BaseIndividual,
        arg: ArgsT,
        level: int,
    ) -> BaseObjective:

        if (
            self.movement_type == MovementType.DIRECT
            or (self.movement_type == MovementType.SIMULATE
            and (level + 1 != self.max_chain_length))
        ):
            movement.execute(arg)
            current_objective = individual.get_objective()
            return current_objective

        if self.movement_type == MovementType.DO_UNDO:
            movement.execute(arg)
            candidate_obj = individual.get_objective()
            return candidate_obj

        else:
            candidate_obj = movement.simulate(arg)
            return candidate_obj

    def _apply_best_chain(
        self,
        individual: BaseIndividual,
        best_chain: List[Tuple[Type[Movement], ArgsT]],
    ) -> bool:

        if not best_chain:
            return False
        
        if self._tracker._total_improvements == 0:
            return False

        for mov_cls, arg in best_chain:
            mov_cls(individual).execute(arg)
        chained_args = tuple(arg for _, arg in best_chain)
        self.memory._on_accept(chained_args, individual)  
        return True

    def _generate_fallback_individual(
        self, current_individual: BaseIndividual, level: int
    ) -> Optional[BaseIndividual]:
        if (
            (self.movement_type == MovementType.DIRECT)
            or self.movement_type == MovementType.SIMULATE
            and level + 1 != self.max_chain_length
        ):
            fallback_individual = current_individual.copy()
        else:
            fallback_individual = None
        return fallback_individual

    def _process_fallback(
        self,
        stack: Stack,
    ) -> bool:
        level, mov_cls, mov_obj, level_individual, it, arg, fallback_individual = stack[-1]
        if arg:
            if self.movement_type == MovementType.DO_UNDO:
                mov_obj.undo(arg)
            else:
                level_individual.overwrite_with(fallback_individual.copy())
            stack[-1] = (
                level,
                mov_cls,
                mov_obj,
                level_individual,
                it,
                None,
                fallback_individual,
            )
            return True
        return False

    def _process_final_level(
        self,
        level: int,
        candidate_obj: BaseObjective,
        mov_cls: Type[Movement],
        stack: Stack,
        current_individual: BaseIndividual,
        level_individual: BaseIndividual,
        mov_obj: Movement,
        arg: ArgsT,
        best_objective: BaseObjective,
        best_chain: List[Tuple[Type[Movement], ArgsT]],
        individual: BaseIndividual,
    ) -> Tuple[bool, List[Tuple[Type[Movement], ArgsT]], BaseObjective, bool]:
        improved = False
        if level + 1 == self.max_chain_length:
            if self.movement_type == MovementType.DO_UNDO:
                mov_obj.undo(arg) 
            elif self.movement_type == MovementType.DIRECT:
                current_individual.overwrite_with(level_individual)
            if self.movement_type != MovementType.SIMULATE:
                accepted = self.acceptance.compare_individuals(self._tracker.get_best_individual(), individual)
            else:
                accepted = self.acceptance.compare(best_objective, candidate_obj)
            if accepted:
                chain = [
                    (frame[1], frame[5])
                    for frame in stack
                    if frame[5] is not None
                ] + [(mov_cls, arg)]
                chained_args = tuple(arg for _, arg in best_chain)
                if self.memory.is_tabu(chained_args, candidate_obj):
                    return True, best_chain, best_objective, False 
                best_chain = chain
                best_objective = candidate_obj
                improved = True
            return True, best_chain, best_objective, improved
        return False, best_chain, best_objective, improved

    def _validate_movement_type(self):
        for search_space in self.search_spaces:
            movement = search_space.associated_movement
            movement_type = self.movement_type
            if movement_type == MovementType.SIMULATE:
                if not hasattr(movement, "simulate") or not callable(getattr(movement, "simulate")):
                    raise AttributeError(
                        f"{movement.__name__} must implement a 'simulate' method for MovementType.SIMULATE"
                    )

            elif movement_type == MovementType.DO_UNDO:
                if not hasattr(movement, "_undo") or not callable(getattr(movement, "_undo")):
                    raise AttributeError(
                        f"{movement.__name__} must implement an '_undo' method for MovementType.DO_UNDO"
                    )
from typing import Type, Optional, Tuple
from opt_flow.movement import Movement
from opt_flow.movement import SearchSpace
from opt_flow.movement import MovementType
from opt_flow.structure import BaseIndividual
from opt_flow.acceptance._base import BaseAcceptance
from opt_flow.structure._base import BaseObjective
from opt_flow.localsearch.interfaces import MemoryStrategy
from opt_flow.localsearch.strategies.memory import NoMemory
from opt_flow.stopping._base import BaseStopping
from opt_flow.movement import ArgsT
from opt_flow.localsearch._base import BaseLocalSearch
from opt_flow.callback import Callback
from typing import Type, List
from opt_flow.utils import camel_to_snake
class LocalSearch(BaseLocalSearch):
    """
    Local search operator exploring a single search space using a given movement.

    This operator iterates over a search space, evaluates candidate moves,
    and applies the best move according to the acceptance criterion and memory strategy.

    """
    __slots__ = ("_short_name",)
    def __init__(
        self,
        search_space_cls: Type[SearchSpace],
        movement_type: MovementType,
        acceptance: Optional[BaseAcceptance] = None,
        seed: Optional[int] = None,
        memory: Optional[MemoryStrategy] = None,
        stopping_criterion: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        """
        Initialize a SimpleLocalSearch operator.

        Args:
            search_space_cls (Type[SearchSpace]): Search space class to explore.
            movement_type (MovementType): Type of movement execution (DIRECT, SIMULATE, DO_UNDO).
            acceptance (BaseAcceptance, optional): Acceptance criterion. Defaults to global default.
            seed (int, optional): Random seed for reproducibility.
            memory (MemoryStrategy, optional): Memory strategy for tabu or acceptance restrictions.
            stopping_criterion (BaseStopping, optional): Stopping criterion. Defaults to BI().
            callbacks (List[Callback], optional): Callbacks invoked during search.
        """
        super().__init__(
            acceptance=acceptance,
            movement_type=movement_type,
            seed=seed,
            stopping_criterion=stopping_criterion,
            callbacks=callbacks,
        )
        self.search_space_cls = search_space_cls
        self.memory = memory or NoMemory()
        self._short_name = f"{camel_to_snake(self.search_space_cls.__name__)}"

    @property
    def short_name(self, sep="-") -> str:
        return self._short_name

    def _search(self, individual: BaseIndividual) -> bool:
        search_space = self.search_space_cls(
            individual, seed=self.rng.integers(0, 1000000000)
        )

        initial_individual = individual.copy()
        best_individual = None
        movement = self.search_space_cls.associated_movement(individual)
        best_arg, best_objective = (
            None,
            individual.get_objective(),
        )
        candidate_individual = None
        process_tabu = self._process_tabu
        should_continue = self._should_continue
        evaluate_move = self._evaluate_move
        process_fallback = self._process_fallback
        for arg in search_space:

            accepted, candidate_objective, candidate_individual = evaluate_move(
                arg, individual, movement, best_objective, best_individual
            )
            accepted = process_tabu(arg, candidate_objective, accepted)

            if accepted:
                best_arg, best_objective, best_individual = (
                    arg,
                    candidate_objective,
                    candidate_individual.copy(),
                )
            if not should_continue(
                candidate_individual, candidate_objective, accepted, self._short_name
            ):
                break

            process_fallback(initial_individual, candidate_individual, movement, arg)

        if candidate_individual is not None:
            process_fallback(initial_individual, candidate_individual, movement, arg)

        return self._apply_best_move(individual, movement, best_arg)

    def _process_tabu(
        self, arg: ArgsT, objective: BaseObjective, accepted: bool
    ) -> bool:
        if not accepted:
            return False
        return not self.memory.is_tabu(arg, objective)

    def _process_fallback(
        self,
        initial_individual: BaseIndividual,
        candidate_individual: BaseIndividual,
        movement: Movement,
        arg: ArgsT,
    ):
        if self.movement_type == MovementType.DIRECT:
            candidate_individual.overwrite_with(initial_individual.copy())
        elif self.movement_type == MovementType.DO_UNDO:
            movement.undo(arg)

    def _evaluate_move(
        self,
        arg: ArgsT,
        individual: BaseIndividual,
        movement: Movement,
        best_objective: BaseObjective,
        best_individual: BaseIndividual,
    ) -> Tuple[bool, BaseObjective, BaseIndividual]:

        if self.movement_type == MovementType.DIRECT:
            movement.execute(arg)
            accepted = self.acceptance.compare_individuals(best_individual, individual)
            new_objective = individual.get_objective()
            return accepted, new_objective, individual

        elif self.movement_type == MovementType.DO_UNDO:
            movement.execute(arg)
            candidate_objective = individual.get_objective()
            accepted = self.acceptance.compare_individuals(best_individual, individual)
            return accepted, candidate_objective, individual

        elif self.movement_type == MovementType.SIMULATE:
            candidate_objective = movement.simulate(arg)
            accepted = self.acceptance.compare(best_objective, candidate_objective)
            return accepted, candidate_objective, individual

    def _apply_best_move(
        self,
        individual: BaseIndividual,
        movement: Movement,
        best_arg: Optional[ArgsT],
    ) -> bool:
        if best_arg is None:
            return False

        if self._tracker._total_improvements == 0:
            return False

        movement.execute(best_arg)
        self.memory._on_accept(best_arg, individual)
        return True

    def _validate_movement_type(self):
        movement = self.search_space_cls.associated_movement
        movement_type = self.movement_type
        if movement_type == MovementType.SIMULATE:
            if not hasattr(movement, "simulate") or not callable(
                getattr(movement, "simulate")
            ):
                raise AttributeError(
                    f"{movement.__name__} must implement a 'simulate' method for MovementType.SIMULATE"
                )

        elif movement_type == MovementType.DO_UNDO:
            if not hasattr(movement, "_undo") or not callable(
                getattr(movement, "undo")
            ):
                raise AttributeError(
                    f"{movement.__name__} must implement an 'undo' method for MovementType.DO_UNDO"
                )

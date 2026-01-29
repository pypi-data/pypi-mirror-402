from opt_flow.localsearch.interfaces import ChainArgumentGenerator
from typing import Optional, Type, Iterator, Dict, List, Tuple, Any
from opt_flow.movement import Movement
from opt_flow.movement import SearchSpace
from opt_flow.movement import ArgsT
from opt_flow.localsearch.strategies.link_matrix import LinkMatrix
from opt_flow.structure import BaseIndividual
from opt_flow.movement import MovementType
from opt_flow.movement import Movement
from opt_flow.localsearch.interfaces import ScoreCalculator
from opt_flow.localsearch.interfaces import ScoreNormalizer
from opt_flow.localsearch.strategies.score_normalizer import DefaultNormalizer
from opt_flow.localsearch.strategies.score_filter import NoFilter
from opt_flow.localsearch.interfaces import ScoreFilter


class GenericGenerator(ChainArgumentGenerator):
    
    """
    Flexible chain argument generator supporting scoring, filtering, ranking,
    and movement-link constraints.

    This generator can:
    - Enumerate candidate arguments from a search space
    - Enforce link constraints between successive movements
    - Score candidate arguments using objectives and/or individuals
    - Normalize and rank scores
    - Select top-k arguments per movement
    - Adapt behavior based on movement execution type
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        k: Optional[Dict[Type[Movement], int]] = None,
        score_calculator: Optional[ScoreCalculator] = None,
        score_normalizer: Optional[ScoreNormalizer] = None,
        score_filter: Optional[ScoreFilter] = None,
        link_checker_matrix: Optional[LinkMatrix] = None,
        movement_type_dict: Optional[Dict[Type[Movement], MovementType]] = None,
    ):
        """
        Initialize a generic chain argument generator.

        Args:
            seed (int, optional): Random seed for reproducibility.
            k (Optional[Dict[Type[Movement], int]]): Optional mapping specifying
                how many top-ranked arguments to keep per movement type.
            score_calculator (ScoreCalculator, optional): Calculator used to
                assign scalar scores to candidate moves.
            score_normalizer (ScoreNormalizer): Normalizer applied to raw scores.
            score_filter (ScoreFilter): Filter determining which scored moves
                are eligible.
            link_checker_matrix (LinkMatrix, optional): Matrix defining valid
                transitions between movement types.
            movement_type_dict (Dict[Type[Movement], MovementType], optional):
                Overrides default execution types for specific movements.
        """
        super().__init__(seed=seed)
        self.k = k
        self.score_calculator = score_calculator
        self.score_normalizer = score_normalizer or DefaultNormalizer()
        self.link_checker_matrix = link_checker_matrix or {}
        self.movement_type_dict = movement_type_dict or {}
        self.score_filter = score_filter or NoFilter()

        
 
    def generate(
        self,
        prev_movement: Optional[Movement],
        prev_movement_cls: Optional[Type[Movement]],
        prev_arg: Optional[ArgsT],
        individual: BaseIndividual,
        level: int,
        next_space_cls: Type[SearchSpace],
        last_individual: BaseIndividual,
    ) -> Iterator[ArgsT]:

        next_args, next_movement_cls = self._generate_args(
            next_space_cls, prev_movement_cls, individual, prev_arg, last_individual
        )
        if self.score_calculator:
            scores = self._calculate_scores(next_args, next_movement_cls, individual)
            next_args, _ = self._generate_args(
                next_space_cls, prev_movement_cls, individual, prev_arg, last_individual
            )
            zipped_scores = list(zip(next_args, scores))
            zipped_scores.sort(key=lambda x: x[1])
            if self.k:
                top_k = zipped_scores[: self.k[next_movement_cls]]
                return (arg for arg, _ in top_k)
            else:
                return (arg for arg, _ in zipped_scores)
        return next_args

    def _generate_args(
        self,
        next_space_cls: Type[SearchSpace],
        prev_movement_cls: Optional[Type[SearchSpace]],
        individual: BaseIndividual,
        prev_arg: ArgsT,
        last_individual: BaseIndividual,
    ) -> Tuple[Iterator[ArgsT], Type[Movement]]:
        next_movement_cls = next_space_cls.associated_movement
        link_checker = self.link_checker_matrix.get(
            (prev_movement_cls, next_movement_cls)
        )

        if link_checker is None:
            next_args = iter(next_space_cls(individual,seed=self.rng.integers(0, 10000000)))

        else:
            next_args = (
                arg
                for arg in next_space_cls(individual, seed=self.rng.integers(0, 10000000))
                if link_checker.check(prev_arg, last_individual, arg, individual)
            )
        return next_args, next_movement_cls

    def _calculate_scores(
        self,
        next_args: Iterator[ArgsT],
        next_movement_cls: Type[Movement],
        individual: BaseIndividual,
    ) -> List[Any]:
        next_movement_type = self.movement_type_dict.get(
            next_movement_cls, MovementType.DIRECT
        )
        scores = []
        for arg in next_args:
            if next_movement_type == MovementType.SIMULATE:
                score = self.score_calculator.calculate_score(
                    next_movement_cls(individual).simulate(arg), individual
                )
                if self.score_filter.is_allowed(score, individual):
                    scores.append((arg, score))
            elif next_movement_type == MovementType.DO_UNDO:
                movement = next_movement_cls(individual)
                movement.execute(arg)
                score = self.score_calculator.calculate_score(
                    individual.get_objective(), individual
                )
                if self.score_filter.is_allowed(score, individual):
                    scores.append((arg, score))
                movement.undo(arg)
            elif next_movement_type == MovementType.DIRECT:
                simulated_individual = individual.copy()
                movement = next_movement_cls(simulated_individual)
                movement.execute(arg)
                score = self.score_calculator.calculate_score(
                    simulated_individual.get_objective(), simulated_individual
                )
                if self.score_filter.is_allowed(score, simulated_individual):
                    scores.append((arg, score))
        normalized_scores = self.score_normalizer.normalize([x[1] for x in scores])
        return normalized_scores

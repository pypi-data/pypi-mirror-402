from typing import Optional, Any
from opt_flow.metaheuristic.algorithm_type import AlgorithmType
from opt_flow.metaheuristic.mhconfig import mhconfig
from opt_flow.structure import BaseIndividual
from opt_flow.stats import ImprovementHistory
from opt_flow.stats.improvement_history_view import ImprovementHistoryView
from time import time as time_calc
from opt_flow.acceptance._base.base_acceptance import BaseAcceptance
from opt_flow.core.base_population import BasePopulation
from opt_flow.trajectory._base.base_trajectory import BaseTrajectory
from opt_flow.recombination.base_recombination import BaseRecombination

class Algorithm:
    
    """
    A wrapper for a metaheuristic algorithm that stores its execution metadata, 
    improvement history, and final individual.

    Attributes:
        alg (Any): The underlying algorithm instance.
        name (str): Name of the algorithm.
        alg_type (AlgorithmType): Type of the algorithm.
        id (str): Unique identifier for the algorithm instance.
        execution_time (float): Time at which the algorithm was executed.
        objective (float): Objective value of the final individual.
        improvement_history (ImprovementHistory): History of improvements during execution.
        final_individual (BaseIndividual): The individual returned by the algorithm.
        is_best (bool): Flag indicating whether this individual is currently the best.
    """
    
    def __init__(self, algorithm: Any, name: str, alg_type: Optional[AlgorithmType] = None):
        self.alg = algorithm
        self.name = name
        self.alg_type = alg_type
        self.alg_type = self._infer_algorithm_type(algorithm)
        self.id = f"{name}-{mhconfig.node_id}"
        self.execution_time = None
        self.objective = None
        self.improvement_history = None
        mhconfig.increment_id()
        self._reset()
        
    @staticmethod
    def _infer_algorithm_type(algorithm: Any) -> AlgorithmType:
        """
        Infers the AlgorithmType from the algorithm's base class.
        """

        if isinstance(algorithm, BaseAcceptance):
            return AlgorithmType.acceptance

        if isinstance(algorithm, BaseRecombination):
            return AlgorithmType.recombination

        if isinstance(algorithm, BasePopulation):
            return AlgorithmType.population

        if isinstance(algorithm, BaseTrajectory):
            return AlgorithmType.trajectory

        raise TypeError(
            f"Cannot infer AlgorithmType for algorithm of type "
            f"'{type(algorithm).__name__}'.\n"
            "Expected a subclass of one of:\n"
            "  - BaseAcceptance\n"
            "  - BaseRecombination\n"
            "  - BasePopulation\n"
            "  - BaseTrajectory"
        )
        
    def get_improvement_history(self) -> ImprovementHistory:
        """
        Returns the improvement history of the algorithm execution.

        If the algorithm has no recorded improvements, but a final individual exists,
        the history will include the final individual's objective.

        Returns:
            ImprovementHistory
        """
        history = ImprovementHistory()
        if self.improvement_history:
            history.extend(self.improvement_history)
            return history
        if not history and self.final_individual:
            history.append((self.final_individual.get_objective(), self.name, self.is_best, self.execution_time))
        return history
    
    def get_improvement_view(self) -> ImprovementHistoryView:
        """
        Returns the improvement history view of the algorithm execution.

        If the algorithm has no recorded improvements, but a final individual exists,
        the history will include the final individual's objective.

        Returns:
            ImprovementHistoryView
        """
        return self.get_improvement_history().view()

    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Algorithm):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def set_individual(self, individual: BaseIndividual):
        """
        Stores the final individual of the algorithm, its objective value, execution time, 
        and improvement history if available.

        Args:
            individual (BaseIndividual): The individual produced by the algorithm.
        """
        self.final_individual = individual
        self.execution_time = time_calc()
        self.objective = individual.get_objective()
        if hasattr(self.alg, "get_improvement_history"):
            self.improvement_history = self.alg.get_improvement_history()

        
    def get_individual(self) -> BaseIndividual:
        """
        Returns a copy of the final individual.

        Returns:
            BaseIndividual: Copied individual object.
        """
        return self.final_individual.copy()
        
        
    def _set_best(self):
        self.is_best = True
        
    def _reset(self):
        self.is_best = False
        self.final_individual = None
        self.objective = None
        self.execution_time = None
        self.improvement_history = None
        
    def _clear(self):
        self.final_individual = None
        
        
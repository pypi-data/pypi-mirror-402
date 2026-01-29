from opt_flow.stats.stats_record import StatsRecord
from opt_flow.stats.improvement_history import ImprovementHistory
from opt_flow.structure import BaseIndividual
from typing import Optional, List
import time
from opt_flow.config import config


class StatsTracker:
    __slots__ = (
        "_start_time",
        "_track_iterations_without_improvement",
        "_track_time_without_improvement",
        "_track_total_iterations",
        "_track_total_improvements",
        "_track_best_individual",
        "_track_current_best",
        "_track",
        "_track_iter",
        "_track_indiv",
        "__dict__",
    )

    def __init__(self, dependencies: List[str]=[]):
        self._start_time = time.time()
        self._track_iterations_without_improvement = (
            "iterations_without_improvement" in dependencies
        )
        self._iterations_without_improvement = 0
        self._track_time_without_improvement = (
            "time_without_improvements" in dependencies
        )
        self._time_without_improvement = 0
        self._track_total_iterations = "iteration" in dependencies
        self._total_iterations = 0
        self._track_total_improvements = "total_improvements" in dependencies
        self._total_improvements = 0
        self._track_best_individual = "individual" in dependencies
        self._best_individual: Optional[BaseIndividual] = None
        self._track_current_best = "current_best" in dependencies
        self._track_iter = self._track_iterations_without_improvement or self._track_total_iterations or self._track_time_without_improvement or self._track_total_improvements
        self._track_indiv = self._track_best_individual or self._track_current_best
        self._is_current_best = False
        self._track = config.track or dependencies != []
        self._improvement_history = ImprovementHistory()
        self._acceptance = config.default_acceptance

    def increment_iteration(self):
        self._total_iterations += 1

    def get_improvement_history(self) -> ImprovementHistory:
        return self._improvement_history

    def get_iterations_without_improvement(self) -> int:
        return self._iterations_without_improvement

    def get_total_iterations(self) -> int:
        return self._total_iterations

    def is_current_best(self) -> bool:
        return self._is_current_best

    def _record(self, record: StatsRecord):
        if not self._track:
            return
        if self._track_iter:
            if self._track_total_iterations:
                self._total_iterations += 1
            if not record.accepted:
                if self._track_iterations_without_improvement:
                    self._iterations_without_improvement += 1
                if self._track_time_without_improvement:
                    self._time_without_improvement = record.timestamp - self._start_time
            else:
                if self._track_iterations_without_improvement:
                    self._iterations_without_improvement = 0
                if self._track_time_without_improvement:
                    self._time_without_improvement = 0
                if self._track_total_improvements:
                    self._total_improvements += 1
        if self._track_indiv:
            new_individual = record.individual
            best_individual = self._best_individual
            if not self._acceptance.compare_individuals(best_individual, new_individual):
                if self._track_current_best:
                    self._is_current_best = False
            else:
                if self._track_best_individual:
                    if best_individual is None:
                        self._best_individual = new_individual
                    else:
                        best_individual.overwrite_with(new_individual)
                if self._track_current_best:
                    self._is_current_best = True
        self._improvement_history.append(
            (record.objective, record.event, record.accepted, record.timestamp)
        )

    def get_best_individual(self) -> BaseIndividual:
        return self._best_individual

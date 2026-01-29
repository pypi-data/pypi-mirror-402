from typing import NamedTuple, Any, List
from opt_flow.stats import StatsRecord, StatsTracker


class CallbackArgs(NamedTuple):
    """
    Container for arguments passed to callbacks during optimization.

    Immutable and lightweight. Best if callback arguments shouldn't be modified.
    """
    
    iteration: int
    timestamp: float
    objective: Any
    accepted: bool
    current_best: bool
    individual: Any
    event: str
    start_time: float
    iterations_without_improvement: int
    time_without_improvement: float
    total_improvements: int
    history: List[Any]
    
    @classmethod
    def from_stats(cls, record: StatsRecord, stats: StatsTracker) -> 'CallbackArgs':
        """
        Create a CallbackArgs instance from a StatsRecord and StatsTracker.

        Args:
            record (StatsRecord): Record of the current iteration/event.
            stats (StatsTracker): Tracker containing cumulative statistics.

        Returns:
            CallbackArgs: Initialized instance containing the current algorithm state.
        """
        return cls(
            iteration=stats._total_iterations,
            timestamp=record.timestamp,
            objective=record.objective,
            accepted=record.accepted,
            current_best=stats._is_current_best,
            individual=record.individual,
            event=record.event,
            start_time=stats._start_time,
            iterations_without_improvement=stats._iterations_without_improvement,
            time_without_improvement=stats._time_without_improvement,
            total_improvements=stats._total_improvements,
            history=stats._improvement_history,
        )
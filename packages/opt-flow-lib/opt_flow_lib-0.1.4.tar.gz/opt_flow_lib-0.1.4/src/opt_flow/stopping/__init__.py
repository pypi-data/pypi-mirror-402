"""
This module provides a collection of stopping criteria for metaheuristic algorithms.

Stopping criteria determine when an algorithm should terminate based on
various conditions such as time limits, iteration limits, improvements,
or solution quality. Both simple and composite stopping strategies are supported.

"""

from opt_flow.stopping.and_stopping import AndStopping
from opt_flow.stopping.bi import BI
from opt_flow.stopping.bok import Bok
from opt_flow.stopping.fi import FI
from opt_flow.stopping.iteration_limit_stopping import IterationLimitStopping
from opt_flow.stopping.iterations_without_improvement_stopping import (
    IterationsWithoutImprovementStopping,
)
from opt_flow.stopping.no_stopping import NoStopping
from opt_flow.stopping.or_stopping import OrStopping
from opt_flow.stopping.quality_stopping import QualityStopping
from opt_flow.stopping.time_limit_stopping import TimeLimitStopping
from opt_flow.stopping.time_without_improvement_stopping import (
    TimeWithoutImprovementStopping,
)
from opt_flow.stopping._base import BaseCompositeStopping
from opt_flow.stopping._base import BaseStopping
from opt_flow.stopping.parallel_trajectory_stopping import ParallelTrajectoryStopping
__all__ = [
    "AndStopping",
    "BI",
    "FI",
    "Bok",
    "IterationLimitStopping",
    "NoStopping",
    "OrStopping",
    "QualityStopping",
    "TimeLimitStopping",
    "TimeWithoutImprovementStopping",
    "IterationsWithoutImprovementStopping",
    "BaseCompositeStopping",
    "BaseStopping",
    "ParallelTrajectoryStopping"
]

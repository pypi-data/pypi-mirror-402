from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class DiminishingReturnsIndex(BaseMetric):
    name = "diminishing_returns_index"
    description = "Measures slowdown of improvement over time (0=no slowdown, 1=heavy slowdown) per objective."

    def __init__(self, window: int = 5, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        super().__init__()
        self.window = window
        self.directions = directions

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        directions = self.directions
        accepted = np.asarray(history.accepted_mask())
        results = {}

        for d, direction in enumerate(directions):
            # per-objective improvements
            series = vals[:, d]
            diffs = np.diff(series) * direction.value  # positive = improvement

            # only accepted steps
            diffs = diffs[accepted[:-1]]  # skip last index
            if len(diffs) < self.window * 2:
                results[d] = float(np.nan)
                continue

            early = np.mean(np.abs(diffs[:self.window]))
            late = np.mean(np.abs(diffs[-self.window:]))
            if early == 0:
                results[d] = 0.0
            else:
                results[d] = float(1 - (late / early))

        return results

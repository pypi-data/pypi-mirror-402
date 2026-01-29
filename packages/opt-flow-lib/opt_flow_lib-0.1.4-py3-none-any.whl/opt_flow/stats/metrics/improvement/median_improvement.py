from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class MedianImprovement(BaseMetric):
    name = "median_improvement"
    description = "Median improvement per objective (direction-aware)."
    
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions


    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        directions = self.directions
        accepted = np.asarray(history.accepted_mask())

        diffs = np.diff(vals, axis=0)  # (T-1, D)

        # direction-aware: positive = improvement
        for d, direction in enumerate(directions):
            diffs[:, d] *= direction.value

        results = {}
        for d in range(vals.shape[1]):
            dd = diffs[:, d]
            dd = dd[accepted[:-1]]  # only count accepted moves
            if len(dd) == 0:
                results[d] = float(np.nan)
            else:
                results[d] = float(np.median(dd))
        return results
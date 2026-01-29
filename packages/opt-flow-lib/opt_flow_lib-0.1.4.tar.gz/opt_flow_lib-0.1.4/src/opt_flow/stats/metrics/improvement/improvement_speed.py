from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class ImprovementSpeed(BaseMetric):
    name = "improvement_speed"
    description = "Average direction-aware improvement per second (per objective)."
    
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions


    def compute(self, history):
        vals = np.asarray(history.objectives())     # (T, D)
        times = np.asarray(history.timestamps())    # (T,)
        directions = self.directions
        accepted = np.asarray(history.accepted_mask())

        diffs = np.diff(vals, axis=0)                # (T-1, D)
        dt = np.diff(times)                          # (T-1,)

        # avoid division by zero or negative time
        valid = dt > 0
        diffs = diffs[valid]
        dt = dt[valid]
        accepted = accepted[:-1][valid]

        # direction-aware: positive = improvement
        for d, direction in enumerate(directions):
            diffs[:, d] *= direction.value

        # improvement rate per second
        rates = diffs / dt[:, None]                  # (T-1, D)

        results = {}
        for d in range(vals.shape[1]):
            rd = rates[:, d]
            rd = rd[accepted]                        # only accepted steps
            results[d] = float(np.mean(rd)) if len(rd) > 0 else float("nan")

        return results

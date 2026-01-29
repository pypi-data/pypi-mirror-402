from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class RelativeImprovement(BaseMetric):
    name = "relative_improvement"
    description = "Relative improvement w.r.t initial objective (per dimension, direction-aware)."
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        directions = self.directions

        start = vals[0, :]
        results = {}

        for d, direction in enumerate(directions):
            series = vals[:, d]
            if direction == ObjectiveDirection.MINIMIZE:
                best = np.min(series)
                raw = start[d] - best
            elif direction == ObjectiveDirection.MAXIMIZE:
                best = np.max(series)
                raw = best - start[d]
            else:
                raise ValueError(f"Unknown direction {direction}")

            denom = np.abs(start[d])
            if denom == 0:
                results[d] = float(np.nan)
            else:
                results[d] = float(raw / denom)

        return results

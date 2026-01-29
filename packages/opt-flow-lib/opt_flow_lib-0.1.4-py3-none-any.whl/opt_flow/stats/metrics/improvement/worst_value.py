from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class WorstValue(BaseMetric):
    name = "worst_value"
    description = "Worst value reached per objective, respecting direction."
    
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions


    def compute(self, history):
        vals = np.asarray(history.objectives())     # (T, D)
        directions = self.directions             # (D,)

        best = np.empty(vals.shape[1])

        for d, direction in enumerate(directions):
            if direction == ObjectiveDirection.MINIMIZE:
                best[d] = np.max(vals[:, d])
            elif direction == ObjectiveDirection.MAXIMIZE:
                best[d] = np.min(vals[:, d])
            else:
                raise ValueError(f"Unknown direction {direction}")

        return {
            d: float(best[d])
            for d in range(len(best))
        }

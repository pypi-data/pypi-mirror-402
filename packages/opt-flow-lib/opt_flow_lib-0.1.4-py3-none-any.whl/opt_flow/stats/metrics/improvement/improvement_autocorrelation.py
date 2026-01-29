from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class ImprovementAutocorrelation(BaseMetric):
    name = "improvement_autocorrelation"
    description = "Correlation between consecutive improvements (per objective, direction-aware)."

    def __init__(self, lag: int = 1, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        super().__init__()
        self.lag = lag
        self.directions = directions

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        directions = self.directions
        accepted = np.asarray(history.accepted_mask())

        diffs = np.diff(vals, axis=0)  # (T-1, D)
        # multiply by direction: positive always = improvement
        for d, direction in enumerate(directions):
            diffs[:, d] *= direction.value

        results = {}
        for d in range(vals.shape[1]):
            dd = diffs[:, d]
            # only consider accepted steps
            dd = dd[accepted[:-1]]  # exclude last step
            if len(dd) <= self.lag:
                results[d] = 0.0
            else:
                x = dd[:-self.lag]
                y = dd[self.lag:]
                corr = np.corrcoef(x, y)[0, 1]
                results[d] = float(corr)
        return results
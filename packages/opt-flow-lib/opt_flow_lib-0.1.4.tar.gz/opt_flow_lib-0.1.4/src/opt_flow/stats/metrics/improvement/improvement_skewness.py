from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class ImprovementSkewness(BaseMetric):
    name = "improvement_skewness"
    description = "Skewness of the improvement distribution."

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        diffs = np.diff(vals, axis=0)
        results = {}
        for d in range(vals.shape[1]):
            dd = diffs[:, d]
            m = np.mean(dd)
            s = np.std(dd)
            if s == 0:
                results[d] = 0.0
            else:
                results[d] = float(np.mean(((dd - m) / s) ** 3))
        return results
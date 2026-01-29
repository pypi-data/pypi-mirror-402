from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class ImprovementVolatility(BaseMetric):
    name = "improvement_volatility"
    description = "Volatility of the improvement series."

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        diffs = np.diff(vals, axis=0)
        return {d: float(np.std(diffs[:, d])) for d in range(vals.shape[1])}
from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class CumulativeImprovement(BaseMetric):
    name = "cumulative_improvement"
    description = "Cumulative improvement obtained."

    def compute(self, history):
        vals = history.objectives()
        start = np.array(vals[0])
        end = np.array(vals[-1])
        res = start - end
        return [float(x) for x in res]



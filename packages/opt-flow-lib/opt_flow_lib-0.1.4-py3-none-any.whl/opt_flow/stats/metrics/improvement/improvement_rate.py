from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from opt_flow.stats.metrics.improvement.cumulative_improvement import CumulativeImprovement
from opt_flow.stats.metrics.temporal.total_time import TotalTime
import numpy as np
@register_metric
class ImprovementRate(BaseMetric):
    name = "improvement_rate"
    description = "Rate of improvements per second."

    def compute(self, history):
        imp = np.array(CumulativeImprovement().compute(history))
        time = TotalTime().compute(history)
        if time == 0:
            return np.nan
        res = imp / time
        return [float(x) for x in res]


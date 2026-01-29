from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from opt_flow.stats.metrics.improvement.cumulative_improvement import CumulativeImprovement
from opt_flow.stats.metrics.improvement.total_improvements import TotalImprovements
import numpy as np
@register_metric
class ImprovementEfficiency(BaseMetric):
    name = "improvement_efficiency"
    description = "Total improvement per accepted step."

    def compute(self, history):
        imp = np.array(CumulativeImprovement().compute(history))
        acc = TotalImprovements().compute(history)
        if acc == 0:
            return np.nan
        res = imp / acc
        return [float(x) for x in res]

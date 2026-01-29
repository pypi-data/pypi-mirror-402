from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class FinalValue(BaseMetric):
    name = "final_value"
    description = "Final objective value reached in the algorithm."

    def compute(self, history):
        vals = np.asarray(history.objectives())  
        res = [float(x) for x in vals[-1]]
        return res

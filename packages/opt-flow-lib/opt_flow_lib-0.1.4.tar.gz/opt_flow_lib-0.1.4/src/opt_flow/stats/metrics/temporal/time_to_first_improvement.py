from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np

@register_metric
class TimeToFirstImprovement(BaseMetric):
    name = "time_to_first_improvement"
    description = "Time until first improvement found."
    

    def compute(self, history):
        timestamps = history.timestamps()
        for acc, t in zip(history.accepted_mask(), timestamps[1:]):
            if acc:
                return t - timestamps[0]
        return np.nan

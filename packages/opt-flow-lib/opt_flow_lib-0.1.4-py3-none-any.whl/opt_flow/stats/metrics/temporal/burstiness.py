from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class Burstiness(BaseMetric):
    name = "burstiness"
    description = "Burstiness of accepted events."

    def compute(self, history):
        accepted_times = [t for t, a in zip(history.timestamps(), history.accepted_mask()) if a]
        if len(accepted_times) < 2:
            return np.nan
        intervals = np.diff(accepted_times)
        mu, sigma = np.mean(intervals), np.std(intervals)
        return float((sigma - mu) / (sigma + mu))

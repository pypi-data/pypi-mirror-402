from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np

@register_metric
class AverageIntervalBetweenAccepts(BaseMetric):
    name = "average_interval_between_accepts"
    description = "Average time passed between accepted events."

    def compute(self, history):
        accepted_times = [t for t, acc in zip(history.timestamps(), history.accepted_mask()) if acc]
        if len(accepted_times) < 2:
            return np.nan
        return float(np.mean(np.diff(accepted_times)))


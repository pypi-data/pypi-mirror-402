from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class StagnationPeriods(BaseMetric):
    name = "stagnation_periods"
    description = "Count how many times the optimizer stagnates (no improvement)."
    
    def __init__(self, threshold: float=1e-6):
        super().__init__()
        self.threshold = threshold

    def compute(self, history):
        v = history.objectives()
        diffs = np.diff(v)
        return int(np.sum(np.abs(diffs) < self.threshold))

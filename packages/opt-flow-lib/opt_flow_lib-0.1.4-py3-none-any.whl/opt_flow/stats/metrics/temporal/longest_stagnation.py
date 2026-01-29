from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class LongestStagnation(BaseMetric):
    name = "longest_stagnation"
    description = "Longest streak without improvement."
    
    def __init__(self, threshold: int=1e-6):
        super().__init__()
        self.threshold = threshold

    def compute(self, history):
        v = history.objectives()
        diffs = np.abs(np.diff(v))
        mask = diffs < self.threshold
        longest, current = 0, 0
        for m in mask:
            current = current + 1 if m else 0
            longest = max(longest, current)
        return longest

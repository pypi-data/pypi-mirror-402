from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class EventSuccessOverTime(BaseMetric):        
    name = "event_success_over_time"
    description = "Rolling acceptance rate over time (for convergence phases)."
    
    def __init__(self, bins: int=10):
        self.bins = bins

    def compute(self, history):
        times = np.array(history.timestamps())
        acc = np.array(history.accepted_mask())
        edges = np.linspace(times[0], times[-1], self.bins + 1)
        rates = []
        for i in range(self.bins):
            mask = (times >= edges[i]) & (times < edges[i + 1])
            if np.sum(mask) == 0:
                rates.append(np.nan)
            else:
                rates.append(float(np.mean(acc[mask])))
        return rates

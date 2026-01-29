from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from collections import defaultdict
@register_metric
class EventSuccessTiming(BaseMetric):
    name = "event_success_timing"
    description = "Average time between successful events per type."

    def compute(self, history):
        times_by_event = defaultdict(list)
        for e, acc, t in zip(history.events(), history.accepted_mask(), history.timestamps()):
            if acc:
                times_by_event[e].append(t)
        return {
            e: float(np.mean(np.diff(ts))) if len(ts) > 1 else np.nan
            for e, ts in times_by_event.items()
        }


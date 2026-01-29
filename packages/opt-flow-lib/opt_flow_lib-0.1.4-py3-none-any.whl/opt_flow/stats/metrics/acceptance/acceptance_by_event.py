from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from collections import defaultdict

@register_metric
class AcceptanceByEvent(BaseMetric):
    name = "acceptance_by_event"
    description = "Accepted improvements by event."

    def compute(self, history):
        event_accept = defaultdict(lambda: [0, 0])
        for _, e, acc, _ in history:
            event_accept[e][1] += 1
            if acc:
                event_accept[e][0] += 1
        return {e: a[0] / a[1] for e, a in event_accept.items()}
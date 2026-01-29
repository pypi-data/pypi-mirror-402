from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from collections import Counter
@register_metric
class EventCounts(BaseMetric):
    name = "event_counts"
    description = "Executed iterations by event."

    def compute(self, history):
        return dict(Counter(history.events()))

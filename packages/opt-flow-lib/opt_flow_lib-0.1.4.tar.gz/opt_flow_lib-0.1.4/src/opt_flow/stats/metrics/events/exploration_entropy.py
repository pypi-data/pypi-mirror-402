from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.stats.metrics.events.event_counts import EventCounts
@register_metric
class ExplorationEntropy(BaseMetric):
    name = "exploration_entropy"
    description = "Shannon entropy of event usage (diversity of exploration)."

    def compute(self, history):
        event_counts = EventCounts().compute(history)
        counts = np.array(list(event_counts.values()))
        probs = counts / counts.sum()
        return float(-np.sum(probs * np.log2(probs)))

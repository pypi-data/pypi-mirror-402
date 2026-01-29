from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics.events.event_counts import EventCounts
from opt_flow.stats.metrics.temporal.average_interval_between_accepts import AverageIntervalBetweenAccepts
from opt_flow.stats.metrics_registry import register_metric

@register_metric
class EventEfficiency(BaseMetric):
    name = "event_efficiency"
    description = "Fraction of event occurrences that were accepted."

    def compute(self, history):
        event_counts = EventCounts().compute(history)
        accepted = history.accepted_mask()
        events = history.events()

        accepted_counts = {}

        for e, acc in zip(events, accepted):
            if acc:
                accepted_counts[e] = accepted_counts.get(e, 0) + 1

        return {
            e: accepted_counts.get(e, 0) / event_counts[e]
            for e in event_counts
            if event_counts[e] > 0
        }

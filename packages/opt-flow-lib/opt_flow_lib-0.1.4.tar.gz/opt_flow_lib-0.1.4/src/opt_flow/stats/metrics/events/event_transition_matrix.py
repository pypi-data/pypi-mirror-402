from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from collections import defaultdict
@register_metric
class EventTransitionMatrix(BaseMetric):
    name = "event_transition_matrix"
    description = "Count transitions between event types (for behavioral patterns)."

    def compute(self, history):
        transitions = {}
        events = history.events()
        for e1, e2 in zip(events[:-1], events[1:]):
            if e1 not in transitions:
                transitions[e1] = {}
            if e2 not in transitions[e1]:
                transitions[e1][e2] = 0
            transitions[e1][e2] += 1
        return dict(transitions)

from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from collections import defaultdict
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class MeanImprovementByEvent(BaseMetric):
    name = "mean_improvement_by_event"
    description = "Mean improvement by event (per objective, direction-aware)."
    
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions

    def compute(self, history):
        vals = np.asarray(history.objectives()) 
        events = history.events()
        accepted = np.asarray(history.accepted_mask())
        directions = self.directions

        event_vals = defaultdict(lambda: defaultdict(list))

        for i in range(len(vals)):
            if not accepted[i]:
                continue
            event = events[i]
            for d, direction in enumerate(directions):
                event_vals[event][d].append(vals[i, d] * direction.value)

        results = {}
        for event, obj_map in event_vals.items():
            results[event] = {}
            for d, values in obj_map.items():
                if len(values) == 1:
                    results[event][d] = float(values[0])
                else:
                    diffs = np.diff(values) 
                    results[event][d] = float(np.mean(diffs))
        return results
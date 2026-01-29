from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric

@register_metric
class TotalImprovements(BaseMetric):
    name = "total_improvements"
    description = "Total improvements found."

    def compute(self, history):
        return sum(history.accepted_mask())
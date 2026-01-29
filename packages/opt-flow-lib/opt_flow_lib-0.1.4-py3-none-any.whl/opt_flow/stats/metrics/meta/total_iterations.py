from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric

@register_metric
class TotalIterations(BaseMetric):
    name = "total_iterations"
    description = "Total iterations executed."

    def compute(self, history):
        return len(history)
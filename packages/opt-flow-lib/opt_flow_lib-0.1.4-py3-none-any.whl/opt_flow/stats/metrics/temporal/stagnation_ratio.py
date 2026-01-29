from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from opt_flow.stats.metrics.temporal.stagnation_periods import StagnationPeriods
from opt_flow.stats.metrics.meta.total_iterations import TotalIterations

@register_metric
class StagnationRatio(BaseMetric):
    name = "stagnation_ratio"
    description = "Fraction of time spent stagnating."
    
    def __init__(self, threshold: float=1e-6):
        super().__init__()
        self.threshold = threshold

    def compute(self, history):
        stags = StagnationPeriods(self.threshold).compute(history)
        total_steps = TotalIterations().compute(history)
        return 0 if not total_steps else stags / total_steps
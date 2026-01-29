from logging import INFO, log
from typing import Union

from opt_flow.callback.base.callback import Callback
from opt_flow.callback.base.callback_args import CallbackArgs
from opt_flow.stats.improvement_history_view import ImprovementHistoryView
from opt_flow.stats.base_metric import BaseMetric


class MetricLogger(Callback):
    """
    Callback that logs any metric computed from the improvement history.

    The metric can be provided either as:
    - a metric name registered in ImprovementAnalyzer, or
    - a BaseMetric instance

    Metrics are computed using ImprovementHistoryView.
    """
    __dependencies__ = ["iterations_without_improvement", "time_without_improvements", "iteration", "total_improvements", "individual", "current_best"]

    def __init__(
        self,
        metric: Union[str, BaseMetric],
        *,
        on_improvement: bool = True,
        level: int = INFO,
        prefix: str = "metric",
    ):
        """
        Initialize the MetricLogger callback.

        Args:
            metric (str | BaseMetric):
                Metric name (registered in ImprovementAnalyzer) or
                a metric instance.
            on_improvement (bool):
                If True, log only when a candidate solution is accepted.
                If False, log on every callback invocation.
            level (int):
                Logging level (e.g., logging.INFO, logging.DEBUG).
            prefix (str):
                Prefix added to log messages.
        """
        self.metric = metric
        self.on_improvement = on_improvement
        self.level = level
        self.prefix = prefix

    def __call__(self, arg: CallbackArgs):
        """
        Compute and log the metric based on the callback context.

        Args:
            arg (CallbackArgs): Callback context.
        """
        if self.on_improvement and not arg.accepted:
            return

        history_view = ImprovementHistoryView(arg.history)

        # Compute metric
        if isinstance(self.metric, BaseMetric):
            value = self.metric.compute(arg.history)
            name = self.metric.name
        else:
            value = history_view.compute(self.metric)
            name = self.metric

        # Log metric (supports scalar or dict outputs)
        if isinstance(value, dict):
            for k, v in value.items():
                log(
                    self.level,
                    f"{self.prefix}.{name}.{k} = {v}",
                )
        else:
            log(
                self.level,
                f"{self.prefix}.{name} = {value}",
            )

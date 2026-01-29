from opt_flow.stats.metrics_registry import get_registered_metrics
from typing import Dict, Any, List
from pathlib import Path
import json
from opt_flow.config import config
import numpy as np

def _nan_to_none(obj: Any) -> Any:
    """
    Recursively replace np.nan with None in nested structures.
    """
    if isinstance(obj, dict):
        return {k: _nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return obj.__class__(_nan_to_none(v) for v in obj)
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    else:
        return obj
    
class ImprovementAnalyzer:
    """
    Computes registered metrics for a given improvement history.

    This class retrieves all metrics registered in the metrics registry
    and allows computing them either all at once or individually.
    """

    def __init__(self, history):
        self.history = history
        self.metrics = get_registered_metrics()

    def compute_all(self):
        """
        Compute all registered metrics for the history.

        Returns:
            Dict[str, Any]: A dictionary mapping metric names to their
            computed values. If a metric computation fails, the value
            is a string describing the error.
        """
        results = {}
        for name, metric_cls in self.metrics.items():
            metric = metric_cls()
            try:
                results[name] = metric.compute(self.history)
            except Exception as e:
                results[name] = f"Error: {e}"
        return results

    def compute(self, name: str, extra_args: Dict[str, Any]):
        """
        Compute a single metric by name.

        Args:
            name (str): Name of the registered metric to compute.
            extra_args (Dict[str, Any]): Additional keyword arguments
                passed to the metric class constructor.

        Returns:
            Any: The result of the metric computation.

        Raises:
            ValueError: If the requested metric name is not registered.
        """
        metric_cls = self.metrics.get(name)
        if not metric_cls:
            raise ValueError(f"Unknown metric '{name}'")
        return metric_cls(**extra_args).compute(self.history)
    
    def metric_info(self, metric_name: str) -> Dict[str, Any]:
        """Get all available information for a metric by name.
        
        Args:
            metric_name (str): The name of the metric.
            
        Returns:
            Dict[str, Any]: A dictionary with the description and additional 
            parameters for the metric.
            
        Raises:
            ValueError: If the requested metric name is not registered.
        """
        metric_cls = self.metrics.get(metric_name)
        if not metric_cls:
            raise ValueError(f"Unknown metric '{metric_name}'")
        return metric_cls().info()

    def list_metrics(self) -> List[str]:
        """Get the names of all available metrics to calculate.
        
        Returns:
            List[str]: A list of all available metric names."""
        return list(self.metrics.keys())
    
    
    def save_metrics(
        self,
        metric_names: tuple[str, ...] | None = None,
        extra_args: dict[str, dict[str, Any]] | None = None,
        folder: Path | None = None
    ):
        """
        Save selected or all computed metrics to a JSON file, with optional
        extra arguments for individual metrics. Extra args are shown in
        the metric name in the saved results.

        Parameters
        ----------
        metric_names : tuple[str, ...] | None, optional
            A tuple of metric names to save. If None, all metrics are
            computed and saved.
        extra_args : dict[str, dict[str, Any]] | None, optional
            A dictionary mapping metric names to extra keyword arguments
            to pass to their constructor.
            Example: {'accuracy': {'normalize': True}, 'f1': {'average': 'macro'}}
        folder : Path | None, optional
            The path to save the metrics. If None, a default
            name including a timestamp is generated.

        Notes
        -----
        The file is saved under a 'runs' directory in the current
        working directory. If the directory does not exist, it is
        created automatically. The saved JSON is pretty-printed
        and sorted for readability.
        """
        results = self.get_metrics_payload(metric_names, extra_args)
        # Determine run folder
        if folder is None:
            folder = Path("runs") / f"{config.start_time}_{config.name}"
        folder.mkdir(parents=True, exist_ok=True)

        
        path = folder / "metrics.json"
        path.write_text(json.dumps(results, indent=4, sort_keys=True), encoding="utf-8")
        
        
    def get_metrics_payload(
        self,
        metric_names: tuple[str, ...] | None = None,
        extra_args: dict[str, dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Gets the payload for selected or all computed metrics to a JSON file, with
        optional extra arguments for individual metrics. Extra args are shown in
        the metric name in the saved results.

        Parameters
        ----------
        metric_names : tuple[str, ...] | None, optional
            A tuple of metric names to save. If None, all metrics are
            computed and saved.
        extra_args : dict[str, dict[str, Any]] | None, optional
            A dictionary mapping metric names to extra keyword arguments
            to pass to their constructor.
            Example: {'accuracy': {'normalize': True}, 'f1': {'average': 'macro'}}

        """
        extra_args = extra_args or {}

        # Determine which metrics to compute
        if metric_names is None:
            metric_names = tuple(self.list_metrics())

        results = {}
        for name in metric_names:
            try:
                args = extra_args.get(name, {})
                # Include args in metric name
                if args:
                    args_str = ",".join(f"{k}={v}" for k, v in sorted(args.items()))
                    result_name = f"{name}({args_str})"
                else:
                    result_name = name

                results[result_name] = self.compute(name, extra_args=args)
            except Exception as e:
                results[result_name] = f"Error: {e}"

        results = dict(sorted(results.items()))
        results = _nan_to_none(results)
        return results
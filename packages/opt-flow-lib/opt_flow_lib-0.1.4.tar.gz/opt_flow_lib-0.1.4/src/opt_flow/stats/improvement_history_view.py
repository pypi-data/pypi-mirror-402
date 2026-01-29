from opt_flow.stats.improvement_analizer import ImprovementAnalyzer
from opt_flow.stats.improvement_visualizer import ImprovementVisualizer
from typing import Dict, List, Any
from pathlib import Path

class ImprovementHistoryView:

    """
    Provides an interface for analyzing and visualizing an improvement history.

    Combines an ImprovementAnalyzer for computing metrics and an
    ImprovementVisualizer for plotting, offering a unified view
    of the improvement process.
    """
    def __init__(self, history):
        self._history = history
        self._analyzer = ImprovementAnalyzer(history)
        self._visualizer = ImprovementVisualizer(history)

    def metrics(self):
        """
        List all available metric names.

        Returns:
            List[str]: Names of all registered metrics.
        """
        return list(self._analyzer.metrics.keys())

    def compute(self, name: str, **extra_args):
        """
        Compute a specific metric by name.

        Args:
            name (str): Name of the metric to compute.
            **extra_args: Additional keyword arguments for the metric.

        Returns:
            Any: Computed metric value.
        """
        return self._analyzer.compute(name, extra_args)

    def compute_all(self):
        """
        Compute all registered metrics for the history.

        Returns:
            Dict[str, Any]: Dictionary mapping metric names to their
            computed values.
        """
        return self._analyzer.compute_all()

    def plots(self):
        """
        List all available plot types.

        Returns:
            List[str]: Names of all registered plots.
        """
        return list(self._visualizer.plots.keys())

    def plot(self, name: str, **extra_args):
        """
        Render a specific plot for the improvement history.

        Args:
            name (str): Name of the plot to render.
            **extra_args: Additional keyword arguments for the plot.

        Returns:
            Any: Result of the plot rendering.
        """
        return self._visualizer.plot(name, extra_args)
    
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
        return self._analyzer.metric_info(metric_name)

    def list_metrics(self) -> List[str]:
        """Get the names of all available metrics to calculate.
        
        Returns:
            List[str]: A list of all available metric names."""
        return self._analyzer.list_metrics()
    
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
        return self._analyzer.save_metrics(metric_names, extra_args, folder)
    
    def get_metrics_payload(
        self,
        metric_names: tuple[str, ...] | None = None,
        extra_args: dict[str, dict[str, Any]] | None = None,
    ):
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
        return self._analyzer.get_metrics_payload(metric_names, extra_args)
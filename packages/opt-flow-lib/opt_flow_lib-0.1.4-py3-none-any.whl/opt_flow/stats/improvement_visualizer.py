from opt_flow.stats.plots_registry import get_registered_plots
from typing import Dict, Any
class ImprovementVisualizer:
    
    """
    Visualizes the history of solution improvements in a metaheuristic.

    This class uses a registry of pre-defined plot classes to render
    visualizations of improvement histories.
    """
    
    def __init__(self, history):
        self.history = history
        self.plots = get_registered_plots()
        
    def plot(self, name: str, extra_args: Dict[str, Any]):
        """
        Render a specific plot for the improvement history.

        Args:
            name (str): Name of the registered plot type to use.
            extra_args (Dict[str, Any]): Additional keyword arguments
                passed to the plot class constructor.

        Returns:
            Any: The result of the plot method of the selected plot class.

        Raises:
            ValueError: If the requested plot name is not registered.
        """
        plot_cls = self.plots.get(name)
        if not plot_cls:
            raise ValueError(f"Unknown plot '{name}'")
        return plot_cls(**extra_args).plot(self.history)

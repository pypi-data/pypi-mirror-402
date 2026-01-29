from opt_flow.stats.base_plot import BasePlot
import plotly.graph_objects as go
from opt_flow.config import config
from opt_flow.stats.plots_registry import register_plot

@register_plot
class ScalarObjectivePlot(BasePlot):
    
    name = "scalar_objective_plot"
    description = "Plot of the evolution of the objective throughout the optimization."
    
    def __init__(self, only_accepted: bool=True):
        self.only_accepted = only_accepted
        
    def plot(self, history):
        if not history:
            return
        filtered = history.get(only_accepted=self.only_accepted)
        if not filtered:
            raise ValueError("No accepted records to plot." if self.only_accepted else
                            "No records to plot.")

        objectives, events, _, timestamps = zip(*filtered)
        
        from opt_flow.structure import ScalarObjective
        values_list = []
        for v in objectives:
            if isinstance(v, ScalarObjective):
                values_list.append((v.value,)[0])
            else:
                values_list.append(tuple(vx.value for vx in v)[0])

        from opt_flow.structure import ScalarObjective
        names = []
        for v in objectives:
            if isinstance(v, ScalarObjective):
                names.append((v.name,))
            else:
                names.append(tuple(vx.name for vx in v))
    
        # objectives: [((v1, v2, ...), (n1, n2, ...)), ...]
        names = names[0]

        # Normalize timestamps
        start_time = config.start_time
        timestamps = [t - start_time for t in timestamps]

        # Build color map for events
        unique_events = sorted(set(events))
        color_map = {
            e: f"hsl({i * 360 / len(unique_events)}, 70%, 50%)"
            for i, e in enumerate(unique_events)
        }

        fig = self._plot_scalar_objective(values_list, names[0], events, timestamps, color_map)

        fig.update_layout(
            title=self.description,
            xaxis_title="Time (seconds)",
            yaxis_title="Objective Value",
            template="plotly_white",
            showlegend=True,
        )

        fig.show()

    def _plot_scalar_objective(self, values, name, events, timestamps, color_map) -> go.Figure:
        """
        Internal method to build the scalar objective plot.
        """
        y_values = values
        fig = go.Figure()

        for event in sorted(set(events)):
            mask = [e == event for e in events]

            fig.add_trace(
                go.Scatter(
                    x=[t for t, m in zip(timestamps, mask) if m],
                    y=[y for y, m in zip(y_values, mask) if m],
                    mode="markers",
                    name=event,
                    marker={
                        "color": color_map[event],
                        "size": 7,
                    },
                )
            )
        fig.update_yaxes(title_text=name)

        return fig
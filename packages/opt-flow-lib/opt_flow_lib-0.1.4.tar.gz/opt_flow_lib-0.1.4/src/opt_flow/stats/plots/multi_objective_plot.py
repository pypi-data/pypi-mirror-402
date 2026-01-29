from opt_flow.stats.base_plot import BasePlot
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from opt_flow.config import config
from opt_flow.stats.plots_registry import register_plot


@register_plot
class MultiObjectivePlot(BasePlot):

    name = "multi_objective_plot"
    description = "Plot of the evolution of each objective in a multi-objective optimization."

    def __init__(self, only_accepted: bool = True):
        self.only_accepted = only_accepted

    def plot(self, history):
        if not history:
            return

        filtered = history.get(only_accepted=self.only_accepted)
        if not filtered:
            raise ValueError(
                "No accepted records to plot."
                if self.only_accepted
                else "No records to plot."
            )

        # Unpack history tuples
        objectives, events, _, timestamps = zip(*filtered)
        
        from opt_flow.structure import ScalarObjective
        values_list = []
        for v in objectives:
            if isinstance(v, ScalarObjective):
                values_list.append((v.value,))
            else:
                values_list.append(tuple(vx.value for vx in v))

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

        fig = self._plot_multi_objective(
            values_list,
            names,
            events,
            timestamps,
            color_map,
        )

        fig.update_layout(
            title=self.description,
            xaxis_title="Time (seconds)",
            template="plotly_white",
            showlegend=True,
        )

        fig.show()

    def _plot_multi_objective(
        self,
        values_list,
        names,
        events,
        timestamps,
        color_map,
    ) -> go.Figure:
        """
        Build subplots for each objective.
        """

        n_objectives = len(names)

        fig = make_subplots(
            rows=n_objectives,
            cols=1,
            shared_xaxes=True,
            subplot_titles=names,
        )

        for i, name in enumerate(names):
            # Extract i-th objective values
            y_values = [vals[i] for vals in values_list]

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
                        legendgroup=event,
                        showlegend=(i == 0),  # show legend only once
                    ),
                    row=i + 1,
                    col=1,
                )

            fig.update_yaxes(title_text=name, row=i + 1, col=1)

        return fig

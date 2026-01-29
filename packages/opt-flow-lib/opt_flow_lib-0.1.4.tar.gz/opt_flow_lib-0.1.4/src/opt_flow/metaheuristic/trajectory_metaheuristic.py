from opt_flow.trajectory._base import BaseTrajectory
from opt_flow.metaheuristic.metaheuristic import Metaheuristic
class TrajectoryMetaheuristic(BaseTrajectory, Metaheuristic):
    """
    Base class for trajectory-based metaheuristics that iteratively explore
    individuals by following a trajectory, rather than creating individuals
    from scratch or operating on a population.

    This class inherits from BaseTrajectory (for trajectory-based behavior) 
    and Metaheuristic (for general metaheuristic functionality).

    Note:
        Trajectory metaheuristics do not support individual creation via
        the `create` method.
    """

    def create(self, *args, **kwargs):
        raise RuntimeError("Not possible to call a trajectory metaheuristic for individual creation.")
    
    def get_improvement_history(self):
        return Metaheuristic.get_improvement_history(self)
    
    def get_improvement_history_view(self):
        return super().get_improvement_history_view()
    
    def _on_start(self):
        Metaheuristic._on_start(self)
    
    @staticmethod
    def pipeline(*algs) -> "TrajectoryMetaheuristic":
        mh = TrajectoryMetaheuristic()
        last_alg = None
        for alg in algs:
            mh.add_algorithm(alg)
            if last_alg is not None:
                mh.connect(last_alg, alg)
            last_alg = alg
        return mh

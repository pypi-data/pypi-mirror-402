from opt_flow.metaheuristic.factories._base import TrajectoryFactory
from opt_flow.trajectory import BaseTrajectory

class SimpleTrajectoryFactory(TrajectoryFactory):
    
    """
    Factory for a single trajectory algorithm.

    This factory always returns the same trajectory instance, making it
    suitable for static metaheuristic configurations where no adaptation
    or sequencing is required.
    """
    
    
    def __init__(self, trajectory: BaseTrajectory):
        self.trajectory = trajectory
        
    def create(self) -> BaseTrajectory:
        """
        Returns the configured trajectory algorithm.

        Returns:
            BaseTrajectory: The stored trajectory algorithm instance.
        """
        return self.trajectory
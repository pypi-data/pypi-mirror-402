from opt_flow.trajectory import BaseTrajectory
from opt_flow.metaheuristic.factories._base.base_factory import BaseFactory
from abc import abstractmethod

class TrajectoryFactory(BaseFactory):
    """
    Abstract factory class for creating BaseTrajectory algorithm instances.

    This factory standardizes the creation of trajectory-based 
    algorithms that iteratively refine individuals in an optimization problem.
    """
    @abstractmethod
    def create(self, **kwargs) -> BaseTrajectory:
        """
        Creates and returns a new BaseImprovement algorithm instance.

        Args:
            **kwargs: Arbitrary keyword arguments used to configure the algorithm instance.

        Returns:
            BaseTrajectory: A newly created trajectory algorithm instance.
        """
        pass

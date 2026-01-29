from enum import Enum

class ObjectiveDirection(Enum):
    """
    Enum to specify the optimization direction of an objective.

    Attributes
    ----------
    MINIMIZE : int
        Indicates that the objective should be minimized.
    MAXIMIZE : int
        Indicates that the objective should be maximized.
    """
    
    MINIMIZE = 1
    MAXIMIZE = -1
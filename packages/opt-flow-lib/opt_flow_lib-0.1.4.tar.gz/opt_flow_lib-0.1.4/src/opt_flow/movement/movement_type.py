from enum import Enum

class MovementType(Enum):
    """
    Movement Types for Local Search

    This module defines the MovementType enumeration, which specifies the type of movement
    execution strategy in a local search algorithm:

    - DIRECT: Apply the movement directly to the individual.
    - SIMULATE: Evaluate the movement without modifying the individual.
    - DO_UNDO: Apply the movement and then undo it after evaluation.

    These movement types control how candidate individuals are generated and assessed
    during local search procedures.
    """
    DIRECT = 1
    SIMULATE = 2
    DO_UNDO = 3
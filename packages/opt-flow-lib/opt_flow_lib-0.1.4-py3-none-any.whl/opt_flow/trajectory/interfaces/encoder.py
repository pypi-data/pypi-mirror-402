from abc import ABC, abstractmethod
from opt_flow.structure import BaseIndividual
from typing import Dict, Any

class Encoder(ABC):
    
    """
    Abstract base class defining the interface for individual encoders.

    An encoder is responsible for converting a `BaseIndividual` object into
    a serialized or dictionary representation that can be stored, transmitted,
    or used in parallel processing.

    Methods
    -------
    encode(individual)
        Converts a `BaseIndividual` object into a dictionary representation.
    """
    
    @abstractmethod
    def encode(self, individual: BaseIndividual) -> Dict[str, Any]:
        """
        Encode a `BaseIndividual` instance into a dictionary.

        Parameters
        ----------
        individual : BaseIndividual
            The individual object to encode.

        Returns
        -------
        Dict[str, Any]
            A dictionary representing the individual's data, suitable for
            serialization or communication between processes.
        """
        pass
from abc import ABC, abstractmethod
from opt_flow.structure import BaseIndividual
from opt_flow.structure import Data
from typing import Dict, Any

class Decoder(ABC):
    
    """
    Abstract base class defining the interface for individual decoders.

    A decoder is responsible for transforming a serialized or dictionary 
    representation of a individual into a proper `BaseIndividual` object 
    that can be used by algorithms.

    Methods
    -------
    decode(problem, individual_dict)
        Converts a serialized individual representation into a `BaseIndividual`.
    """
    
    @abstractmethod
    def decode(self, data: Data, individual_dict: Dict[str, Any]) -> BaseIndividual:
        """
        Decode a serialized individual into a `BaseIndividual` instance.

        Parameters
        ----------
        data : Data
            The data instance that the individual belongs to.
        individual_dict : Dict[str, Any]
            A dictionary representing the individual.

        Returns
        -------
        BaseIndividual
            The reconstructed individual object.
        """        
        pass